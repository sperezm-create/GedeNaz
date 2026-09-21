"""Pruebas de los helpers de entrada (enteros y rango de fechas).

No tocan Flask ni MySQL -- corren siempre, sin necesitar .env.
"""

from datetime import datetime

import pytest

from gedenaz.logic.errores import ValidationError
from gedenaz.logic.filtros import a_entero, parsear_rango_fechas


@pytest.mark.parametrize(
    "valor, esperado",
    [(3, 3), (0, 0), (-2, -2), (3.0, 3), ("7", 7), (" 7 ", 7)],
)
def test_a_entero_acepta_enteros_de_verdad(valor, esperado):
    assert a_entero(valor) == esperado


@pytest.mark.parametrize("valor", [None, True, False, 3.5, "abc", "3.5", "", [], {}])
def test_a_entero_rechaza_todo_lo_demas(valor):
    assert a_entero(valor) is None


def test_rango_sin_filtros_no_limita():
    assert parsear_rango_fechas(None, None) == (None, None)
    assert parsear_rango_fechas("", "") == (None, None)


def test_rango_hasta_es_inclusivo_termina_a_las_00_del_dia_siguiente():
    inicio, fin = parsear_rango_fechas("2026-09-01", "2026-09-30")
    assert inicio == datetime(2026, 9, 1, 0, 0)
    assert fin == datetime(2026, 10, 1, 0, 0)


def test_rango_de_un_solo_dia_es_valido():
    inicio, fin = parsear_rango_fechas("2026-09-20", "2026-09-20")
    assert inicio == datetime(2026, 9, 20)
    assert fin == datetime(2026, 9, 21)


def test_rango_con_un_solo_extremo():
    assert parsear_rango_fechas("2026-09-01", None) == (datetime(2026, 9, 1), None)
    assert parsear_rango_fechas(None, "2026-09-01") == (None, datetime(2026, 9, 2))


def test_rango_con_formato_invalido_reporta_cada_campo():
    with pytest.raises(ValidationError) as exc:
        parsear_rango_fechas("20-09-2026", "manana")
    assert set(exc.value.errores) == {"desde", "hasta"}


def test_rango_con_desde_posterior_a_hasta_es_error():
    with pytest.raises(ValidationError) as exc:
        parsear_rango_fechas("2026-09-30", "2026-09-01")
    assert "desde" in exc.value.errores
