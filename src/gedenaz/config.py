"""Carga de configuracion desde variables de entorno (.env).

Ver docs/specs/05-entorno-desarrollo.md para como generar el archivo .env
a partir de .env.example.
"""

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


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


def get_db_config() -> DBConfig:
    return DBConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gedenaz"),
        ssl_ca=os.getenv("DB_SSL_CA") or None,
    )
