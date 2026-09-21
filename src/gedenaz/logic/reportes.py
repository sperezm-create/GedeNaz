"""Reglas de negocio de los reportes (RF3.1 -- ver
docs/specs/01-requisitos-funcionales.md). Valida los parametros y delega la
consulta en data/reportes.py.
"""

from gedenaz.data import reportes as reportes_repo
from gedenaz.logic.errores import ValidationError
from gedenaz.logic.filtros import a_entero, parsear_rango_fechas

ORDENES_VALIDOS = ("unidades", "ingresos")
LIMITE_POR_DEFECTO = 10
LIMITE_MAXIMO = 100


def productos_mas_vendidos(
    desde: str | None = None,
    hasta: str | None = None,
    limite: str | int | None = None,
    orden: str | None = None,
) -> list[dict]:
    """RF3.1: ranking de productos mas vendidos (el primero es el mas
    vendido). Lanza ValidationError, reportando todos los parametros
    invalidos a la vez."""
    errores: dict[str, str] = {}

    inicio = fin_exclusivo = None
    try:
        inicio, fin_exclusivo = parsear_rango_fechas(desde, hasta)
    except ValidationError as exc:
        errores.update(exc.errores)

    orden_normalizado = (orden or "unidades").strip().lower()
    if orden_normalizado not in ORDENES_VALIDOS:
        errores["orden"] = "Debe ser 'unidades' o 'ingresos'."

    if limite is None or limite == "":
        limite_normalizado = LIMITE_POR_DEFECTO
    else:
        limite_normalizado = a_entero(limite)
        if limite_normalizado is None or not 1 <= limite_normalizado <= LIMITE_MAXIMO:
            errores["limite"] = f"Debe ser un entero entre 1 y {LIMITE_MAXIMO}."

    if errores:
        raise ValidationError(errores)

    return reportes_repo.productos_mas_vendidos(
        inicio, fin_exclusivo, limite_normalizado, orden_normalizado
    )
