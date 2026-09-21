"""Pruebas de las reglas de negocio de RF5 (validacion de una venta).

No tocan Flask ni MySQL -- corren siempre, sin necesitar .env.
"""

import pytest

from gedenaz.logic.errores import ValidationError
from gedenaz.logic.ventas import registrar_venta, validar_venta


def test_venta_valida_devuelve_las_lineas_normalizadas():
    lineas = validar_venta(
        {"items": [{"producto_id": 38, "cantidad": 2}, {"producto_id": 41, "cantidad": 1}]}
    )
    assert lineas == [(38, 2), (41, 1)]


def test_acepta_numeros_como_texto_o_float_entero():
    assert validar_venta({"items": [{"producto_id": "38", "cantidad": 2.0}]}) == [(38, 2)]


@pytest.mark.parametrize("cuerpo", [{}, {"items": []}, {"items": None}, {"items": "x"}, {"items": {}}])
def test_items_obligatorio_y_no_vacio(cuerpo):
    with pytest.raises(ValidationError) as exc:
        validar_venta(cuerpo)
    assert set(exc.value.errores) == {"items"}


def test_cada_linea_debe_ser_un_objeto():
    with pytest.raises(ValidationError) as exc:
        validar_venta({"items": [5]})
    assert "items[0]" in exc.value.errores


@pytest.mark.parametrize("producto_id", [None, 0, -1, True, "abc", 1.5])
def test_producto_id_invalido(producto_id):
    with pytest.raises(ValidationError) as exc:
        validar_venta({"items": [{"producto_id": producto_id, "cantidad": 1}]})
    assert "items[0].producto_id" in exc.value.errores


@pytest.mark.parametrize("cantidad", [None, 0, -1, True, "abc", 1.5])
def test_cantidad_invalida(cantidad):
    with pytest.raises(ValidationError) as exc:
        validar_venta({"items": [{"producto_id": 1, "cantidad": cantidad}]})
    assert "items[0].cantidad" in exc.value.errores


def test_producto_repetido_en_dos_lineas_es_error():
    with pytest.raises(ValidationError) as exc:
        validar_venta(
            {"items": [{"producto_id": 5, "cantidad": 1}, {"producto_id": 5, "cantidad": 2}]}
        )
    assert "items[1].producto_id" in exc.value.errores
    assert "items[0]" in exc.value.errores["items[1].producto_id"]


def test_reporta_todos_los_problemas_a_la_vez_nombrando_la_linea():
    with pytest.raises(ValidationError) as exc:
        validar_venta(
            {
                "items": [
                    {"producto_id": 1, "cantidad": 1},
                    {"producto_id": 2, "cantidad": 0},
                    {"cantidad": 3},
                ]
            }
        )
    assert set(exc.value.errores) == {"items[1].cantidad", "items[2].producto_id"}


def test_registrar_venta_valida_antes_de_tocar_la_base():
    """La validacion corre antes de abrir ninguna conexion, asi que este
    test no necesita .env ni MySQL."""
    with pytest.raises(ValidationError):
        registrar_venta({"items": []})
