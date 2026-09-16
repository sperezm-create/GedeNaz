"""Reglas de negocio de la entidad Producto (RF1 -- ver
docs/specs/01-requisitos-funcionales.md). No importa nada de flask ni de
mysql.connector: se puede probar con pytest sin servidor HTTP ni base de
datos.
"""

from gedenaz.data import productos as productos_repo


class ValidationError(Exception):
    """Se lanza cuando los datos de un producto no cumplen RF1.

    `errores` es un dict {campo: mensaje}, pensado para devolverse tal
    cual como JSON en la respuesta 400 de la API.
    """

    def __init__(self, errores: dict[str, str]):
        self.errores = errores
        super().__init__(str(errores))


def validar_producto(datos: dict) -> None:
    errores: dict[str, str] = {}

    nombre = datos.get("nombre")
    if not nombre or not str(nombre).strip():
        errores["nombre"] = "El nombre es obligatorio."

    categoria = datos.get("categoria")
    if not categoria or not str(categoria).strip():
        errores["categoria"] = "La categoria es obligatoria."

    precio = datos.get("precio")
    if precio is None or precio == "":
        errores["precio"] = "El precio es obligatorio."
    else:
        try:
            if float(precio) <= 0:
                errores["precio"] = "El precio debe ser mayor que 0."
        except (TypeError, ValueError):
            errores["precio"] = "El precio debe ser un numero."

    stock = datos.get("stock")
    if stock is None or stock == "":
        errores["stock"] = "El stock es obligatorio."
    else:
        try:
            if int(stock) < 0:
                errores["stock"] = "El stock no puede ser negativo."
        except (TypeError, ValueError):
            errores["stock"] = "El stock debe ser un numero entero."

    if errores:
        raise ValidationError(errores)


def crear_producto(datos: dict) -> dict:
    """Valida `datos` (RF1) y, si son validos, los guarda. Devuelve el
    producto creado (con id y timestamps) o lanza ValidationError."""
    validar_producto(datos)

    return productos_repo.crear_producto(
        nombre=str(datos["nombre"]).strip(),
        categoria=str(datos["categoria"]).strip(),
        precio=float(datos["precio"]),
        stock=int(datos["stock"]),
    )
