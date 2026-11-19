"""Comprueba la conexion a la base y que el esquema este aplicado.

Uso: python scripts/check_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gedenaz.config import get_db_config  # noqa: E402
from gedenaz.data.database import create_connection  # noqa: E402

EXPECTED = {"producto", "venta", "detalle_venta", "plan_pago", "cuota", "abono"}


def main() -> int:
    cfg = get_db_config()
    print(f"Conectando a {cfg.database}@{cfg.host}:{cfg.port} como {cfg.user} ...")
    try:
        conn = create_connection()
    except Exception as exc:  # noqa: BLE001
        print(f"FALLO la conexion: {exc}")
        return 1
    cursor = conn.cursor()
    cursor.execute("SELECT NOW()")
    print("Hora de la sesion (debe ser hora de Chile):", cursor.fetchone()[0])
    cursor.execute("SHOW TABLES")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    missing = EXPECTED - tables
    if missing:
        print("Faltan tablas:", ", ".join(sorted(missing)))
        print("Ejecuta: python scripts/apply_schema.py")
        return 2
    print("OK: conexion y tablas correctas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
