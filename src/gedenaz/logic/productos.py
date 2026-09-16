"""Reglas de negocio de la entidad Producto (RF1-RF4 -- ver
docs/specs/01-requisitos-funcionales.md). No importa nada de flask ni de
mysql.connector: se puede probar con pytest sin servidor HTTP ni base de
datos.
"""

from gedenaz.data import productos as productos_repo


class ValidationError(Exception):
    """Se lanza cuando los datos de un producto no cumplen RF1/RF3.

    `errores` es un dict {campo: mensaje}, pensado para devolverse tal
    cual como JSON en la respuesta 400 de la API.
    """

    def __init__(self, errores: dict[str, str]):
        self.errores = errores
        super().__init__(str(errores))


class NotFoundError(Exception):
    """Se lanza cuando se pide un producto (por id) que no existe o ya
    esta dado de baja -- la API lo traduce a un 404."""


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


def listar_productos(nombre: str | None = None, categoria: str | None = None) -> list[dict]:
    """RF2: lista productos activos, opcionalmente filtrados por nombre
    y/o categoria."""
    nombre = nombre.strip() if nombre else None
    categoria = categoria.strip() if categoria else None
    return productos_repo.listar_productos(nombre=nombre, categoria=categoria)


def obtener_producto(id_: int) -> dict:
    """RF2: detalle de un producto. Lanza NotFoundError si no existe."""
    producto = productos_repo.obtener_producto(id_)
    if producto is None:
        raise NotFoundError(f"No existe un producto activo con id {id_}.")
    return producto


def actualizar_producto(id_: int, datos: dict) -> dict:
    """RF3: valida `datos` (mismas reglas que RF1) y actualiza el
    producto. Lanza ValidationError o NotFoundError segun corresponda."""
    validar_producto(datos)

    producto = productos_repo.actualizar_producto(
        id_,
        nombre=str(datos["nombre"]).strip(),
        categoria=str(datos["categoria"]).strip(),
        precio=float(datos["precio"]),
        stock=int(datos["stock"]),
    )
    if producto is None:
        raise NotFoundError(f"No existe un producto activo con id {id_}.")
    return producto


def eliminar_producto(id_: int) -> None:
    """RF4: da de baja (baja logica) un producto. Lanza NotFoundError si
    no existia. La confirmacion antes de eliminar es responsabilidad de
    la UI (ver docs/specs/01-requisitos-funcionales.md RF4)."""
    if not productos_repo.eliminar_producto(id_):
        raise NotFoundError(f"No existe un producto activo con id {id_}.")
