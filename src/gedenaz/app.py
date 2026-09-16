"""Fabrica de la app Flask (API) de GedeNaz App.

La app Android consume esta API por HTTP; nunca se conecta a MySQL
directo (ver docs/specs/03-arquitectura.md). Los endpoints de negocio
(productos) se agregan como blueprints en src/gedenaz/api/ a medida que
se implementan RF1-RF4 (Fase 1 en adelante, ver docs/specs/04-plan-de-trabajo.md).
"""

from flask import Flask, jsonify

from gedenaz.api.productos import productos_bp
from gedenaz.data.db import get_connection


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(productos_bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="gedenaz-api")

    @app.get("/health/db")
    def health_db():
        try:
            conn = get_connection()
            conn.close()
        except Exception as exc:  # noqa: BLE001 -- reportar cualquier falla de conexion tal cual
            return jsonify(status="error", detail=str(exc)), 503
        return jsonify(status="ok", service="gedenaz-db")

    return app
