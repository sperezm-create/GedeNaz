"""Endpoints HTTP de las ventas (RF5 -- ver docs/specs/06-referencia-api.md).
Solo traduce HTTP <-> Python: llama a logic/ventas.py y devuelve JSON, sin
SQL ni reglas de negocio propias. No hay PUT/PATCH/DELETE: las ventas son
inmutables en esta version.
"""

from flask import Blueprint, jsonify, request

from gedenaz.api.respuestas import error_json
from gedenaz.logic.errores import ConflictError, NotFoundError, ValidationError
from gedenaz.logic.ventas import listar_ventas, obtener_venta, registrar_venta

ventas_bp = Blueprint("ventas", __name__)


@ventas_bp.post("/ventas")
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        venta = registrar_venta(datos)
    except ValidationError as exc:
        return error_json("Los datos enviados no son validos.", campos=exc.errores)
    except ConflictError as exc:
        return error_json(exc.mensaje, campos=exc.campos, status=409)
    return jsonify(venta), 201


@ventas_bp.get("/ventas")
def listar():
    try:
        ventas = listar_ventas(
            desde=request.args.get("desde"), hasta=request.args.get("hasta")
        )
    except ValidationError as exc:
        return error_json("Los filtros enviados no son validos.", campos=exc.errores)
    return jsonify(ventas), 200


@ventas_bp.get("/ventas/<int:id_>")
def detalle(id_: int):
    try:
        venta = obtener_venta(id_)
    except NotFoundError as exc:
        return error_json(str(exc), status=404)
    return jsonify(venta), 200
