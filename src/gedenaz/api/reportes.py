"""Endpoints HTTP de reportes (RF3.1 -- ver docs/specs/06-referencia-api.md).
Solo traduce HTTP <-> Python: llama a logic/reportes.py y devuelve JSON.
"""

from flask import Blueprint, jsonify, request

from gedenaz.api.respuestas import error_json
from gedenaz.logic.errores import ValidationError
from gedenaz.logic.reportes import productos_mas_vendidos

reportes_bp = Blueprint("reportes", __name__)


@reportes_bp.get("/reportes/productos-mas-vendidos")
def mas_vendidos():
    try:
        ranking = productos_mas_vendidos(
            desde=request.args.get("desde"),
            hasta=request.args.get("hasta"),
            limite=request.args.get("limite"),
            orden=request.args.get("orden"),
        )
    except ValidationError as exc:
        return error_json("Los filtros enviados no son validos.", campos=exc.errores)
    return jsonify(ranking), 200
