"""Pruebas de los endpoints HTTP de RF1-RF4.

Requieren un .env con credenciales reales de MySQL -- se saltan solas
si no hay ninguna configurada. Cada test borra lo que crea.
"""

import os

import pytest

from gedenaz.app import create_app
from gedenaz.data.db import connection_scope

pytestmark = pytest.mark.skipif(
    not os.getenv("DB_PASSWORD"),
    reason="Requiere un .env con credenciales reales de MySQL",
)


def _borrar(id_: int) -> None:
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM producto WHERE id = %s", (id_,))
        conn.commit()
        cursor.close()


def test_post_productos_crea_y_devuelve_201():
    client = create_app().test_client()
    response = client.post(
        "/productos",
        json={"nombre": "Test API pytest", "categoria": "prueba", "precio": 2500, "stock": 5},
    )
    body = response.get_json()
    try:
        assert response.status_code == 201
        assert body["nombre"] == "Test API pytest"
        assert body["id"] > 0
    finally:
        if body and "id" in body:
            _borrar(body["id"])


def test_post_productos_valida_campos_obligatorios():
    client = create_app().test_client()
    response = client.post("/productos", json={"categoria": "prueba", "precio": 100, "stock": 1})

    assert response.status_code == 400
    assert "nombre" in response.get_json()["errores"]


def test_post_productos_valida_stock_negativo():
    client = create_app().test_client()
    response = client.post(
        "/productos",
        json={"nombre": "Anillo", "categoria": "prueba", "precio": 100, "stock": -1},
    )

    assert response.status_code == 400
    assert "stock" in response.get_json()["errores"]


def test_get_productos_lista_y_filtra():
    client = create_app().test_client()
    creado = client.post(
        "/productos",
        json={"nombre": "Listar API pytest", "categoria": "anillo", "precio": 10, "stock": 1},
    ).get_json()
    try:
        respuesta = client.get("/productos?nombre=Listar API pytest")
        assert respuesta.status_code == 200
        ids = {p["id"] for p in respuesta.get_json()}
        assert creado["id"] in ids
    finally:
        _borrar(creado["id"])


def test_get_producto_detalle_200_y_404():
    client = create_app().test_client()
    creado = client.post(
        "/productos",
        json={"nombre": "Detalle API pytest", "categoria": "anillo", "precio": 10, "stock": 1},
    ).get_json()
    try:
        ok = client.get(f"/productos/{creado['id']}")
        assert ok.status_code == 200
        assert ok.get_json()["nombre"] == "Detalle API pytest"

        no_existe = client.get("/productos/999999999")
        assert no_existe.status_code == 404
    finally:
        _borrar(creado["id"])


def test_put_producto_actualiza_y_valida():
    client = create_app().test_client()
    creado = client.post(
        "/productos",
        json={"nombre": "Editar API pytest", "categoria": "anillo", "precio": 10, "stock": 1},
    ).get_json()
    try:
        editado = client.put(
            f"/productos/{creado['id']}",
            json={"nombre": "Editado API pytest", "categoria": "collar", "precio": 20, "stock": 2},
        )
        assert editado.status_code == 200
        assert editado.get_json()["nombre"] == "Editado API pytest"

        invalido = client.put(
            f"/productos/{creado['id']}",
            json={"nombre": "Editado API pytest", "categoria": "collar", "precio": 20, "stock": -1},
        )
        assert invalido.status_code == 400

        no_existe = client.put(
            "/productos/999999999",
            json={"nombre": "x", "categoria": "x", "precio": 1, "stock": 1},
        )
        assert no_existe.status_code == 404
    finally:
        _borrar(creado["id"])


def test_delete_producto_da_de_baja_y_404_si_no_existe():
    client = create_app().test_client()
    creado = client.post(
        "/productos",
        json={"nombre": "Eliminar API pytest", "categoria": "anillo", "precio": 10, "stock": 1},
    ).get_json()
    try:
        borrado = client.delete(f"/productos/{creado['id']}")
        assert borrado.status_code == 204

        ya_no_esta = client.get(f"/productos/{creado['id']}")
        assert ya_no_esta.status_code == 404

        no_existe = client.delete("/productos/999999999")
        assert no_existe.status_code == 404
    finally:
        _borrar(creado["id"])
