"""Smoke test de la tarea 1.1: confirma que el entorno de desarrollo
del backend (paquetes del requirements.txt y el paquete gedenaz) esta
correctamente instalado y es importable.
"""

import os

import pytest


def test_dependencias_instaladas():
    import flask  # noqa: F401
    import mysql.connector  # noqa: F401
    import dotenv  # noqa: F401


def test_paquete_gedenaz_importable():
    from gedenaz import config

    db_config = config.get_db_config()
    # El nombre depende del .env de cada quien (gedenaz, defaultdb, test...):
    # solo se comprueba que la configuracion cargue.
    assert db_config.database


def test_api_health():
    from gedenaz.app import create_app

    client = create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


@pytest.mark.skipif(
    not os.getenv("DB_PASSWORD"),
    reason="Requiere un .env con credenciales reales de MySQL",
)
def test_api_health_db():
    from gedenaz.app import create_app

    client = create_app().test_client()
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
