from gedenaz.config import DBConfig
from gedenaz.data import database


def test_create_connection_verifies_tls_when_ca_is_configured(monkeypatch):
    received = {}

    def connect(**kwargs):
        received.update(kwargs)
        return "connection"

    monkeypatch.setattr(database.mysql.connector, "connect", connect)
    config = DBConfig(
        host="gateway.example",
        port=4000,
        user="cloud-user",
        password="secret",
        database="gedenaz",
        ssl_ca="C:/certs/tidb-ca.pem",
    )

    result = database.create_connection(config)

    assert result == "connection"
    assert received == {
        "host": "gateway.example",
        "port": 4000,
        "user": "cloud-user",
        "password": "secret",
        "database": "gedenaz",
        "ssl_ca": "C:/certs/tidb-ca.pem",
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
    }


def test_create_connection_preserves_local_mysql_options_without_ca(monkeypatch):
    received = {}

    def connect(**kwargs):
        received.update(kwargs)
        return "connection"

    monkeypatch.setattr(database.mysql.connector, "connect", connect)
    config = DBConfig(
        host="localhost",
        port=3306,
        user="local-user",
        password="secret",
        database="gedenaz",
    )

    database.create_connection(config)

    assert received == {
        "host": "localhost",
        "port": 3306,
        "user": "local-user",
        "password": "secret",
        "database": "gedenaz",
    }
