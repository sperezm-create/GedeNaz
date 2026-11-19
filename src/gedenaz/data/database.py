"""Conexion y ciclo de vida de conexiones MySQL."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import mysql.connector
from mysql.connector import MySQLConnection

from gedenaz.config import PROJECT_ROOT, DBConfig, get_db_config


def _mysql_offset(iana_zone: str) -> str:
    """Desfase UTC vigente ahora en `iana_zone`, en formato MySQL ('-03:00').

    Se usa un desfase numerico y no el nombre de la zona porque un nombre exige
    que el servidor tenga cargadas las tablas de zonas horarias.
    """
    raw = datetime.now(ZoneInfo(iana_zone)).strftime("%z")  # ej. '-0300'
    return f"{raw[:3]}:{raw[3:]}"


def _resolve_ca_path(ssl_ca: str) -> str:
    """Resuelve rutas relativas contra la raiz del proyecto, no contra el cwd."""
    ca_path = Path(ssl_ca)
    if not ca_path.is_absolute():
        ca_path = PROJECT_ROOT / ca_path
    return str(ca_path)


def create_connection(config: DBConfig | None = None) -> MySQLConnection:
    db_config = config or get_db_config()
    connection_options = {
        "host": db_config.host,
        "port": db_config.port,
        "user": db_config.user,
        "password": db_config.password,
        "database": db_config.database,
        "time_zone": _mysql_offset(db_config.time_zone),
    }
    if db_config.ssl_ca:
        connection_options.update(
            ssl_ca=_resolve_ca_path(db_config.ssl_ca),
            ssl_verify_cert=True,
        )
        if db_config.ssl_verify_identity:
            connection_options["ssl_verify_identity"] = True
    return mysql.connector.connect(**connection_options)


def with_connection(operation: Callable[[MySQLConnection], object]) -> object:
    connection = create_connection()
    try:
        return operation(connection)
    finally:
        connection.close()
