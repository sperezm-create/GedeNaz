"""Capa de conexion a MySQL.

Expone get_connection() / connection_scope(), usando la configuracion de
.env (ver config.py). Las funciones tipo repositorio (data/productos.py,
data/ventas.py, data/reportes.py -- ver docs/specs/03-arquitectura.md) se
construyen sobre esta conexion.
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Iterator
from zoneinfo import ZoneInfo

import mysql.connector

from gedenaz.config import get_db_config


def _desfase_mysql(zona_iana: str) -> str:
    """Desfase UTC vigente AHORA en `zona_iana`, en el formato numerico que
    entiende MySQL ('-03:00'). Se usa un desfase numerico y no el nombre de
    la zona porque un nombre exige que el servidor MySQL tenga cargadas las
    tablas de zonas horarias (un MySQL local en Windows normalmente no las
    tiene); un desfase numerico funciona en cualquier servidor, y al
    calcularlo en cada conexion respeta el horario de verano de Chile."""
    crudo = datetime.now(ZoneInfo(zona_iana)).strftime("%z")  # ej. '-0300'
    return f"{crudo[:3]}:{crudo[3:]}"


def get_connection():
    """Abre una conexion nueva a MySQL usando la configuracion de .env.

    La sesion queda en la hora de Chile (config `DB_TIMEZONE`), asi
    CURRENT_TIMESTAMP / NOW() -- fecha_venta, fecha_creacion, etc. -- se
    guardan en hora local y los filtros por dia de los reportes coinciden
    con el dia que ve el usuario (Aiven trabaja en UTC por defecto: una
    venta a las 21:30 caeria "al dia siguiente").
    """
    cfg = get_db_config()

    connect_kwargs = dict(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        time_zone=_desfase_mysql(cfg.time_zone),
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
