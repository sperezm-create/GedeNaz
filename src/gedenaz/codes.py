"""Códigos visibles y estables para productos y boletas."""


def product_code(product_id: int) -> str:
    return f"GN-{int(product_id):06d}"


def receipt_code(sale_id: int) -> str:
    return f"BOL-{int(sale_id):06d}"
