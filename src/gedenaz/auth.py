"""Autenticación del administrador."""

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def is_valid_admin_login(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD
