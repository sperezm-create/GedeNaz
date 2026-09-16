"""Pruebas del endpoint HTTP de RF1 (POST /productos).

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
