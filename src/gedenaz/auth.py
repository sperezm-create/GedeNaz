"""Autenticación del administrador.

Las credenciales se toman de API_ADMIN_USERNAME / API_ADMIN_PASSWORD (.env),
las mismas que usa la API y la app móvil: una sola cuenta para todo.
Si no están configuradas se usan las predeterminadas originales.
"""

import secrets

from gedenaz.config import get_configured_admin

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def is_valid_admin_login(username: str, password: str) -> bool:
    expected_username, expected_password = get_configured_admin() or (
        ADMIN_USERNAME,
        ADMIN_PASSWORD,
    )
    return secrets.compare_digest(
        username.strip().encode("utf-8"), expected_username.encode("utf-8")
    ) & secrets.compare_digest(
        password.encode("utf-8"), expected_password.encode("utf-8")
    )
