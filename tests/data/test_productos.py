"""Pruebas de acceso a datos de RF1-RF4.

Requieren un .env con credenciales reales de MySQL -- se saltan solas
si no hay ninguna configurada. Cada test borra lo que crea, para no
dejar basura en la base compartida de Aiven.
"""

import os

import pytest

from gedenaz.data.db import connection_scope
from gedenaz.data.productos import (
    actualizar_producto,
    crear_producto,
    eliminar_producto,
    listar_productos,
    obtener_producto,
)

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


def test_listar_productos_encuentra_por_nombre_y_categoria():
    p1 = crear_producto(nombre="Anillo pytest data", categoria="anillo", precio=1, stock=1)
    p2 = crear_producto(nombre="Collar pytest data", categoria="collar", precio=1, stock=1)
    try:
        por_nombre = listar_productos(nombre="pytest data")
        ids = {p["id"] for p in por_nombre}
        assert {p1["id"], p2["id"]} <= ids

        por_categoria = listar_productos(categoria="anillo")
        ids_categoria = {p["id"] for p in por_categoria}
        assert p1["id"] in ids_categoria
        assert p2["id"] not in ids_categoria
    finally:
        _borrar(p1["id"])
        _borrar(p2["id"])


def test_obtener_producto_existente_y_no_existente():
    creado = crear_producto(nombre="Detalle pytest", categoria="prueba", precio=1, stock=1)
    try:
        detalle = obtener_producto(creado["id"])
        assert detalle == creado
        assert obtener_producto(-1) is None
    finally:
        _borrar(creado["id"])


def test_actualizar_producto_cambia_los_campos():
    creado = crear_producto(nombre="Original pytest", categoria="anillo", precio=100, stock=5)
    try:
        actualizado = actualizar_producto(
            creado["id"], nombre="Editado pytest", categoria="collar", precio=200, stock=10
        )
        assert actualizado["nombre"] == "Editado pytest"
        assert actualizado["categoria"] == "collar"
        assert actualizado["precio"] == 200
        assert actualizado["stock"] == 10

        assert actualizar_producto(-1, nombre="x", categoria="x", precio=1, stock=1) is None
    finally:
        _borrar(creado["id"])


def test_eliminar_producto_es_baja_logica():
    creado = crear_producto(nombre="A eliminar pytest", categoria="prueba", precio=1, stock=1)
    try:
        assert eliminar_producto(creado["id"]) is True
        # Baja logica: ya no aparece como activo...
        assert obtener_producto(creado["id"]) is None
        # ...pero la fila sigue existiendo en la base (no se borro fisico).
        with connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT activo FROM producto WHERE id = %s", (creado["id"],))
            fila = cursor.fetchone()
            cursor.close()
        assert fila is not None
        assert fila[0] == 0
        # Repetir la baja sobre algo ya inactivo no encuentra nada que borrar.
        assert eliminar_producto(creado["id"]) is False
    finally:
        _borrar(creado["id"])
