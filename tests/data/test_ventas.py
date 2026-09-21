"""Pruebas de acceso a datos de RF5 (ventas) y RF3.1 (ranking).

Requieren un .env con credenciales reales de MySQL -- se saltan solas si
no hay ninguna configurada. El fixture `crear_productos` (conftest.py)
borra al final los productos de prueba y las ventas que los usaron.
"""

import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from gedenaz.config import get_db_config
from gedenaz.data.db import connection_scope
from gedenaz.data.productos import actualizar_producto_parcial, eliminar_producto, obtener_producto
from gedenaz.data.reportes import productos_mas_vendidos
from gedenaz.data.ventas import (
    ProductoNoDisponibleError,
    StockInsuficienteError,
    listar_ventas,
    obtener_venta,
    registrar_venta,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("DB_PASSWORD"),
    reason="Requiere un .env con credenciales reales de MySQL",
)

SIN_LIMITE_DE_FECHAS = (datetime(2000, 1, 1), datetime(2100, 1, 1))


def _stock(producto: dict) -> int:
    return obtener_producto(producto["id"])["stock"]


def _lineas_guardadas(*productos: dict) -> int:
    ids = [p["id"] for p in productos]
    marcas = ", ".join(["%s"] * len(ids))
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM detalle_venta WHERE producto_id IN ({marcas})", ids)
        cantidad = cursor.fetchone()[0]
        cursor.close()
    return cantidad


def _solo_mios(filas: list[dict], *productos: dict) -> list[dict]:
    """El ranking real puede tener otros productos (la base es compartida):
    los tests miran solo el orden relativo de los suyos."""
    ids = {p["id"] for p in productos}
    return [f for f in filas if f["producto_id"] in ids]


# --- registrar_venta ---


def test_registrar_venta_descuenta_stock_y_guarda_foto_del_precio(crear_productos):
    a = crear_productos("Venta A pytest", precio=1000, stock=10)
    b = crear_productos("Venta B pytest", precio=500, stock=5)

    venta = registrar_venta([(a["id"], 3), (b["id"], 1)])

    assert venta["id"] > 0
    assert venta["total"] == 3500.0
    assert [(i["producto_id"], i["cantidad"]) for i in venta["items"]] == [(a["id"], 3), (b["id"], 1)]
    assert venta["items"][0]["precio_unitario"] == 1000.0
    assert venta["items"][0]["subtotal"] == 3000.0
    assert venta["items"][0]["nombre"] == "Venta A pytest"
    assert _stock(a) == 7
    assert _stock(b) == 4

    # Foto, no referencia: cambiar el precio despues no altera la venta.
    actualizar_producto_parcial(a["id"], {"precio": 2000})
    assert obtener_venta(venta["id"])["items"][0]["precio_unitario"] == 1000.0
    assert obtener_venta(venta["id"])["total"] == 3500.0


def test_se_puede_vender_exactamente_todo_el_stock(crear_productos):
    a = crear_productos("Todo el stock pytest", stock=3)
    registrar_venta([(a["id"], 3)])
    assert _stock(a) == 0


def test_stock_insuficiente_no_guarda_nada(crear_productos):
    a = crear_productos("Poco stock A pytest", stock=2)
    b = crear_productos("Poco stock B pytest", stock=5)

    with pytest.raises(StockInsuficienteError) as exc:
        registrar_venta([(b["id"], 1), (a["id"], 3)])

    assert exc.value.indice == 1
    assert exc.value.disponible == 2
    assert exc.value.solicitado == 3
    # Todo o nada: ni siquiera la linea valida (b) se descuenta ni se guarda.
    assert _stock(a) == 2
    assert _stock(b) == 5
    assert _lineas_guardadas(a, b) == 0


def test_producto_inexistente_o_dado_de_baja_no_guarda_nada(crear_productos):
    a = crear_productos("Disponible pytest", stock=10)

    with pytest.raises(ProductoNoDisponibleError) as exc:
        registrar_venta([(a["id"], 1), (999999999, 1)])
    assert exc.value.indice == 1
    assert _stock(a) == 10
    assert _lineas_guardadas(a) == 0

    eliminar_producto(a["id"])
    with pytest.raises(ProductoNoDisponibleError) as exc:
        registrar_venta([(a["id"], 1)])
    assert exc.value.indice == 0


def test_dos_ventas_simultaneas_no_venden_mas_stock_del_que_hay(crear_productos):
    """Con una sola unidad y dos ventas al mismo tiempo, exactamente una
    debe ganar y la otra recibir 'sin stock' (no un error de la base ni
    stock negativo): es lo que garantiza el SELECT ... FOR UPDATE."""
    a = crear_productos("Ultima unidad pytest", stock=1)
    barrera = threading.Barrier(2)
    resultados: list[str] = []

    def vender():
        barrera.wait()
        try:
            registrar_venta([(a["id"], 1)])
            resultados.append("ok")
        except StockInsuficienteError:
            resultados.append("sin_stock")
        except Exception as exc:  # noqa: BLE001 -- cualquier otra cosa es un fallo del test
            resultados.append(f"error: {type(exc).__name__}")

    hilos = [threading.Thread(target=vender) for _ in range(2)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert sorted(resultados) == ["ok", "sin_stock"]
    assert _stock(a) == 0


def test_fecha_venta_se_guarda_en_hora_de_chile(crear_productos):
    a = crear_productos("Hora Chile pytest")
    venta = registrar_venta([(a["id"], 1)])

    fecha = datetime.fromisoformat(venta["fecha_venta"])
    ahora = datetime.now(ZoneInfo(get_db_config().time_zone)).replace(tzinfo=None)
    assert abs((ahora - fecha).total_seconds()) < 300


# --- obtener_venta / listar_ventas ---


def test_obtener_y_listar_ventas(crear_productos):
    a = crear_productos("Historial pytest", stock=10)
    v1 = registrar_venta([(a["id"], 1)])
    v2 = registrar_venta([(a["id"], 2)])

    assert obtener_venta(v1["id"]) == v1
    assert obtener_venta(-1) is None

    ids = [v["id"] for v in listar_ventas()]
    assert ids.index(v2["id"]) < ids.index(v1["id"])  # la mas reciente primero

    en_2000 = [v["id"] for v in listar_ventas(datetime(2000, 1, 1), datetime(2000, 1, 2))]
    assert v1["id"] not in en_2000

    hasta_2100 = [v["id"] for v in listar_ventas(*SIN_LIMITE_DE_FECHAS)]
    assert {v1["id"], v2["id"]} <= set(hasta_2100)


# --- productos_mas_vendidos (RF3.1) ---


def test_ranking_por_unidades_y_por_ingresos(crear_productos):
    barato = crear_productos("Zeta barato pytest", precio=100, stock=50)
    caro = crear_productos("Alfa caro pytest", precio=1000, stock=50)
    registrar_venta([(barato["id"], 3), (caro["id"], 1)])
    registrar_venta([(barato["id"], 2)])
    # barato: 5 unidades / $500 -- caro: 1 unidad / $1000

    por_unidades = _solo_mios(productos_mas_vendidos(None, None, 100, "unidades"), barato, caro)
    assert [f["producto_id"] for f in por_unidades] == [barato["id"], caro["id"]]
    assert por_unidades[0]["unidades_vendidas"] == 5
    assert por_unidades[0]["ingresos"] == 500.0
    assert por_unidades[0]["activo"] is True

    por_ingresos = _solo_mios(productos_mas_vendidos(None, None, 100, "ingresos"), barato, caro)
    assert [f["producto_id"] for f in por_ingresos] == [caro["id"], barato["id"]]


def test_empate_de_unidades_desempata_por_nombre(crear_productos):
    zzz = crear_productos("Zzz empate pytest")
    aaa = crear_productos("Aaa empate pytest")
    registrar_venta([(zzz["id"], 2), (aaa["id"], 2)])

    filas = _solo_mios(productos_mas_vendidos(None, None, 100, "unidades"), zzz, aaa)
    assert [f["nombre"] for f in filas] == ["Aaa empate pytest", "Zzz empate pytest"]


def test_ranking_incluye_productos_dados_de_baja(crear_productos):
    p = crear_productos("Dado de baja pytest")
    registrar_venta([(p["id"], 1)])
    eliminar_producto(p["id"])

    filas = _solo_mios(productos_mas_vendidos(None, None, 100, "unidades"), p)
    assert len(filas) == 1
    assert filas[0]["activo"] is False


def test_ranking_respeta_el_rango_de_fechas_y_el_limite(crear_productos):
    p = crear_productos("Rango pytest")
    registrar_venta([(p["id"], 1)])

    fuera = productos_mas_vendidos(datetime(2000, 1, 1), datetime(2000, 1, 2), 100, "unidades")
    assert _solo_mios(fuera, p) == []

    dentro = productos_mas_vendidos(*SIN_LIMITE_DE_FECHAS, 100, "unidades")
    assert len(_solo_mios(dentro, p)) == 1

    assert len(productos_mas_vendidos(None, None, 1, "unidades")) <= 1
