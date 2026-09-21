"""Conexion y ciclo de vida de conexiones MySQL."""

from collections.abc import Callable

import mysql.connector
from mysql.connector import MySQLConnection

from gedenaz.config import DBConfig, get_db_config


def create_connection(config: DBConfig | None = None) -> MySQLConnection:
    db_config = config or get_db_config()
    return mysql.connector.connect(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        database=db_config.database,
    )


def with_connection(operation: Callable[[MySQLConnection], object]) -> object:
    connection = create_connection()
    try:
        return operation(connection)
    finally:
        connection.close()
