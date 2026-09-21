"""Helpers de respuesta HTTP compartidos por los blueprints de api/."""

from flask import jsonify


def error_json(mensaje: str, campos: dict[str, str] | None = None, status: int = 400):
    """Sobre unico para toda respuesta de error -- ver
    docs/specs/06-referencia-api.md. `campos` va en errores de validacion
    (400) y de conflicto de stock (409), y es None en el resto (ej. 404)."""
    return jsonify(error={"mensaje": mensaje, "campos": campos}), status
