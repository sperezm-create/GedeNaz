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


def listar_productos(nombre: str | None = None, categoria: str | None = None) -> list[dict]:
    """Lista productos activos, opcionalmente filtrados por nombre y/o
    categoria (coincidencia parcial, sin distinguir mayusculas/minusculas --
    ver docs/specs/01-requisitos-funcionales.md RF2)."""
    condiciones = ["activo = 1"]
    parametros: list = []

    if nombre:
        condiciones.append("nombre LIKE %s")
        parametros.append(f"%{nombre}%")
    if categoria:
        condiciones.append("categoria LIKE %s")
        parametros.append(f"%{categoria}%")

    where = " AND ".join(condiciones)

    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {_COLUMNAS} FROM producto WHERE {where} ORDER BY nombre",
            parametros,
        )
        filas = cursor.fetchall()
        cursor.close()

    return [_serializar(fila) for fila in filas]


def obtener_producto(id_: int) -> dict | None:
    """Devuelve el detalle de un producto activo, o None si no existe
    (o esta dado de baja)."""
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {_COLUMNAS} FROM producto WHERE id = %s AND activo = 1",
            (id_,),
        )
        fila = cursor.fetchone()
        cursor.close()

    return _serializar(fila) if fila else None


def actualizar_producto(
    id_: int, nombre: str, categoria: str, precio: float, stock: int
) -> dict | None:
    """Actualiza los 4 campos de un producto activo. Devuelve el producto
    ya actualizado, o None si no existe (o esta dado de baja)."""
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE producto SET nombre = %s, categoria = %s, precio = %s, "
            "stock = %s WHERE id = %s AND activo = 1",
            (nombre, categoria, precio, stock, id_),
        )
        conn.commit()
        actualizo_algo = cursor.rowcount > 0

        if not actualizo_algo:
            cursor.close()
            return None

        cursor.execute(
            f"SELECT {_COLUMNAS} FROM producto WHERE id = %s", (id_,)
        )
        fila = cursor.fetchone()
        cursor.close()

    return _serializar(fila)


def eliminar_producto(id_: int) -> bool:
    """Da de baja (baja logica, columna `activo`) un producto activo.
    Devuelve True si existia y se dio de baja, False si no existia (o ya
    estaba de baja) -- ver docs/specs/02-modelo-de-datos.md."""
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE producto SET activo = 0 WHERE id = %s AND activo = 1",
            (id_,),
        )
        conn.commit()
        dio_de_baja = cursor.rowcount > 0
        cursor.close()

    return dio_de_baja
