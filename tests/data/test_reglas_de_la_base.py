"""Reglas que debe cumplir la BASE DE DATOS misma, no solo nuestro codigo.

Nuestra capa de logica ya valida todo esto antes de llegar a la base, pero
estas restricciones (CHECK, claves foraneas) y el comportamiento de
collation son la ultima linea de defensa, y son justo lo que puede cambiar
al mover el proyecto a otro proveedor compatible con MySQL (ver
docs/specs/02-modelo-de-datos.md). Correr esta suite contra la base nueva
antes de migrar.

Requieren un .env con credenciales reales -- se saltan solas si no hay.
Los INSERT directos que deben ser rechazados se hacen sin commit: si la
base NO los rechazara, igual no dejan residuos (la conexion se cierra).
"""

import os

import mysql.connector
import pytest

from gedenaz.data.db import connection_scope
from gedenaz.data.productos import eliminar_producto, listar_productos
from gedenaz.data.ventas import registrar_venta

pytestmark = pytest.mark.skipif(
    not os.getenv("DB_PASSWORD"),
    reason="Requiere un .env con credenciales reales de MySQL",
)


def test_busqueda_por_nombre_no_distingue_mayusculas(crear_productos):
    """RF2: 'coincidencia insensible a mayusculas/minusculas'. Depende de la
    collation de la base (utf8mb4_bin, por ejemplo, la haria sensible)."""
    p = crear_productos("Anillo MAYUSCULAS pytest", categoria="Collar")

    por_nombre = listar_productos(nombre="anillo mayusculas PYTEST")
    assert p["id"] in {f["id"] for f in por_nombre}

    por_categoria = listar_productos(categoria="COLLAR")
    assert p["id"] in {f["id"] for f in por_categoria}


def test_la_base_rechaza_stock_negativo():
    with connection_scope() as conn:
        cursor = conn.cursor()
        with pytest.raises(mysql.connector.Error):
            cursor.execute(
                "INSERT INTO producto (nombre, categoria, precio, stock) "
                "VALUES ('Stock negativo pytest', 'prueba', 100, -1)"
            )
        conn.rollback()


def test_la_base_rechaza_precio_no_positivo():
    with connection_scope() as conn:
        cursor = conn.cursor()
        with pytest.raises(mysql.connector.Error):
            cursor.execute(
                "INSERT INTO producto (nombre, categoria, precio, stock) "
                "VALUES ('Precio cero pytest', 'prueba', 0, 1)"
            )
        conn.rollback()


def test_la_base_rechaza_cantidad_no_positiva_en_una_linea_de_venta(crear_productos):
    p = crear_productos("Cantidad cero pytest")
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO venta (fecha_venta) VALUES (NOW())")
        venta_id = cursor.lastrowid
        with pytest.raises(mysql.connector.Error):
            cursor.execute(
                "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario) "
                "VALUES (%s, %s, 0, 100)",
                (venta_id, p["id"]),
            )
        conn.rollback()


def test_la_base_rechaza_una_linea_de_venta_de_un_producto_inexistente():
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO venta (fecha_venta) VALUES (NOW())")
        venta_id = cursor.lastrowid
        with pytest.raises(mysql.connector.Error):
            cursor.execute(
                "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario) "
                "VALUES (%s, 999999999, 1, 100)",
                (venta_id,),
            )
        conn.rollback()


def test_la_base_impide_borrar_fisicamente_un_producto_con_ventas(crear_productos):
    """Por eso RF4 es baja logica: el historial de ventas no se puede perder."""
    p = crear_productos("Con ventas pytest", stock=5)
    registrar_venta([(p["id"], 1)])

    with connection_scope() as conn:
        cursor = conn.cursor()
        with pytest.raises(mysql.connector.Error):
            cursor.execute("DELETE FROM producto WHERE id = %s", (p["id"],))
        conn.rollback()

    assert eliminar_producto(p["id"]) is True  # la baja logica si funciona
