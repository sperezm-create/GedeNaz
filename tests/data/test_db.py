"""Pruebas de la capa de conexion (tarea 1.3, Carta Gantt).

Requieren un .env con credenciales reales de MySQL (ver
docs/specs/05-entorno-desarrollo.md, seccion 8) -- se saltan solas si no
hay ninguna configurada, para no romper el entorno de quien todavia no
monto su propia base.
"""

import os

import pytest

from gedenaz.data.db import connection_scope, get_connection

pytestmark = pytest.mark.skipif(
    not os.getenv("DB_PASSWORD"),
    reason="Requiere un .env con credenciales reales de MySQL",
)


def test_get_connection_conecta():
    conn = get_connection()
    try:
        assert conn.is_connected()
    finally:
        conn.close()


def test_connection_scope_corre_una_consulta_y_cierra_la_conexion():
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
        cursor.close()

    assert not conn.is_connected()
