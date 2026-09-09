"""Smoke test de la tarea 1.1: confirma que el entorno de desarrollo
(paquetes del requirements.txt y el paquete gedenaz) esta correctamente
instalado y es importable.
"""

import tkinter


def test_dependencias_instaladas():
    import mysql.connector  # noqa: F401
    import dotenv  # noqa: F401


def test_paquete_gedenaz_importable():
    from gedenaz import config

    db_config = config.get_db_config()
    assert db_config.database == "gedenaz"


def test_tkinter_disponible():
    root = tkinter.Tk()
    root.withdraw()
    root.destroy()
