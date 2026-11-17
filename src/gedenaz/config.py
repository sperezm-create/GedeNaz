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


def get_api_credentials() -> tuple[str, str]:
    username = os.getenv("API_ADMIN_USERNAME", "").strip()
    password = os.getenv("API_ADMIN_PASSWORD", "")
    if not username or not password:
        raise RuntimeError(
            "Configura API_ADMIN_USERNAME y API_ADMIN_PASSWORD antes de iniciar la API."
        )
    return username, password
