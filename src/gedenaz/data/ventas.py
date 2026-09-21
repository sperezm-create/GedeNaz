"""Acceso a datos de las ventas (RF5 -- ver docs/specs/02-modelo-de-datos.md).
Unica capa que ejecuta SQL sobre `venta` y `detalle_venta`; logic/ventas.py
llama a estas funciones, nunca al reves.
"""

from datetime import datetime
from decimal import Decimal

from gedenaz.data.db import connection_scope


class ProductoNoDisponibleError(Exception):
    """Una linea de la venta apunta a un producto que no existe o esta de
    baja. `indice` es la posicion de esa linea en la lista recibida."""

    def __init__(self, indice: int, producto_id: int):
        self.indice = indice
        self.producto_id = producto_id
        super().__init__(f"items[{indice}]: producto {producto_id} no disponible")


class StockInsuficienteError(Exception):
    """Una linea pide mas unidades que el stock disponible."""

    def __init__(self, indice: int, producto_id: int, nombre: str, disponible: int, solicitado: int):
        self.indice = indice
        self.producto_id = producto_id
        self.nombre = nombre
        self.disponible = disponible
        self.solicitado = solicitado
        super().__init__(
            f"items[{indice}]: stock insuficiente de {nombre!r} "
            f"(disponible {disponible}, solicitado {solicitado})"
        )


def _armar_venta(id_: int, fecha: datetime, lineas: list[tuple]) -> dict:
    """`lineas`: tuplas (producto_id, nombre, cantidad, precio_unitario)."""
    items = []
    total = Decimal("0")
    for producto_id, nombre, cantidad, precio_unitario in lineas:
        subtotal = precio_unitario * cantidad
        total += subtotal
        items.append(
            {
                "producto_id": producto_id,
                "nombre": nombre,
                "cantidad": cantidad,
                "precio_unitario": float(precio_unitario),
                "subtotal": float(subtotal),
            }
        )
    return {
        "id": id_,
        "fecha_venta": fecha.isoformat(),
        "total": float(total),
        "items": items,
    }


def _leer_lineas(cursor, venta_ids: list[int]) -> dict[int, list[tuple]]:
    """Lineas de las ventas indicadas, agrupadas por venta_id y en el orden
    en que se registraron."""
    if not venta_ids:
        return {}
    placeholders = ", ".join(["%s"] * len(venta_ids))
    cursor.execute(
        "SELECT d.venta_id, d.producto_id, p.nombre, d.cantidad, d.precio_unitario "
        "FROM detalle_venta d JOIN producto p ON p.id = d.producto_id "
        f"WHERE d.venta_id IN ({placeholders}) ORDER BY d.id",
        venta_ids,
    )
    lineas: dict[int, list[tuple]] = {}
    for venta_id, producto_id, nombre, cantidad, precio in cursor.fetchall():
        lineas.setdefault(venta_id, []).append((producto_id, nombre, cantidad, precio))
    return lineas


def _leer_venta(cursor, venta_id: int) -> dict | None:
    cursor.execute("SELECT id, fecha_venta FROM venta WHERE id = %s", (venta_id,))
    fila = cursor.fetchone()
    if fila is None:
        return None
    lineas = _leer_lineas(cursor, [venta_id])
    return _armar_venta(fila[0], fila[1], lineas.get(venta_id, []))


def registrar_venta(items: list[tuple[int, int]]) -> dict:
    """Registra una venta completa en UNA transaccion y devuelve la venta.

    `items`: lista de (producto_id, cantidad), sin productos repetidos.
    Bloquea las filas de `producto` involucradas (SELECT ... FOR UPDATE, en
    orden de id para evitar bloqueos cruzados entre dos ventas
    simultaneas), valida existencia y stock, inserta la cabecera y las
    lineas (con el precio vigente como "foto") y descuenta el stock. Si
    algo falla se hace rollback y no queda nada guardado.

    Lanza ProductoNoDisponibleError o StockInsuficienteError.
    """
    ids = sorted({producto_id for producto_id, _ in items})

    with connection_scope() as conn:
        cursor = conn.cursor()
        try:
            placeholders = ", ".join(["%s"] * len(ids))
            cursor.execute(
                "SELECT id, nombre, precio, stock FROM producto "
                f"WHERE id IN ({placeholders}) AND activo = 1 ORDER BY id FOR UPDATE",
                ids,
            )
            productos = {fila[0]: fila for fila in cursor.fetchall()}

            for indice, (producto_id, cantidad) in enumerate(items):
                fila = productos.get(producto_id)
                if fila is None:
                    raise ProductoNoDisponibleError(indice, producto_id)
                if cantidad > fila[3]:
                    raise StockInsuficienteError(indice, producto_id, fila[1], fila[3], cantidad)

            cursor.execute("INSERT INTO venta (fecha_venta) VALUES (NOW())")
            venta_id = cursor.lastrowid

            for producto_id, cantidad in items:
                precio_vigente = productos[producto_id][2]
                cursor.execute(
                    "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario) "
                    "VALUES (%s, %s, %s, %s)",
                    (venta_id, producto_id, cantidad, precio_vigente),
                )
                cursor.execute(
                    "UPDATE producto SET stock = stock - %s WHERE id = %s",
                    (cantidad, producto_id),
                )

            conn.commit()
        except Exception:
            conn.rollback()
            cursor.close()
            raise

        venta = _leer_venta(cursor, venta_id)
        cursor.close()

    return venta


def obtener_venta(venta_id: int) -> dict | None:
    """Detalle de una venta, o None si no existe."""
    with connection_scope() as conn:
        cursor = conn.cursor()
        venta = _leer_venta(cursor, venta_id)
        cursor.close()
    return venta


def listar_ventas(desde: datetime | None = None, hasta_exclusivo: datetime | None = None) -> list[dict]:
    """Ventas (con sus lineas), de la mas reciente a la mas antigua.
    `desde` es inclusivo y `hasta_exclusivo` exclusivo (ver
    logic/filtros.py::parsear_rango_fechas)."""
    condiciones: list[str] = []
    parametros: list = []
    if desde is not None:
        condiciones.append("fecha_venta >= %s")
        parametros.append(desde)
    if hasta_exclusivo is not None:
        condiciones.append("fecha_venta < %s")
        parametros.append(hasta_exclusivo)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, fecha_venta FROM venta {where} ORDER BY fecha_venta DESC, id DESC",
            parametros,
        )
        cabeceras = cursor.fetchall()
        lineas = _leer_lineas(cursor, [c[0] for c in cabeceras])
        cursor.close()

    return [_armar_venta(id_, fecha, lineas.get(id_, [])) for id_, fecha in cabeceras]
