"""Consultas de reporte (RF3.1 -- ver docs/specs/01-requisitos-funcionales.md).
Solo lectura sobre `venta`, `detalle_venta` y `producto`.
"""

from datetime import datetime

from gedenaz.data.db import connection_scope

# Whitelist: `orden` se interpola en el SQL (no se puede parametrizar un
# ORDER BY), asi que solo se aceptan estas dos claves fijas.
_ORDEN_SQL = {
    "unidades": "unidades_vendidas DESC, p.nombre ASC",
    "ingresos": "ingresos DESC, p.nombre ASC",
}


def productos_mas_vendidos(
    desde: datetime | None,
    hasta_exclusivo: datetime | None,
    limite: int,
    orden: str,
) -> list[dict]:
    """Ranking de productos vendidos. Incluye productos dados de baja que
    tuvieron ventas (es historial, no inventario actual). Los ingresos usan
    el precio_unitario de cada linea, no el precio actual del producto."""
    order_by = _ORDEN_SQL[orden]  # KeyError si `orden` no esta validado antes

    condiciones: list[str] = []
    parametros: list = []
    if desde is not None:
        condiciones.append("v.fecha_venta >= %s")
        parametros.append(desde)
    if hasta_exclusivo is not None:
        condiciones.append("v.fecha_venta < %s")
        parametros.append(hasta_exclusivo)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.id, p.nombre, p.categoria, p.activo, "
            "       SUM(d.cantidad) AS unidades_vendidas, "
            "       SUM(d.cantidad * d.precio_unitario) AS ingresos "
            "FROM detalle_venta d "
            "JOIN venta v ON v.id = d.venta_id "
            "JOIN producto p ON p.id = d.producto_id "
            f"{where} "
            "GROUP BY p.id, p.nombre, p.categoria, p.activo "
            f"ORDER BY {order_by} "
            "LIMIT %s",
            (*parametros, limite),
        )
        filas = cursor.fetchall()
        cursor.close()

    return [
        {
            "producto_id": producto_id,
            "nombre": nombre,
            "categoria": categoria,
            "activo": bool(activo),
            "unidades_vendidas": int(unidades),
            "ingresos": float(ingresos),
        }
        for producto_id, nombre, categoria, activo, unidades, ingresos in filas
    ]
