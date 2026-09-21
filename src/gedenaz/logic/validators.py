"""Validaciones de negocio para productos."""

from decimal import Decimal, InvalidOperation


def validate_product(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Los datos del producto son inválidos.")

    nombre = str(data.get("nombre", "")).strip()
    categoria = str(data.get("categoria", "")).strip()

    if not nombre:
        raise ValueError("El nombre del producto es obligatorio.")
    if not categoria:
        raise ValueError("La categoría es obligatoria.")

    try:
        precio = Decimal(str(data.get("precio", "0")))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("El precio del producto es inválido.")

    try:
        stock = int(data.get("stock", "0"))
    except (TypeError, ValueError):
        raise ValueError("El stock debe ser un número entero.")

    if precio <= 0:
        raise ValueError("El precio debe ser mayor que cero.")
    if stock < 0:
        raise ValueError("El stock no puede ser negativo.")

    return {
        "nombre": nombre,
        "categoria": categoria.lower(),
        "precio": precio,
        "stock": stock,
    }
