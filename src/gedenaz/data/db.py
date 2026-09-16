"""Capa de conexion a MySQL.

Expone get_connection() / connection_scope(), usando la configuracion de
.env (ver config.py). Las funciones tipo repositorio (crear_producto,
listar_productos, actualizar_producto, eliminar_producto -- ver
docs/specs/03-arquitectura.md) se construyen sobre esta conexion a medida
que se implementan RF1-RF4 (Fase 1 en adelante).
"""

from contextlib import contextmanager
from typing import Iterator

import mysql.connector

from gedenaz.config import get_db_config


def get_connection():
    """Abre una conexion nueva a MySQL usando la configuracion de .env."""
    cfg = get_db_config()

    connect_kwargs = dict(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
    )
    if cfg.ssl_ca:
        # Sin ssl_verify_cert=True junto a ssl_ca, mysql-connector rechaza
        # la conexion con "Invalid ssl-mode" -- ver nota en config.py y
        # docs/specs/05-entorno-desarrollo.md (pasa con Aiven).
        connect_kwargs["ssl_ca"] = cfg.ssl_ca
        connect_kwargs["ssl_verify_cert"] = True

    return mysql.connector.connect(**connect_kwargs)


@contextmanager
def connection_scope() -> Iterator["mysql.connector.MySQLConnection"]:
    """Abre una conexion, la entrega, y la cierra al salir del bloque `with`."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
