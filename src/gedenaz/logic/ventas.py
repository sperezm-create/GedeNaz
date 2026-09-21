"""Reglas de negocio de las ventas (RF5 -- ver
docs/specs/01-requisitos-funcionales.md). No importa nada de flask ni de
mysql.connector: la validacion se prueba con pytest sin servidor ni base.
"""

from gedenaz.data import ventas as ventas_repo
from gedenaz.logic.errores import ConflictError, NotFoundError, ValidationError
from gedenaz.logic.filtros import a_entero, parsear_rango_fechas


def validar_venta(datos: dict) -> list[tuple[int, int]]:
    """Valida el cuerpo de POST /ventas y devuelve las lineas ya
    normalizadas `[(producto_id, cantidad), ...]`.

    Lanza ValidationError con una entrada por cada problema, nombrando la
    linea (`items[2].cantidad`). Que el producto exista y alcance el stock
    lo comprueba la capa de datos, dentro de la transaccion.
    """
    items = datos.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError({"items": "Debes enviar al menos un producto en 'items'."})

    errores: dict[str, str] = {}
    lineas: list[tuple[int, int]] = []
    primera_aparicion: dict[int, int] = {}

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errores[f"items[{i}]"] = "Cada linea debe ser un objeto con 'producto_id' y 'cantidad'."
            continue

        producto_id = a_entero(item.get("producto_id"))
        cantidad = a_entero(item.get("cantidad"))
        linea_valida = True

        if producto_id is None or producto_id < 1:
            errores[f"items[{i}].producto_id"] = (
                "El producto_id es obligatorio y debe ser un entero positivo."
            )
            linea_valida = False
        elif producto_id in primera_aparicion:
            errores[f"items[{i}].producto_id"] = (
                f"Producto repetido (ya esta en items[{primera_aparicion[producto_id]}])."
            )
            linea_valida = False
        else:
            primera_aparicion[producto_id] = i

        if cantidad is None or cantidad < 1:
            errores[f"items[{i}].cantidad"] = (
                "La cantidad es obligatoria y debe ser un entero mayor o igual a 1."
            )
            linea_valida = False

        if linea_valida:
            lineas.append((producto_id, cantidad))

    if errores:
        raise ValidationError(errores)

    return lineas


def registrar_venta(datos: dict) -> dict:
    """RF5: valida `datos` y registra la venta (cabecera + lineas +
    descuento de stock, todo o nada). Lanza ValidationError (datos
    invalidos o producto inexistente) o ConflictError (stock
    insuficiente)."""
    lineas = validar_venta(datos)

    try:
        return ventas_repo.registrar_venta(lineas)
    except ventas_repo.ProductoNoDisponibleError as exc:
        raise ValidationError(
            {f"items[{exc.indice}].producto_id": f"No existe un producto activo con id {exc.producto_id}."}
        ) from exc
    except ventas_repo.StockInsuficienteError as exc:
        raise ConflictError(
            f"No hay stock suficiente de '{exc.nombre}'.",
            campos={
                f"items[{exc.indice}].cantidad": (
                    f"Stock insuficiente: disponible {exc.disponible}, solicitado {exc.solicitado}."
                )
            },
        ) from exc


def obtener_venta(id_: int) -> dict:
    """RF5: detalle de una venta. Lanza NotFoundError si no existe."""
    venta = ventas_repo.obtener_venta(id_)
    if venta is None:
        raise NotFoundError(f"No existe una venta con id {id_}.")
    return venta


def listar_ventas(desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """RF5: ventas de la mas reciente a la mas antigua, opcionalmente
    dentro de un rango de dias (YYYY-MM-DD, ambos inclusive). Lanza
    ValidationError si el rango es invalido."""
    inicio, fin_exclusivo = parsear_rango_fechas(desde, hasta)
    return ventas_repo.listar_ventas(inicio, fin_exclusivo)
