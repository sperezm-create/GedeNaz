"""Casos de uso y validaciones de ventas."""

from decimal import Decimal, InvalidOperation
from typing import Any

from gedenaz.data.sales_repository import InMemorySalesRepository, SalesRepository
from gedenaz.installments import FREQUENCIES, MAX_INSTALLMENTS, parse_first_due_date

SALE_RECIPIENTS = ("Hombre", "Mujer", "No especificado")


class SalesService:
    def __init__(
        self,
        repository: SalesRepository | InMemorySalesRepository | None = None,
    ) -> None:
        self.repository = repository or SalesRepository()

    def create_sale(
        self,
        items: list[dict[str, Any]],
        payment_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not items:
            raise ValueError("Agrega al menos un producto antes de confirmar la venta.")

        quantities: dict[tuple[int, str], int] = {}
        for item in items:
            try:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Cada producto debe tener un identificador y una cantidad entera.") from exc
            if isinstance(item.get("product_id"), bool) or product_id <= 0 or quantity <= 0:
                raise ValueError("El producto y la cantidad deben ser valores positivos.")
            if isinstance(item.get("quantity"), bool) or str(item["quantity"]).strip() != str(quantity):
                raise ValueError("La cantidad debe ser un número entero positivo.")
            recipient = str(item.get("genero_destino", "No especificado")).strip()
            if recipient not in SALE_RECIPIENTS:
                raise ValueError("El destinatario debe ser Hombre o Mujer.")
            key = (product_id, recipient)
            quantities[key] = quantities.get(key, 0) + quantity

        requested_items = [
            {"product_id": product_id, "quantity": quantity, "genero_destino": recipient}
            for (product_id, recipient), quantity in quantities.items()
        ]
        normalized_plan = None
        if payment_plan is not None:
            try:
                count = int(payment_plan["cantidad_cuotas"])
                frequency = str(payment_plan["frecuencia"]).strip()
                first_due_date = parse_first_due_date(payment_plan["primer_vencimiento"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    "Completa un número de cuotas y una fecha de primer vencimiento válida."
                ) from exc
            if (
                isinstance(payment_plan.get("cantidad_cuotas"), bool)
                or not 2 <= count <= MAX_INSTALLMENTS
            ):
                raise ValueError(f"El plan debe tener entre 2 y {MAX_INSTALLMENTS} cuotas.")
            if str(payment_plan["cantidad_cuotas"]).strip() != str(count):
                raise ValueError("La cantidad de cuotas debe ser un número entero.")
            if frequency not in FREQUENCIES:
                raise ValueError("Selecciona una frecuencia semanal, quincenal o mensual.")
            normalized_plan = {
                "cantidad_cuotas": count,
                "frecuencia": frequency,
                "primer_vencimiento": first_due_date,
            }
        return self.repository.create_sale(requested_items, normalized_plan)

    def list_sales(self) -> list[dict[str, Any]]:
        return self.repository.list_sales()

    def cancel_sale(self, sale_id: int) -> None:
        if isinstance(sale_id, bool) or sale_id <= 0:
            raise ValueError("El identificador de la boleta no es válido.")
        self.repository.cancel_sale(sale_id)

    def add_payment(
        self,
        sale_id: int,
        installment_number: int,
        amount: Decimal | str | int,
    ) -> dict[str, Any]:
        if isinstance(sale_id, bool) or sale_id <= 0:
            raise ValueError("El identificador de la venta no es válido.")
        if isinstance(installment_number, bool) or installment_number <= 0:
            raise ValueError("Selecciona una cuota válida.")
        try:
            payment_amount = Decimal(str(amount).strip())
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("El monto del abono debe ser numérico.") from exc
        if not payment_amount.is_finite() or payment_amount <= 0:
            raise ValueError("El monto del abono debe ser mayor que cero.")
        try:
            rounded_amount = payment_amount.quantize(Decimal("0.01"))
        except InvalidOperation as exc:
            raise ValueError("El monto del abono está fuera del rango permitido.") from exc
        if payment_amount != rounded_amount:
            raise ValueError("El monto del abono admite como máximo dos decimales.")
        return self.repository.add_payment(sale_id, installment_number, payment_amount)

    def get_payment_plan(self, sale_id: int) -> dict[str, Any] | None:
        return self.repository.get_payment_plan(sale_id)

    def product_stats(self) -> list[dict[str, Any]]:
        return self.repository.product_stats()

    def category_stats(self) -> list[dict[str, Any]]:
        return self.repository.category_stats()

    def price_stats(self) -> list[dict[str, Any]]:
        return self.repository.price_stats()
