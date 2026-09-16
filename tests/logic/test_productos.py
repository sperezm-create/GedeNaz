"""Pruebas de las reglas de negocio de RF1/RF3 (validaciones).

No tocan Flask ni MySQL -- corren siempre, sin necesitar .env ni base
de datos configurada.
"""

import pytest

from gedenaz.logic.productos import (
    ValidationError,
    actualizar_producto,
    actualizar_producto_parcial,
    validar_producto,
    validar_producto_parcial,
)


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


def test_actualizar_producto_valida_antes_de_tocar_la_base():
    """La validacion de RF3 corre antes de llamar a la capa de datos, asi
    que este test no necesita .env ni conexion a MySQL."""
    with pytest.raises(ValidationError) as exc:
        actualizar_producto(1, {"nombre": "Anillo", "categoria": "anillo", "precio": 100, "stock": -1})
    assert "stock" in exc.value.errores


# --- validar_producto_parcial (PATCH) ---


def test_parcial_un_solo_campo_valido_no_lanza_error():
    validar_producto_parcial({"stock": 10})


def test_parcial_sin_campos_es_error():
    with pytest.raises(ValidationError) as exc:
        validar_producto_parcial({})
    assert "_general" in exc.value.errores


def test_parcial_ignora_campos_desconocidos():
    with pytest.raises(ValidationError) as exc:
        validar_producto_parcial({"campo_inventado": "x"})
    assert "_general" in exc.value.errores


def test_parcial_solo_valida_los_campos_presentes():
    """Si solo mandas stock, no debe exigir nombre/categoria/precio."""
    validar_producto_parcial({"stock": 0})


def test_parcial_stock_negativo_invalido():
    with pytest.raises(ValidationError) as exc:
        validar_producto_parcial({"stock": -1})
    assert "stock" in exc.value.errores
    assert "nombre" not in exc.value.errores


def test_parcial_precio_invalido():
    with pytest.raises(ValidationError) as exc:
        validar_producto_parcial({"precio": 0})
    assert "precio" in exc.value.errores


def test_actualizar_producto_parcial_valida_antes_de_tocar_la_base():
    with pytest.raises(ValidationError) as exc:
        actualizar_producto_parcial(1, {"stock": -1})
    assert "stock" in exc.value.errores
