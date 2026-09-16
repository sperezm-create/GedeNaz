"""Aplica un archivo .sql a la base de datos configurada en .env.

Uso:
    python scripts/apply_schema.py src/gedenaz/data/schema_cloud.sql

Util para correr schema.sql / schema_cloud.sql sin depender de un cliente
grafico (MySQL Workbench a veces se cuelga en "Starting editor session"
contra bases remotas).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mysql.connector  # noqa: E402

from gedenaz.config import get_db_config  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/apply_schema.py <archivo.sql>")
        raise SystemExit(1)

    sql_path = Path(sys.argv[1])
    sql_text = sql_path.read_text(encoding="utf-8")

    cfg = get_db_config()
    connect_kwargs = dict(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
    )
    if cfg.ssl_ca:
        connect_kwargs["ssl_ca"] = cfg.ssl_ca
        connect_kwargs["ssl_verify_cert"] = True

    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    conn = mysql.connector.connect(**connect_kwargs)
    cursor = conn.cursor()
    for statement in statements:
        cursor.execute(statement)
        if cursor.with_rows:
            cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    print(f"OK: {sql_path.name} aplicado a {cfg.database}@{cfg.host}")


if __name__ == "__main__":
    main()
