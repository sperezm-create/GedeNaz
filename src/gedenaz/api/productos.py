"""Endpoints HTTP de la entidad Producto (RF1-RF4 -- ver
docs/specs/01-requisitos-funcionales.md). Solo traduce HTTP <-> Python:
llama a logic/productos.py y devuelve JSON, sin SQL ni reglas de negocio
propias.
"""

from flask import Blueprint, jsonify, request

from gedenaz.api.respuestas import error_json
from gedenaz.logic.errores import NotFoundError, ValidationError
from gedenaz.logic.productos import (
    actualizar_producto,
    actualizar_producto_parcial,
    crear_producto,
    eliminar_producto,
    listar_productos,
    obtener_producto,
)

productos_bp = Blueprint("productos", __name__)


@productos_bp.post("/productos")
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        producto = crear_producto(datos)
    except ValidationError as exc:
        return error_json("Los datos enviados no son validos.", campos=exc.errores)
    return jsonify(producto), 201


@productos_bp.get("/productos")
def listar():
    nombre = request.args.get("nombre")
    categoria = request.args.get("categoria")
    productos = listar_productos(nombre=nombre, categoria=categoria)
    return jsonify(productos), 200


@productos_bp.get("/productos/<int:id_>")
def detalle(id_: int):
    try:
        producto = obtener_producto(id_)
    except NotFoundError as exc:
        return error_json(str(exc), status=404)
    return jsonify(producto), 200


@productos_bp.put("/productos/<int:id_>")
def actualizar(id_: int):
    datos = request.get_json(silent=True) or {}
    try:
        producto = actualizar_producto(id_, datos)
    except ValidationError as exc:
        return error_json("Los datos enviados no son validos.", campos=exc.errores)
    except NotFoundError as exc:
        return error_json(str(exc), status=404)
    return jsonify(producto), 200


@productos_bp.patch("/productos/<int:id_>")
def actualizar_parcial(id_: int):
    datos = request.get_json(silent=True) or {}
    try:
        producto = actualizar_producto_parcial(id_, datos)
    except ValidationError as exc:
        return error_json("Los datos enviados no son validos.", campos=exc.errores)
    except NotFoundError as exc:
        return error_json(str(exc), status=404)
    return jsonify(producto), 200


@productos_bp.delete("/productos/<int:id_>")
def eliminar(id_: int):
    try:
        eliminar_producto(id_)
    except NotFoundError as exc:
        return error_json(str(exc), status=404)
    return "", 204
