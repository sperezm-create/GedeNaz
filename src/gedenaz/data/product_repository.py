"""Persistencia de productos en MySQL o memoria local."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from mysql.connector import MySQLConnection

from gedenaz.data.database import with_connection


Product = dict[str, Any]
ConnectionRunner = Callable[[Callable[[MySQLConnection], object]], object]


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def create(self, product: Product) -> int:
        item = dict(product)
        item["id"] = len(self._items) + 1
        item["activo"] = 1
        item["fecha_creacion"] = datetime.now()
        item["fecha_ultimo_ingreso"] = item["fecha_creacion"]
        self._items.append(item)
        return int(item["id"])

    def add_stock_or_create(self, product: Product) -> int:
        for item in self._items:
            if (
                item.get("activo", 1) == 1
                and str(item.get("nombre", "")).casefold() == product["nombre"].casefold()
                and str(item.get("categoria", "")).casefold() == product["categoria"].casefold()
            ):
                item["stock"] += product["stock"]
                item["fecha_ultimo_ingreso"] = datetime.now()
                return int(item["id"])
        return self.create(product)

    def list_active(self, name: str = "", category: str = "") -> list[Product]:
        search_name = name.strip().lower()
        search_category = category.strip().lower()
        items = []
        for item in self._items:
            if item.get("activo", 1) != 1:
                continue
            if search_name and search_name not in str(item.get("nombre", "")).lower():
                continue
            if search_category and search_category not in str(item.get("categoria", "")).lower():
                continue
            items.append(dict(item))
        return items

    def get(self, product_id: int) -> Product | None:
        for item in self._items:
            if item.get("id") == product_id and item.get("activo", 1) == 1:
                return dict(item)
        return None

    def update(self, product_id: int, product: Product) -> None:
        for index, item in enumerate(self._items):
            if item.get("id") == product_id and item.get("activo", 1) == 1:
                self._items[index].update(dict(product))
                return
        raise ValueError("Producto no encontrado.")

    def deactivate(self, product_id: int) -> None:
        for item in self._items:
            if item.get("id") == product_id:
                item["activo"] = 0
                return


class ProductRepository:
    def __init__(self, connection_runner: ConnectionRunner = with_connection) -> None:
        self._connection_runner = connection_runner

    def create(self, product: Product) -> int:
        def insert(connection: MySQLConnection) -> int:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO producto (nombre, categoria, precio, stock)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (product["nombre"], product["categoria"], product["precio"], product["stock"]),
                )
                connection.commit()
                return int(cursor.lastrowid)
            finally:
                cursor.close()

        return int(self._connection_runner(insert))

    def add_stock_or_create(self, product: Product) -> int:
        def modify(connection: MySQLConnection) -> int:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id FROM producto
                    WHERE activo = 1 AND LOWER(nombre) = LOWER(%s)
                      AND LOWER(categoria) = LOWER(%s)
                    FOR UPDATE
                    """,
                    (product["nombre"], product["categoria"]),
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        """
                        UPDATE producto
                        SET stock = stock + %s, fecha_ultimo_ingreso = CURRENT_TIMESTAMP
                        WHERE id = %s AND activo = 1
                        """,
                        (product["stock"], existing["id"]),
                    )
                    product_id = int(existing["id"])
                else:
                    cursor.execute(
                        """
                        INSERT INTO producto
                            (nombre, categoria, precio, stock, fecha_ultimo_ingreso)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """,
                        (product["nombre"], product["categoria"], product["precio"], product["stock"]),
                    )
                    product_id = int(cursor.lastrowid)
                connection.commit()
                return product_id
            finally:
                cursor.close()

        return int(self._connection_runner(modify))

    def list_active(self, name: str = "", category: str = "") -> list[Product]:
        def select(connection: MySQLConnection) -> list[Product]:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, nombre, categoria, precio, stock,
                              activo, fecha_creacion, fecha_actualizacion,
                              fecha_ultimo_ingreso
                    FROM producto
                    WHERE activo = 1
                      AND LOWER(nombre) LIKE LOWER(%s)
                      AND LOWER(categoria) LIKE LOWER(%s)
                    ORDER BY nombre, id
                    """,
                    (f"%{name.strip()}%", f"%{category.strip()}%"),
                )
                return list(cursor.fetchall())
            finally:
                cursor.close()

        return list(self._connection_runner(select))

    def get(self, product_id: int) -> Product | None:
        def select(connection: MySQLConnection) -> Product | None:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, nombre, categoria, precio, stock,
                              activo, fecha_creacion, fecha_actualizacion,
                              fecha_ultimo_ingreso
                    FROM producto
                    WHERE id = %s AND activo = 1
                    """,
                    (product_id,),
                )
                return cursor.fetchone()
            finally:
                cursor.close()

        return self._connection_runner(select)

    def update(self, product_id: int, product: Product) -> None:
        def modify(connection: MySQLConnection) -> None:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE producto
                    SET nombre = %s, categoria = %s, precio = %s, stock = %s
                    WHERE id = %s AND activo = 1
                    """,
                    (product["nombre"], product["categoria"], product["precio"], product["stock"], product_id),
                )
                connection.commit()
            finally:
                cursor.close()

        self._connection_runner(modify)

    def deactivate(self, product_id: int) -> None:
        def modify(connection: MySQLConnection) -> None:
            cursor = connection.cursor()
            try:
                cursor.execute("UPDATE producto SET activo = 0 WHERE id = %s", (product_id,))
                connection.commit()
            finally:
                cursor.close()

        self._connection_runner(modify)
