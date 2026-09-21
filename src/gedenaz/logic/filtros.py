"""Parseo de entradas (enteros, filtros de fecha) compartido por ventas y
reportes."""

from datetime import datetime, timedelta

from gedenaz.logic.errores import ValidationError


def a_entero(valor) -> int | None:
    """Convierte a int solo si es un entero "de verdad": un int, un float
    sin decimales (3.0) o un string numerico ("3"). Devuelve None para
    todo lo demas -- incluidos bool (True no es un 1 valido), None, 3.5 y
    texto no numerico."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        try:
            return int(valor.strip())
        except ValueError:
            return None
    return None


def _parsear_dia(valor: str, campo: str, errores: dict[str, str]) -> datetime | None:
    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d")
    except ValueError:
        errores[campo] = "Formato invalido, usa YYYY-MM-DD (ej. 2026-09-20)."
        return None


def parsear_rango_fechas(
    desde: str | None, hasta: str | None
) -> tuple[datetime | None, datetime | None]:
    """Convierte los filtros `desde` / `hasta` (YYYY-MM-DD, ambos
    inclusive) en `(inicio, fin_exclusivo)`.

    `inicio` es las 00:00 de `desde`; `fin_exclusivo` es las 00:00 del dia
    SIGUIENTE a `hasta`, asi `hasta=2026-09-20` incluye todo ese dia. Un
    filtro ausente (o vacio) queda en None = sin limite. Lanza
    ValidationError si un formato es invalido o `desde` > `hasta`.
    """
    errores: dict[str, str] = {}
    inicio = fin_exclusivo = None

    if desde:
        inicio = _parsear_dia(desde, "desde", errores)
    if hasta:
        dia_hasta = _parsear_dia(hasta, "hasta", errores)
        if dia_hasta is not None:
            fin_exclusivo = dia_hasta + timedelta(days=1)

    if not errores and inicio is not None and fin_exclusivo is not None:
        if inicio >= fin_exclusivo:
            errores["desde"] = "'desde' no puede ser posterior a 'hasta'."

    if errores:
        raise ValidationError(errores)

    return inicio, fin_exclusivo
