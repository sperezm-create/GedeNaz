"""Pruebas de acceso a datos de RF1 (Crear producto).

Requieren un .env con credenciales reales de MySQL -- se saltan solas
si no hay ninguna configurada. Cada test borra lo que crea, para no
dejar basura en la base compartida de Aiven.
"""

import os

import pytest

from gedenaz.data.db import connection_scope
from gedenaz.data.productos import crear_producto

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


def test_crear_producto_lo_guarda_en_la_base():
    producto = crear_producto(nombre="Test pytest", categoria="prueba", precio=1.5, stock=0)
    try:
        assert producto["id"] > 0
        assert producto["nombre"] == "Test pytest"
        assert producto["categoria"] == "prueba"
        assert producto["precio"] == 1.5
        assert producto["stock"] == 0
        assert producto["activo"] is True
        assert producto["fecha_creacion"] is not None
    finally:
        _borrar(producto["id"])
