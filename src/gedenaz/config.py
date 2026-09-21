"""Carga de configuracion desde variables de entorno (.env).

Ver docs/specs/05-entorno-desarrollo.md para como generar el archivo .env
a partir de .env.example.

Por defecto se lee `.env` de la raiz del repo. Para apuntar a OTRA base sin
tocar ese archivo (ej. probar un proveedor nuevo), definir la variable de
entorno GEDENAZ_ENV_FILE con el nombre de otro archivo de la raiz:

    GEDENAZ_ENV_FILE=.env.tidb pytest

Con GEDENAZ_ENV_FILE definida NO se lee `.env`, asi que nunca se mezclan
credenciales de dos bases distintas.
"""

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

_RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(_RAIZ / (os.getenv("GEDENAZ_ENV_FILE") or ".env"))


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    # Ruta al certificado CA (obligatorio en Aiven). Ojo al usarlo con
    # mysql-connector-python: si se pasa ssl_ca, hay que pasar TAMBIEN
    # ssl_verify_cert=True (o ssl-mode='VERIFY_CA'/'VERIFY_IDENTITY'),
    # si no tira "Invalid ssl-mode" -- mismo error que da MySQL Workbench
    # si el "Use SSL" no se pone en "Require and Verify CA".
    ssl_ca: str | None = None
    # Zona horaria (nombre IANA) en la que se guardan las fechas. Ver
    # data/db.py::get_connection.
    time_zone: str = "America/Santiago"


def get_db_config() -> DBConfig:
    return DBConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gedenaz"),
        ssl_ca=os.getenv("DB_SSL_CA") or None,
        time_zone=os.getenv("DB_TIMEZONE") or "America/Santiago",
    )
