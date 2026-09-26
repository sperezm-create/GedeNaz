"""Start a dedicated local API connected to TiDB Cloud for the test app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Configure before importing gedenaz.config, which loads the selected env file.
os.environ["GEDENAZ_ENV_FILE"] = str(ROOT / "env.tidb")
os.environ.setdefault("GEDENAZ_API_HOST", "0.0.0.0")
os.environ.setdefault("GEDENAZ_API_PORT", "5001")

from gedenaz.app import create_app  # noqa: E402


if __name__ == "__main__":
    print("TiDB test API: http://0.0.0.0:5001 (Ctrl+C para detener)")
    create_app().run(
        host=os.environ["GEDENAZ_API_HOST"],
        port=int(os.environ["GEDENAZ_API_PORT"]),
        debug=False,
    )
