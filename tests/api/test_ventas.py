"""Pruebas de los endpoints HTTP de RF5 (/ventas) y RF3.1 (/reportes).

Requieren un .env con credenciales reales de MySQL -- se saltan solas si
no hay ninguna configurada. El fixture `crear_productos` (conftest.py)
borra al final los productos de prueba y las ventas que los usaron.
"""

import os

import pytest

from gedenaz.app import create_app

pytestmark = pytest.mark.skipif(
    not os.getenv("DB_PASSWORD"),
    reason="Requiere un .env con credenciales reales de MySQL",
)


@pytest.fixture
def client():
    return create_app().test_client()


def _stock(client, producto: dict) -> int:
    return client.get(f"/productos/{producto['id']}").get_json()["stock"]


def test_post_ventas_registra_descuenta_stock_y_devuelve_201(client, crear_productos):
    a = crear_productos("API venta A pytest", precio=1000, stock=10)
    b = crear_productos("API venta B pytest", precio=500, stock=5)

    respuesta = client.post(
        "/ventas",
        json={"items": [{"producto_id": a["id"], "cantidad": 2}, {"producto_id": b["id"], "cantidad": 1}]},
    )

    assert respuesta.status_code == 201
    venta = respuesta.get_json()
    assert venta["total"] == 2500.0
    assert len(venta["items"]) == 2
    assert venta["items"][0]["subtotal"] == 2000.0
    assert _stock(client, a) == 8
    assert _stock(client, b) == 4


def test_post_ventas_datos_invalidos_devuelve_400_nombrando_la_linea(client, crear_productos):
    a = crear_productos("API validacion pytest")

    respuesta = client.post(
        "/ventas", json={"items": [{"producto_id": a["id"], "cantidad": 0}]}
    )

    assert respuesta.status_code == 400
    error = respuesta.get_json()["error"]
    assert error["mensaje"]
    assert "items[0].cantidad" in error["campos"]
    assert _stock(client, a) == 10  # no se descuento nada


def test_post_ventas_sin_items_devuelve_400(client):
    respuesta = client.post("/ventas", json={})
    assert respuesta.status_code == 400
    assert "items" in respuesta.get_json()["error"]["campos"]


def test_post_ventas_producto_inexistente_devuelve_400(client):
    respuesta = client.post(
        "/ventas", json={"items": [{"producto_id": 999999999, "cantidad": 1}]}
    )
    assert respuesta.status_code == 400
    assert "items[0].producto_id" in respuesta.get_json()["error"]["campos"]


def test_post_ventas_stock_insuficiente_devuelve_409(client, crear_productos):
    a = crear_productos("API sin stock pytest", stock=2)

    respuesta = client.post("/ventas", json={"items": [{"producto_id": a["id"], "cantidad": 5}]})

    assert respuesta.status_code == 409
    error = respuesta.get_json()["error"]
    assert "API sin stock pytest" in error["mensaje"]
    assert "disponible 2" in error["campos"]["items[0].cantidad"]
    assert _stock(client, a) == 2


def test_get_venta_detalle_200_y_404(client, crear_productos):
    a = crear_productos("API detalle venta pytest")
    creada = client.post("/ventas", json={"items": [{"producto_id": a["id"], "cantidad": 1}]}).get_json()

    ok = client.get(f"/ventas/{creada['id']}")
    assert ok.status_code == 200
    assert ok.get_json() == creada

    no_existe = client.get("/ventas/999999999")
    assert no_existe.status_code == 404
    assert no_existe.get_json()["error"]["campos"] is None


def test_get_ventas_lista_y_filtra_por_fecha(client, crear_productos):
    a = crear_productos("API listar ventas pytest")
    creada = client.post("/ventas", json={"items": [{"producto_id": a["id"], "cantidad": 1}]}).get_json()

    todas = client.get("/ventas?desde=2000-01-01&hasta=2100-01-01")
    assert todas.status_code == 200
    assert creada["id"] in [v["id"] for v in todas.get_json()]

    en_2000 = client.get("/ventas?desde=2000-01-01&hasta=2000-01-02")
    assert creada["id"] not in [v["id"] for v in en_2000.get_json()]


def test_get_ventas_con_fecha_invalida_devuelve_400(client):
    respuesta = client.get("/ventas?desde=20-09-2026")
    assert respuesta.status_code == 400
    assert "desde" in respuesta.get_json()["error"]["campos"]


def test_ventas_no_se_pueden_editar_ni_eliminar(client, crear_productos):
    a = crear_productos("API inmutable pytest")
    creada = client.post("/ventas", json={"items": [{"producto_id": a["id"], "cantidad": 1}]}).get_json()

    for metodo in (client.put, client.patch, client.delete):
        assert metodo(f"/ventas/{creada['id']}").status_code == 405


def test_reporte_producto_mas_vendido_de_punta_a_punta(client, crear_productos):
    popular = crear_productos("Reporte popular pytest", precio=100, stock=50)
    otro = crear_productos("Reporte otro pytest", precio=100, stock=50)
    client.post("/ventas", json={"items": [{"producto_id": popular["id"], "cantidad": 7}]})
    client.post("/ventas", json={"items": [{"producto_id": otro["id"], "cantidad": 2}]})

    respuesta = client.get("/reportes/productos-mas-vendidos?limite=100")

    assert respuesta.status_code == 200
    ranking = [f for f in respuesta.get_json() if f["producto_id"] in {popular["id"], otro["id"]}]
    assert [f["producto_id"] for f in ranking] == [popular["id"], otro["id"]]
    assert ranking[0]["unidades_vendidas"] == 7
    assert ranking[0]["ingresos"] == 700.0
    assert set(ranking[0]) == {
        "producto_id", "nombre", "categoria", "activo", "unidades_vendidas", "ingresos",
    }


def test_reporte_con_parametros_invalidos_devuelve_400(client):
    respuesta = client.get("/reportes/productos-mas-vendidos?orden=ganancia&limite=0")
    assert respuesta.status_code == 400
    campos = respuesta.get_json()["error"]["campos"]
    assert set(campos) == {"orden", "limite"}


def test_reporte_sin_ventas_en_el_rango_devuelve_lista_vacia(client):
    respuesta = client.get("/reportes/productos-mas-vendidos?desde=2000-01-01&hasta=2000-01-02")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == []
