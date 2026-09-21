"""Excepciones de negocio compartidas por logic/productos.py,
logic/ventas.py y logic/reportes.py. La capa api/ las traduce a codigos
HTTP (ver docs/specs/06-referencia-api.md); aca no se importa nada de flask.
"""


class ValidationError(Exception):
    """Los datos recibidos no cumplen las reglas -> 400.

    `errores` es un dict {campo: mensaje}, pensado para devolverse tal
    cual como JSON en la respuesta 400 de la API.
    """

    def __init__(self, errores: dict[str, str]):
        self.errores = errores
        super().__init__(str(errores))


class NotFoundError(Exception):
    """Se pide algo (por id) que no existe o ya esta dado de baja -> 404."""


class ConflictError(Exception):
    """Los datos son validos pero chocan con el estado actual (hoy: stock
    insuficiente al registrar una venta) -> 409.

    `campos` (opcional) indica la linea/campo problematico, igual que en
    ValidationError.
    """

    def __init__(self, mensaje: str, campos: dict[str, str] | None = None):
        self.mensaje = mensaje
        self.campos = campos
        super().__init__(mensaje)
