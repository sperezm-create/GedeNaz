"""Pruebas de la validacion de parametros del reporte de RF3.1.

Solo casos que se rechazan ANTES de consultar la base, asi que no
necesitan .env ni MySQL. El ranking en si se prueba en tests/data/.
"""

import pytest

from gedenaz.logic.errores import ValidationError
from gedenaz.logic.reportes import productos_mas_vendidos


@pytest.mark.parametrize("orden", ["ganancia", "x", "unidades,ingresos"])
def test_orden_desconocido(orden):
    with pytest.raises(ValidationError) as exc:
        productos_mas_vendidos(orden=orden)
    assert set(exc.value.errores) == {"orden"}


@pytest.mark.parametrize("limite", ["0", "-1", "101", "abc", "1.5", 0, 101])
def test_limite_fuera_de_rango_o_no_entero(limite):
    with pytest.raises(ValidationError) as exc:
        productos_mas_vendidos(limite=limite)
    assert set(exc.value.errores) == {"limite"}


def test_fechas_invalidas():
    with pytest.raises(ValidationError) as exc:
        productos_mas_vendidos(desde="ayer", hasta="2026-13-45")
    assert set(exc.value.errores) == {"desde", "hasta"}


def test_reporta_todos_los_parametros_invalidos_a_la_vez():
    with pytest.raises(ValidationError) as exc:
        productos_mas_vendidos(desde="x", orden="y", limite="z")
    assert set(exc.value.errores) == {"desde", "orden", "limite"}
