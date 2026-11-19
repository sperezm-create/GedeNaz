"""Carga de configuracion desde variables de entorno (.env).

Ver docs/specs/05-entorno-desarrollo.md para como generar el archivo .env
a partir de .env.example.

Por defecto se lee `.env` de la raiz del repo. Para apuntar a OTRA base sin
tocar ese archivo (ej. la misma base TiDB que usa el proyecto databaseconnect),
definir GEDENAZ_ENV_FILE con el nombre de otro archivo de la raiz:

    GEDENAZ_ENV_FILE=env.tidb python scripts/run_api.py

Con GEDENAZ_ENV_FILE definida NO se lee `.env`, asi nunca se mezclan
credenciales de dos bases distintas.
"""

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / (os.getenv("GEDENAZ_ENV_FILE") or ".env"))

_TRUE_VALUES = {"1", "true", "yes", "si", "on"}


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    ssl_ca: str | None = None
    # Zona horaria (nombre IANA) en la que se guardan las fechas. TiDB/Aiven
    # trabajan en UTC por defecto: sin esto una venta a las 21:30 en Chile
    # quedaria "al dia siguiente" en el calendario y las estadisticas mensuales.
    time_zone: str = "America/Santiago"
    # Verificar ademas que el nombre del host coincida con el certificado.
    # Desactivado por defecto: es lo que usa databaseconnect y funciona con
    # TiDB Cloud; activar con DB_SSL_VERIFY_IDENTITY=true si se desea.
    ssl_verify_identity: bool = False


def get_db_config() -> DBConfig:
    return DBConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gedenaz"),
        ssl_ca=os.getenv("DB_SSL_CA") or None,
        time_zone=os.getenv("DB_TIMEZONE") or "America/Santiago",
        ssl_verify_identity=os.getenv("DB_SSL_VERIFY_IDENTITY", "").strip().lower()
        in _TRUE_VALUES,
    )


def get_api_credentials() -> tuple[str, str]:
    username = os.getenv("API_ADMIN_USERNAME", "").strip()
    password = os.getenv("API_ADMIN_PASSWORD", "")
    if not username or not password:
        raise RuntimeError(
            "Configura API_ADMIN_USERNAME y API_ADMIN_PASSWORD antes de iniciar la API."
        )
    return username, password


def get_configured_admin() -> tuple[str, str] | None:
    """Credenciales del .env, o None si no estan definidas."""
    username = os.getenv("API_ADMIN_USERNAME", "").strip()
    password = os.getenv("API_ADMIN_PASSWORD", "")
    return (username, password) if username and password else None
