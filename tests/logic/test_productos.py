"""Pruebas de las reglas de negocio de RF1 (Crear producto).

No tocan Flask ni MySQL -- corren siempre, sin necesitar .env ni base
de datos configurada.
"""

import pytest

from gedenaz.logic.productos import ValidationError, validar_producto


def test_producto_valido_no_lanza_error():
    validar_producto(
        {"nombre": "Anillo de oro", "categoria": "anillo", "precio": 15000, "stock": 3}
    )


def test_nombre_obligatorio():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"categoria": "anillo", "precio": 100, "stock": 1})
    assert "nombre" in exc.value.errores


def test_categoria_obligatoria():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "precio": 100, "stock": 1})
    assert "categoria" in exc.value.errores


def test_precio_obligatorio():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "categoria": "anillo", "stock": 1})
    assert "precio" in exc.value.errores


def test_precio_debe_ser_mayor_a_cero():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "categoria": "anillo", "precio": 0, "stock": 1})
    assert "precio" in exc.value.errores


def test_precio_negativo_invalido():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "categoria": "anillo", "precio": -10, "stock": 1})
    assert "precio" in exc.value.errores


def test_precio_no_numerico_invalido():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "categoria": "anillo", "precio": "gratis", "stock": 1})
    assert "precio" in exc.value.errores


def test_stock_obligatorio():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "categoria": "anillo", "precio": 100})
    assert "stock" in exc.value.errores


def test_stock_no_puede_ser_negativo():
    with pytest.raises(ValidationError) as exc:
        validar_producto({"nombre": "Anillo", "categoria": "anillo", "precio": 100, "stock": -1})
    assert "stock" in exc.value.errores


def test_stock_cero_es_valido():
    validar_producto({"nombre": "Anillo", "categoria": "anillo", "precio": 100, "stock": 0})


def test_reporta_todos_los_campos_faltantes_a_la_vez():
    with pytest.raises(ValidationError) as exc:
        validar_producto({})
    assert set(exc.value.errores) == {"nombre", "categoria", "precio", "stock"}
