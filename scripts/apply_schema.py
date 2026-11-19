"""Aplica el esquema de GedeNaz a la base configurada (.env o GEDENAZ_ENV_FILE).

Uso (desde la raiz del proyecto):
    python scripts/apply_schema.py                 # usa schema_cloud.sql
    python scripts/apply_schema.py otro_archivo.sql

Crea la base (DB_NAME) si no existe y luego las tablas faltantes. Es
idempotente: se puede repetir sin perder datos. No modifica tablas que ya
existen con otra estructura (ver docs/GUIA_PRUEBAS_LOCAL.md, seccion 2).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import mysql.connector  # noqa: E402

from gedenaz.config import get_db_config  # noqa: E402
from gedenaz.data.database import _mysql_offset, _resolve_ca_path  # noqa: E402

DEFAULT_SQL = ROOT / "src" / "gedenaz" / "data" / "schema_cloud.sql"


def _statements(sql_text: str) -> list[str]:
    # Se descartan los comentarios antes de separar por ";".
    clean = "\n".join(
        line for line in sql_text.splitlines() if not line.lstrip().startswith("--")
    )
    return [s.strip() for s in clean.split(";") if s.strip()]


def main() -> None:
    sql_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SQL
    cfg = get_db_config()
    if not re.fullmatch(r"[A-Za-z0-9_]+", cfg.database):
        raise SystemExit(f"DB_NAME invalido: {cfg.database!r}")

    options = dict(
        host=cfg.host, port=cfg.port, user=cfg.user, password=cfg.password,
        time_zone=_mysql_offset(cfg.time_zone),
    )
    if cfg.ssl_ca:
        options.update(ssl_ca=_resolve_ca_path(cfg.ssl_ca), ssl_verify_cert=True)

    conn = mysql.connector.connect(**options)
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{cfg.database}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.execute(f"USE `{cfg.database}`")
    for statement in _statements(sql_path.read_text(encoding="utf-8")):
        if statement.upper().startswith(("CREATE DATABASE", "USE ")):
            continue  # la base ya se creo/selecciono arriba
        cursor.execute(statement)
        if cursor.with_rows:
            cursor.fetchall()
    conn.commit()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"OK: {sql_path.name} aplicado a {cfg.database}@{cfg.host}")
    print("Tablas:", ", ".join(tables))


if __name__ == "__main__":
    main()
