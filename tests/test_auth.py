from gedenaz.auth import is_valid_admin_login


def test_login_uses_credentials_from_env(monkeypatch):
    monkeypatch.setenv("API_ADMIN_USERNAME", "dueño")
    monkeypatch.setenv("API_ADMIN_PASSWORD", "clave-secreta")

    assert is_valid_admin_login("dueño", "clave-secreta")
    assert is_valid_admin_login("  dueño ", "clave-secreta")
    assert not is_valid_admin_login("dueño", "otra")
    assert not is_valid_admin_login("admin", "clave-secreta")
    assert not is_valid_admin_login("", "")


def test_login_falls_back_to_original_defaults_without_env(monkeypatch):
    monkeypatch.delenv("API_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("API_ADMIN_PASSWORD", raising=False)

    assert is_valid_admin_login("admin", "admin123")
    assert not is_valid_admin_login("admin", "mala")
