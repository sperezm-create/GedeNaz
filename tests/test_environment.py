"""Smoke test de la tarea 1.1: confirma que el entorno de desarrollo
del backend (paquetes del requirements.txt y el paquete gedenaz) esta
correctamente instalado y es importable.
"""


def test_dependencias_instaladas():
    import flask  # noqa: F401
    import mysql.connector  # noqa: F401
    import dotenv  # noqa: F401


def test_paquete_gedenaz_importable():
    from gedenaz import config

    db_config = config.get_db_config()
    assert db_config.database == "gedenaz"


def test_api_health():
    from gedenaz.app import create_app

    client = create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
