"""Levanta la API FastAPI de GedeNaz sin configurar PYTHONPATH a mano.

Uso (desde la raiz del proyecto):
    python scripts/run_api.py

Lee `.env`, o el archivo indicado en GEDENAZ_ENV_FILE (ej. env.tidb).
Variables opcionales: GEDENAZ_API_HOST (def. 0.0.0.0), GEDENAZ_API_PORT (def. 8000).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402

from gedenaz.config import get_api_credentials, get_db_config  # noqa: E402


def main() -> None:
    get_api_credentials()  # falla temprano si faltan usuario/clave de la API
    cfg = get_db_config()
    host = os.getenv("GEDENAZ_API_HOST", "0.0.0.0")
    port = int(os.getenv("GEDENAZ_API_PORT", "8000"))
    print(f"Base de datos: {cfg.database}@{cfg.host}:{cfg.port}")
    print(f"API: http://127.0.0.1:{port}  (documentacion en /docs, Ctrl+C para detener)")
    uvicorn.run("gedenaz.api:app", host=host, port=port)


if __name__ == "__main__":
    main()
