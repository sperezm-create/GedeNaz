import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def limpiar_productos_y_ventas(producto_ids: list[int]) -> None:
    """Borra productos de prueba Y las ventas que los usaron, en el orden
    que exigen las claves foraneas: lineas -> ventas -> productos."""
    if not producto_ids:
        return

    from gedenaz.data.db import connection_scope

    marcas = ", ".join(["%s"] * len(producto_ids))
    with connection_scope() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT DISTINCT venta_id FROM detalle_venta WHERE producto_id IN ({marcas})",
            producto_ids,
        )
        venta_ids = [fila[0] for fila in cursor.fetchall()]
        cursor.execute(
            f"DELETE FROM detalle_venta WHERE producto_id IN ({marcas})", producto_ids
        )
        if venta_ids:
            marcas_ventas = ", ".join(["%s"] * len(venta_ids))
            cursor.execute(f"DELETE FROM venta WHERE id IN ({marcas_ventas})", venta_ids)
        cursor.execute(f"DELETE FROM producto WHERE id IN ({marcas})", producto_ids)
        conn.commit()
        cursor.close()


@pytest.fixture
def crear_productos():
    """Fabrica de productos de prueba (requiere .env con MySQL real).
    Al terminar el test borra los productos creados y las ventas que los
    usaron, pase lo que pase."""
    from gedenaz.data.productos import crear_producto

    ids: list[int] = []

    def _crear(nombre: str, categoria: str = "prueba", precio: float = 100, stock: int = 10) -> dict:
        producto = crear_producto(nombre=nombre, categoria=categoria, precio=precio, stock=stock)
        ids.append(producto["id"])
        return producto

    yield _crear

    limpiar_productos_y_ventas(ids)
