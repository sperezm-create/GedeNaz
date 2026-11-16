"""Helpers for building interest-free installment schedules."""

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Any


FREQUENCIES = ("Semanal", "Quincenal", "Mensual")
MAX_INSTALLMENTS = 120


def parse_first_due_date(value: date | str) -> date:
    if isinstance(value, datetime):
        raise ValueError("La fecha del primer vencimiento debe ser una fecha, no una fecha con hora.")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("La fecha del primer vencimiento debe tener formato AAAA-MM-DD.") from exc


def build_installment_schedule(
    total: Decimal,
    count: int,
    frequency: str,
    first_due_date: date | str,
) -> list[dict[str, Any]]:
    if not 2 <= count <= MAX_INSTALLMENTS:
        raise ValueError(f"El plan debe tener entre 2 y {MAX_INSTALLMENTS} cuotas.")
    if frequency not in FREQUENCIES:
        raise ValueError("La frecuencia debe ser Semanal, Quincenal o Mensual.")

    start_date = parse_first_due_date(first_due_date)
    base_amount = (total / count).quantize(Decimal("1"), rounding=ROUND_DOWN)
    schedule = []
    for index in range(count):
        due_date = _due_date(start_date, frequency, index)
        amount = base_amount if index < count - 1 else total - base_amount * (count - 1)
        if amount <= 0:
            raise ValueError("El monto total no alcanza para generar cuotas positivas.")
        schedule.append(
            {
                "numero": index + 1,
                "monto": amount,
                "fecha_vencimiento": due_date,
                "pagado": Decimal("0"),
                "saldo": amount,
                "estado": "Pendiente",
                "abonos": [],
            }
        )
    return schedule


def _due_date(first_due_date: date, frequency: str, offset: int) -> date:
    if frequency == "Semanal":
        return first_due_date + timedelta(days=7 * offset)
    if frequency == "Quincenal":
        return first_due_date + timedelta(days=15 * offset)

    month_index = first_due_date.month - 1 + offset
    year = first_due_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(first_due_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
