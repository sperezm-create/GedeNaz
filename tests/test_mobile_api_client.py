import requests
import pytest

from mobile.api_client import ApiClient


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.auth = None
        self.request_args = None

    def request(self, method, url, timeout):
        self.request_args = (method, url, timeout)
        return self.response


def build_response(status_code, payload):
    response = requests.Response()
    response.status_code = status_code
    response._content = requests.compat.json.dumps(payload).encode("utf-8")
    response.url = "https://api.example.test/auth/login"
    return response


def test_client_rejects_urls_without_http_scheme():
    with pytest.raises(ValueError, match="URL completa"):
        ApiClient("api.example.test", "admin", "secret")


def test_login_uses_basic_auth_and_returns_username(monkeypatch):
    session = FakeSession(build_response(200, {"username": "admin"}))
    monkeypatch.setattr("mobile.api_client.requests.Session", lambda: session)
    client = ApiClient("https://api.example.test/", "admin", "secret")
    session.auth = ("admin", "secret")

    assert client.login() == "admin"
    assert session.request_args == (
        "POST",
        "https://api.example.test/auth/login",
        10.0,
    )
    assert session.auth == ("admin", "secret")


def test_login_reports_invalid_credentials(monkeypatch):
    session = FakeSession(build_response(401, {"detail": "Unauthorized"}))
    monkeypatch.setattr("mobile.api_client.requests.Session", lambda: session)
    client = ApiClient("https://api.example.test", "wrong", "wrong")

    with pytest.raises(RuntimeError, match="Usuario o contraseña"):
        client.login()
