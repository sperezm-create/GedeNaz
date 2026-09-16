"""Acceso a datos de la entidad Producto (RF1 -- ver
docs/specs/02-modelo-de-datos.md). Unica capa que ejecuta SQL sobre la
tabla `producto`; logic/productos.py llama a estas funciones, nunca al
reves.
"""

from decimal import Decimal

from gedenaz.data.db import connection_scope

_COLUMNAS = (
    "id, nombre, categoria, precio, stock, activo, "
    "fecha_creacion, fecha_actualizacion"
)


def _serializar(fila: tuple) -> dict:
    id_, nombre, categoria, precio, stock, activo, creado, actualizado = fila
    return {
        "id": id_,
        "nombre": nombre,
        "categoria": categoria,
        "precio": float(precio) if isinstance(precio, Decimal) else precio,
        "stock": stock,
        "activo": bool(activo),
        "fecha_creacion": creado.isoformat() if creado else None,
        "fecha_actualizacion": actualizado.isoformat() if actualizado else None,
    }


def crear_producto(nombre: str, categoria: str, precio: float, stock: int) -> dict:
    """Inserta un producto nuevo y devuelve la fila ya guardada (con id
    y timestamps asignados por MySQL)."""
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO producto (nombre, categoria, precio, stock) "
            "VALUES (%s, %s, %s, %s)",
            (nombre, categoria, precio, stock),
        )
        conn.commit()
        nuevo_id = cursor.lastrowid

        cursor.execute(
            f"SELECT {_COLUMNAS} FROM producto WHERE id = %s", (nuevo_id,)
        )
        fila = cursor.fetchone()
        cursor.close()

    return _serializar(fila)
