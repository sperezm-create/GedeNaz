"""Persistencia de ventas en MySQL o memoria local."""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from copy import deepcopy
from decimal import Decimal
from typing import Any

from mysql.connector import MySQLConnection

from gedenaz.codes import product_code
from gedenaz.data.database import with_connection
from gedenaz.data.product_repository import InMemoryProductRepository
from gedenaz.installments import build_installment_schedule


SaleItem = dict[str, Any]
Sale = dict[str, Any]
ConnectionRunner = Callable[[Callable[[MySQLConnection], object]], object]


def _update_installment_totals(plan: dict[str, Any]) -> None:
    total_paid = Decimal("0")
    total_balance = Decimal("0")
    for installment in plan["cuotas"]:
        paid = sum(
            (Decimal(str(payment["monto"])) for payment in installment["abonos"]),
            Decimal("0"),
        )
        balance = Decimal(str(installment["monto"])) - paid
        installment["pagado"] = paid
        installment["saldo"] = balance
        installment["estado"] = (
            "Pagada" if balance == 0 else "Parcial" if paid > 0 else "Pendiente"
        )
        total_paid += paid
        total_balance += balance
    plan["total_pagado"] = total_paid
    plan["saldo_pendiente"] = total_balance


def _payment_plan_from_rows(
    plan_row: dict[str, Any],
    installment_rows: list[dict[str, Any]],
    payment_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    payments_by_installment: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for payment in payment_rows:
        payments_by_installment[int(payment["cuota_id"])].append(
            {"monto": payment["monto"], "fecha_pago": payment["fecha_pago"]}
        )
    installments = []
    for row in installment_rows:
        installments.append(
            {
                "id": int(row["id"]),
                "numero": int(row["numero"]),
                "monto": Decimal(str(row["monto"])),
                "fecha_vencimiento": row["fecha_vencimiento"],
                "abonos": payments_by_installment[int(row["id"])],
            }
        )
    plan = {
        "id": int(plan_row["id"]),
        "frecuencia": plan_row["frecuencia"],
        "monto_total": Decimal(str(plan_row["monto_total"])),
        "primer_vencimiento": plan_row["primer_vencimiento"],
        "cuotas": installments,
    }
    _update_installment_totals(plan)
    return plan


def _fetch_payment_plan(cursor, sale_id: int) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT id, venta_id, frecuencia, monto_total, primer_vencimiento
        FROM plan_pago
        WHERE venta_id = %s
        """,
        (sale_id,),
    )
    plan_row = cursor.fetchone()
    if plan_row is None:
        return None

    cursor.execute(
        """
        SELECT id, plan_pago_id, numero, monto, fecha_vencimiento
        FROM cuota
        WHERE plan_pago_id = %s
        ORDER BY numero
        """,
        (plan_row["id"],),
    )
    installment_rows = list(cursor.fetchall())
    installment_ids = [row["id"] for row in installment_rows]
    payment_rows = []
    if installment_ids:
        placeholders = ", ".join(["%s"] * len(installment_ids))
        cursor.execute(
            f"""
            SELECT cuota_id, monto, fecha_pago
            FROM abono
            WHERE cuota_id IN ({placeholders})
            ORDER BY fecha_pago, id
            """,
            tuple(installment_ids),
        )
        payment_rows = list(cursor.fetchall())
    return _payment_plan_from_rows(plan_row, installment_rows, payment_rows)


def _build_sale_item(
    product: dict[str, Any],
    quantity: int,
    genero_destino: str = "No especificado",
) -> SaleItem:
    price = Decimal(str(product["precio"]))
    return {
        "product_id": int(product["id"]),
        "codigo_producto": product_code(int(product["id"])),
        "nombre_producto": str(product["nombre"]),
        "categoria_producto": str(product["categoria"]),
        "material_producto": str(product.get("material", "Sin especificar")),
        "talla_producto": str(product.get("talla", "Única")),
        "genero_destino": genero_destino,
        "precio_unitario": price,
        "cantidad": quantity,
        "subtotal": price * quantity,
    }


class InMemorySalesRepository:
    def __init__(self, product_repository: InMemoryProductRepository | None = None) -> None:
        self._product_repository = product_repository
        self._sales: list[Sale] = []

    def create_sale(
        self,
        requested_items: list[dict[str, Any]],
        payment_plan: dict[str, Any] | None = None,
    ) -> Sale:
        if self._product_repository is None:
            raise RuntimeError("El repositorio de productos no está disponible para registrar la venta.")

        items: list[SaleItem] = []
        products_by_id: dict[int, dict[str, Any]] = {}
        quantities_by_product: dict[int, int] = defaultdict(int)
        for requested in requested_items:
            product = self._product_repository.get(requested["product_id"])
            if product is None:
                raise ValueError(f"El producto {requested['product_id']} ya no está disponible.")
            quantity = requested["quantity"]
            items.append(_build_sale_item(product, quantity, requested.get("genero_destino", "No especificado")))
            product_id = int(product["id"])
            products_by_id[product_id] = product
            quantities_by_product[product_id] += quantity

        products_to_update = []
        for product_id, quantity in quantities_by_product.items():
            product = products_by_id[product_id]
            if product["stock"] < quantity:
                raise ValueError(
                    f"Stock insuficiente para {product['nombre']}. Disponible: {product['stock']}."
                )
            products_to_update.append((product, product["stock"] - quantity))

        total = sum((item["subtotal"] for item in items), Decimal("0"))
        saved_plan = None
        if payment_plan is not None:
            saved_plan = {
                "frecuencia": payment_plan["frecuencia"],
                "monto_total": total,
                "primer_vencimiento": payment_plan["primer_vencimiento"],
                "cuotas": build_installment_schedule(
                    total,
                    payment_plan["cantidad_cuotas"],
                    payment_plan["frecuencia"],
                    payment_plan["primer_vencimiento"],
                ),
            }
            _update_installment_totals(saved_plan)

        updated_products: list[dict[str, Any]] = []
        try:
            for product, stock in products_to_update:
                self._product_repository.update(
                    product["id"],
                    {
                        "nombre": product["nombre"],
                        "categoria": product["categoria"],
                        "material": product.get("material", "Sin especificar"),
                        "talla": product.get("talla", "Única"),
                        "precio": product["precio"],
                        "stock": stock,
                    },
                )
                updated_products.append(product)
        except Exception:
            for product in updated_products:
                self._product_repository.update(
                    product["id"],
                    {
                        "nombre": product["nombre"],
                        "categoria": product["categoria"],
                        "material": product.get("material", "Sin especificar"),
                        "talla": product.get("talla", "Única"),
                        "precio": product["precio"],
                        "stock": product["stock"],
                    },
                )
            raise

        sale_id = len(self._sales) + 1
        sale = {
            "id": sale_id,
            "fecha": datetime.now(),
            "total": total,
            "items": items,
            "anulada": False,
            "payment_plan": saved_plan,
        }
        self._sales.append(sale)
        return self._copy_sale(sale)

    def list_sales(self) -> list[Sale]:
        return [self._copy_sale(sale) for sale in reversed(self._sales)]

    def cancel_sale(self, sale_id: int) -> None:
        sale = next((item for item in self._sales if item["id"] == sale_id), None)
        if sale is None:
            raise ValueError("No se encontró la boleta seleccionada.")
        if sale["anulada"]:
            raise ValueError("Esta boleta ya fue anulada.")
        plan = sale.get("payment_plan")
        if plan and any(item["abonos"] for item in plan["cuotas"]):
            raise ValueError(
                "No se puede anular una venta con abonos registrados. "
                "Resuelve la devolución de los pagos antes de anularla."
            )
        if self._product_repository is None:
            raise RuntimeError("El repositorio de productos no está disponible para devolver el stock.")

        restored_items: list[SaleItem] = []
        try:
            for item in sale["items"]:
                self._product_repository.adjust_stock(item["product_id"], item["cantidad"])
                restored_items.append(item)
        except Exception:
            for item in reversed(restored_items):
                self._product_repository.adjust_stock(item["product_id"], -item["cantidad"])
            raise
        sale["anulada"] = True

    def add_payment(self, sale_id: int, installment_number: int, amount: Decimal) -> dict[str, Any]:
        sale = next((item for item in self._sales if item["id"] == sale_id), None)
        if sale is None:
            raise ValueError("No se encontró la venta seleccionada.")
        if sale["anulada"]:
            raise ValueError("No se pueden registrar pagos para una venta anulada.")
        plan = sale.get("payment_plan")
        if plan is None:
            raise ValueError("La venta no tiene un plan de cuotas.")
        installment = next(
            (item for item in plan["cuotas"] if item["numero"] == installment_number),
            None,
        )
        if installment is None:
            raise ValueError("No se encontró la cuota seleccionada.")
        if amount > installment["saldo"]:
            raise ValueError(
                f"El abono supera el saldo de la cuota ({installment['saldo']})."
            )
        installment["abonos"].append({"monto": amount, "fecha_pago": datetime.now()})
        _update_installment_totals(plan)
        return deepcopy(plan)

    def get_payment_plan(self, sale_id: int) -> dict[str, Any] | None:
        sale = next((item for item in self._sales if item["id"] == sale_id), None)
        return deepcopy(sale.get("payment_plan")) if sale else None

    def product_stats(self) -> list[dict[str, Any]]:
        totals: dict[int, dict[str, Any]] = {}
        for sale in self._sales:
            if sale["anulada"]:
                continue
            for item in sale["items"]:
                product_id = item["product_id"]
                stats = totals.setdefault(
                    product_id,
                    {
                        "product_id": product_id,
                        "codigo_producto": item["codigo_producto"],
                        "nombre_producto": item["nombre_producto"],
                        "unidades_vendidas": 0,
                        "ingresos": Decimal("0"),
                    },
                )
                stats["unidades_vendidas"] += item["cantidad"]
                stats["ingresos"] += item["subtotal"]
        return sorted(
            totals.values(),
            key=lambda item: (-item["unidades_vendidas"], item["codigo_producto"]),
        )

    def category_stats(self) -> list[dict[str, Any]]:
        totals: dict[str, int] = defaultdict(int)
        for sale in self._sales:
            if sale["anulada"]:
                continue
            for item in sale["items"]:
                totals[item["categoria_producto"]] += item["cantidad"]
        total_units = sum(totals.values())
        return [
            {
                "categoria": category,
                "unidades_vendidas": units,
                "porcentaje": (Decimal(units) * 100 / total_units).quantize(Decimal("0.01")),
            }
            for category, units in sorted(totals.items(), key=lambda entry: (-entry[1], entry[0].casefold()))
        ] if total_units else []

    def price_stats(self) -> list[dict[str, Any]]:
        totals: dict[Decimal, int] = defaultdict(int)
        for sale in self._sales:
            if sale["anulada"]:
                continue
            for item in sale["items"]:
                totals[item["precio_unitario"]] += item["cantidad"]
        return [
            {"precio_unitario": price, "unidades_vendidas": units}
            for price, units in sorted(totals.items(), key=lambda entry: (-entry[1], entry[0]))
        ]

    @staticmethod
    def _copy_sale(sale: Sale) -> Sale:
        return deepcopy(sale)


class SalesRepository:
    def __init__(self, connection_runner: ConnectionRunner = with_connection) -> None:
        self._connection_runner = connection_runner

    def create_sale(
        self,
        requested_items: list[dict[str, Any]],
        payment_plan: dict[str, Any] | None = None,
    ) -> Sale:
        def insert(connection: MySQLConnection) -> Sale:
            cursor = connection.cursor(dictionary=True)
            try:
                items: list[SaleItem] = []
                quantities_by_product: dict[int, int] = defaultdict(int)
                products_by_id: dict[int, dict[str, Any]] = {}
                for requested in requested_items:
                    cursor.execute(
                        """
                        SELECT id, nombre, categoria, material, talla, precio, stock, activo
                        FROM producto
                        WHERE id = %s
                        FOR UPDATE
                        """,
                        (requested["product_id"],),
                    )
                    product = cursor.fetchone()
                    if product is None or product["activo"] != 1:
                        raise ValueError(f"El producto {requested['product_id']} ya no está disponible.")
                    quantity = requested["quantity"]
                    product_id = int(product["id"])
                    quantities_by_product[product_id] += quantity
                    products_by_id[product_id] = product
                    items.append(
                        _build_sale_item(
                            product,
                            quantity,
                            requested.get("genero_destino", "No especificado"),
                        )
                    )

                for product_id, quantity in quantities_by_product.items():
                    product = products_by_id[product_id]
                    if product["stock"] < quantity:
                        raise ValueError(
                            f"Stock insuficiente para {product['nombre']}. "
                            f"Disponible: {product['stock']}."
                        )

                total = sum((item["subtotal"] for item in items), Decimal("0"))
                cursor.execute("INSERT INTO venta (total) VALUES (%s)", (total,))
                sale_id = int(cursor.lastrowid)
                cursor.execute("SELECT fecha FROM venta WHERE id = %s", (sale_id,))
                sale_date = cursor.fetchone()["fecha"]
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO detalle_venta
                            (venta_id, producto_id, codigo_producto, nombre_producto, categoria_producto,
                             material_producto, talla_producto, genero_destino,
                             precio_unitario, cantidad, subtotal)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            sale_id,
                            item["product_id"],
                            item["codigo_producto"],
                            item["nombre_producto"],
                            item["categoria_producto"],
                            item["material_producto"],
                            item["talla_producto"],
                            item["genero_destino"],
                            item["precio_unitario"],
                            item["cantidad"],
                            item["subtotal"],
                        ),
                    )
                    cursor.execute(
                        "UPDATE producto SET stock = stock - %s WHERE id = %s AND activo = 1",
                        (item["cantidad"], item["product_id"]),
                    )

                saved_plan = None
                if payment_plan is not None:
                    schedule = build_installment_schedule(
                        total,
                        payment_plan["cantidad_cuotas"],
                        payment_plan["frecuencia"],
                        payment_plan["primer_vencimiento"],
                    )
                    cursor.execute(
                        """
                        INSERT INTO plan_pago
                            (venta_id, cantidad_cuotas, frecuencia, monto_total, primer_vencimiento)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            sale_id,
                            payment_plan["cantidad_cuotas"],
                            payment_plan["frecuencia"],
                            total,
                            payment_plan["primer_vencimiento"],
                        ),
                    )
                    plan_id = int(cursor.lastrowid)
                    for installment in schedule:
                        cursor.execute(
                            """
                            INSERT INTO cuota
                                (plan_pago_id, numero, monto, fecha_vencimiento)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                plan_id,
                                installment["numero"],
                                installment["monto"],
                                installment["fecha_vencimiento"],
                            ),
                        )
                    saved_plan = {
                        "id": plan_id,
                        "frecuencia": payment_plan["frecuencia"],
                        "monto_total": total,
                        "primer_vencimiento": payment_plan["primer_vencimiento"],
                        "cuotas": schedule,
                    }
                    _update_installment_totals(saved_plan)

                connection.commit()
                return {
                    "id": sale_id,
                    "fecha": sale_date,
                    "total": total,
                    "items": items,
                    "anulada": False,
                    "payment_plan": saved_plan,
                }
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        return self._connection_runner(insert)

    def list_sales(self) -> list[Sale]:
        def select(connection: MySQLConnection) -> list[Sale]:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, fecha, total, anulada FROM venta ORDER BY id DESC")
                sales = list(cursor.fetchall())
                if not sales:
                    return []

                sale_ids = [sale["id"] for sale in sales]
                placeholders = ", ".join(["%s"] * len(sale_ids))
                cursor.execute(
                    f"""
                    SELECT venta_id, producto_id, codigo_producto, nombre_producto, categoria_producto,
                           material_producto, talla_producto, genero_destino,
                           precio_unitario, cantidad, subtotal
                    FROM detalle_venta
                    WHERE venta_id IN ({placeholders})
                    ORDER BY id
                    """,
                    tuple(sale_ids),
                )
                items_by_sale: dict[int, list[SaleItem]] = defaultdict(list)
                for item in cursor.fetchall():
                    items_by_sale[item["venta_id"]].append(
                        {
                            "product_id": item["producto_id"],
                            "codigo_producto": item["codigo_producto"],
                            "nombre_producto": item["nombre_producto"],
                            "categoria_producto": item["categoria_producto"],
                            "material_producto": item["material_producto"],
                            "talla_producto": item["talla_producto"],
                            "genero_destino": item["genero_destino"],
                            "precio_unitario": item["precio_unitario"],
                            "cantidad": item["cantidad"],
                            "subtotal": item["subtotal"],
                        }
                    )

                cursor.execute(
                    f"""
                    SELECT id, venta_id, frecuencia, monto_total, primer_vencimiento
                    FROM plan_pago
                    WHERE venta_id IN ({placeholders})
                    """,
                    tuple(sale_ids),
                )
                plan_rows = list(cursor.fetchall())
                plans_by_sale: dict[int, dict[str, Any]] = {}
                if plan_rows:
                    plan_ids = [plan["id"] for plan in plan_rows]
                    plan_placeholders = ", ".join(["%s"] * len(plan_ids))
                    cursor.execute(
                        f"""
                        SELECT id, plan_pago_id, numero, monto, fecha_vencimiento
                        FROM cuota
                        WHERE plan_pago_id IN ({plan_placeholders})
                        ORDER BY plan_pago_id, numero
                        """,
                        tuple(plan_ids),
                    )
                    installment_rows = list(cursor.fetchall())
                    installment_ids = [row["id"] for row in installment_rows]
                    payments_by_installment: dict[int, list[dict[str, Any]]] = defaultdict(list)
                    if installment_ids:
                        installment_placeholders = ", ".join(["%s"] * len(installment_ids))
                        cursor.execute(
                            f"""
                            SELECT cuota_id, monto, fecha_pago
                            FROM abono
                            WHERE cuota_id IN ({installment_placeholders})
                            ORDER BY fecha_pago, id
                            """,
                            tuple(installment_ids),
                        )
                        payment_rows = list(cursor.fetchall())
                        for payment in payment_rows:
                            payments_by_installment[int(payment["cuota_id"])].append(payment)

                    installments_by_plan: dict[int, list[dict[str, Any]]] = defaultdict(list)
                    for installment in installment_rows:
                        installments_by_plan[int(installment["plan_pago_id"])].append(installment)
                    for plan_row in plan_rows:
                        plan_id = int(plan_row["id"])
                        plan_installments = installments_by_plan[plan_id]
                        plan_payments = [
                            payment
                            for installment in plan_installments
                            for payment in payments_by_installment[int(installment["id"])]
                        ]
                        plans_by_sale[int(plan_row["venta_id"])] = _payment_plan_from_rows(
                            plan_row,
                            plan_installments,
                            plan_payments,
                        )
                return [
                    {
                        **sale,
                        "items": items_by_sale[sale["id"]],
                        "payment_plan": plans_by_sale.get(int(sale["id"])),
                    }
                    for sale in sales
                ]
            finally:
                cursor.close()

        return list(self._connection_runner(select))

    def get_payment_plan(self, sale_id: int) -> dict[str, Any] | None:
        def select(connection: MySQLConnection) -> dict[str, Any] | None:
            cursor = connection.cursor(dictionary=True)
            try:
                return _fetch_payment_plan(cursor, sale_id)
            finally:
                cursor.close()

        return self._connection_runner(select)

    def add_payment(self, sale_id: int, installment_number: int, amount: Decimal) -> dict[str, Any]:
        def insert(connection: MySQLConnection) -> dict[str, Any]:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id, anulada FROM venta WHERE id = %s FOR UPDATE",
                    (sale_id,),
                )
                sale = cursor.fetchone()
                if sale is None:
                    raise ValueError("No se encontró la venta seleccionada.")
                if sale["anulada"]:
                    raise ValueError("No se pueden registrar pagos para una venta anulada.")

                cursor.execute(
                    """
                    SELECT cuota.id, cuota.monto
                    FROM cuota
                    INNER JOIN plan_pago ON plan_pago.id = cuota.plan_pago_id
                    WHERE plan_pago.venta_id = %s AND cuota.numero = %s
                    FOR UPDATE
                    """,
                    (sale_id, installment_number),
                )
                installment = cursor.fetchone()
                if installment is None:
                    raise ValueError("No se encontró la cuota seleccionada.")

                cursor.execute(
                    "SELECT COALESCE(SUM(monto), 0) AS pagado FROM abono WHERE cuota_id = %s",
                    (installment["id"],),
                )
                paid = Decimal(str(cursor.fetchone()["pagado"]))
                balance = Decimal(str(installment["monto"])) - paid
                if amount > balance:
                    raise ValueError(f"El abono supera el saldo de la cuota ({balance}).")

                cursor.execute(
                    "INSERT INTO abono (cuota_id, monto) VALUES (%s, %s)",
                    (installment["id"], amount),
                )
                plan = _fetch_payment_plan(cursor, sale_id)
                if plan is None:
                    raise RuntimeError("No se pudo volver a cargar el plan de cuotas.")
                connection.commit()
                return plan
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        return self._connection_runner(insert)

    def cancel_sale(self, sale_id: int) -> None:
        def modify(connection: MySQLConnection) -> None:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id, anulada FROM venta WHERE id = %s FOR UPDATE",
                    (sale_id,),
                )
                sale = cursor.fetchone()
                if sale is None:
                    raise ValueError("No se encontró la boleta seleccionada.")
                if sale["anulada"]:
                    raise ValueError("Esta boleta ya fue anulada.")

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(abono.monto), 0) AS total_pagado
                    FROM plan_pago
                    INNER JOIN cuota ON cuota.plan_pago_id = plan_pago.id
                    LEFT JOIN abono ON abono.cuota_id = cuota.id
                    WHERE plan_pago.venta_id = %s
                    """,
                    (sale_id,),
                )
                payment_total = Decimal(str(cursor.fetchone()["total_pagado"]))
                if payment_total > 0:
                    raise ValueError(
                        "No se puede anular una venta con abonos registrados. "
                        "Resuelve la devolución de los pagos antes de anularla."
                    )

                cursor.execute(
                    "SELECT producto_id, cantidad FROM detalle_venta WHERE venta_id = %s",
                    (sale_id,),
                )
                items = list(cursor.fetchall())
                if not items:
                    raise ValueError("La boleta no tiene productos para devolver al inventario.")

                for item in items:
                    cursor.execute(
                        "UPDATE producto SET stock = stock + %s WHERE id = %s",
                        (item["cantidad"], item["producto_id"]),
                    )
                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            f"No se pudo reponer el stock del producto {item['producto_id']}."
                        )

                cursor.execute("UPDATE venta SET anulada = 1 WHERE id = %s", (sale_id,))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        self._connection_runner(modify)

    def product_stats(self) -> list[dict[str, Any]]:
        def select(connection: MySQLConnection) -> list[dict[str, Any]]:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT producto_id AS product_id,
                           MAX(codigo_producto) AS codigo_producto,
                           MAX(nombre_producto) AS nombre_producto,
                           SUM(cantidad) AS unidades_vendidas,
                           SUM(subtotal) AS ingresos
                    FROM detalle_venta
                    INNER JOIN venta ON venta.id = detalle_venta.venta_id
                    WHERE venta.anulada = 0
                    GROUP BY producto_id
                    ORDER BY unidades_vendidas DESC, codigo_producto
                    """
                )
                return list(cursor.fetchall())
            finally:
                cursor.close()

        return list(self._connection_runner(select))

    def category_stats(self) -> list[dict[str, Any]]:
        def select(connection: MySQLConnection) -> list[dict[str, Any]]:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT detalle_venta.categoria_producto AS categoria,
                           SUM(detalle_venta.cantidad) AS unidades_vendidas
                    FROM detalle_venta
                    INNER JOIN venta ON venta.id = detalle_venta.venta_id
                    WHERE venta.anulada = 0
                    GROUP BY detalle_venta.categoria_producto
                    ORDER BY unidades_vendidas DESC, categoria
                    """
                )
                rows = list(cursor.fetchall())
                total_units = sum(int(row["unidades_vendidas"]) for row in rows)
                return [
                    {
                        **row,
                        "porcentaje": (
                            Decimal(int(row["unidades_vendidas"])) * 100 / total_units
                        ).quantize(Decimal("0.01")),
                    }
                    for row in rows
                ] if total_units else []
            finally:
                cursor.close()

        return list(self._connection_runner(select))

    def price_stats(self) -> list[dict[str, Any]]:
        def select(connection: MySQLConnection) -> list[dict[str, Any]]:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT detalle_venta.precio_unitario,
                           SUM(detalle_venta.cantidad) AS unidades_vendidas
                    FROM detalle_venta
                    INNER JOIN venta ON venta.id = detalle_venta.venta_id
                    WHERE venta.anulada = 0
                    GROUP BY detalle_venta.precio_unitario
                    ORDER BY unidades_vendidas DESC, detalle_venta.precio_unitario
                    """
                )
                return list(cursor.fetchall())
            finally:
                cursor.close()

        return list(self._connection_runner(select))
