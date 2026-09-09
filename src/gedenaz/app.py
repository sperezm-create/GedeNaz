"""Fabrica de la app Flask (API) de GedeNaz App.

La app Android consume esta API por HTTP; nunca se conecta a MySQL
directo (ver docs/specs/03-arquitectura.md). Los endpoints de negocio
(productos) se agregan como blueprints en src/gedenaz/api/ a medida que
se implementan RF1-RF4 (Fase 1 en adelante, ver docs/specs/04-plan-de-trabajo.md).
"""

from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="gedenaz-api")

    return app
