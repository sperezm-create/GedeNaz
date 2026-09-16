"""Endpoints HTTP de la entidad Producto (RF1 -- ver
docs/specs/01-requisitos-funcionales.md). Solo traduce HTTP <-> Python:
llama a logic/productos.py y devuelve JSON, sin SQL ni reglas de negocio
propias.
"""

from flask import Blueprint, jsonify, request

from gedenaz.logic.productos import ValidationError, crear_producto

productos_bp = Blueprint("productos", __name__)


@productos_bp.post("/productos")
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        producto = crear_producto(datos)
    except ValidationError as exc:
        return jsonify(errores=exc.errores), 400
    return jsonify(producto), 201
