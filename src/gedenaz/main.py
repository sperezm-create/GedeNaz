"""Punto de entrada del backend (API) de GedeNaz App.

Confirma que el entorno de desarrollo (Python + Flask + venv) esta
correctamente configurado. Los endpoints CRUD reales se agregan en
las Fases 1-3 (ver docs/specs/04-plan-de-trabajo.md).
"""

from gedenaz.app import create_app


def main() -> None:
    app = create_app()
    app.run(debug=True)


if __name__ == "__main__":
    main()
