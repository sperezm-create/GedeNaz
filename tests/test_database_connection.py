from pathlib import Path

from gedenaz import config as config_module
from gedenaz.config import PROJECT_ROOT, DBConfig, get_db_config
from gedenaz.data import database


def _capture(monkeypatch):
    received = {}

    def connect(**kwargs):
        received.update(kwargs)
        return "connection"

    monkeypatch.setattr(database.mysql.connector, "connect", connect)
    monkeypatch.setattr(database, "_mysql_offset", lambda zone: "-03:00")
    return received


def test_create_connection_verifies_certificate_when_ca_is_configured(monkeypatch):
    received = _capture(monkeypatch)
    config = DBConfig(
        host="gateway.example", port=4000, user="cloud-user", password="secret",
        database="gedenaz", ssl_ca="/certs/tidb-ca.pem",
    )

    assert database.create_connection(config) == "connection"
    assert received == {
        "host": "gateway.example",
        "port": 4000,
        "user": "cloud-user",
        "password": "secret",
        "database": "gedenaz",
        "time_zone": "-03:00",
        "ssl_ca": str(Path("/certs/tidb-ca.pem")),
        "ssl_verify_cert": True,
    }


def test_create_connection_can_also_verify_hostname(monkeypatch):
    received = _capture(monkeypatch)
    config = DBConfig(
        host="h", port=4000, user="u", password="p", database="d",
        ssl_ca="/certs/ca.pem", ssl_verify_identity=True,
    )

    database.create_connection(config)

    assert received["ssl_verify_identity"] is True


def test_relative_ca_path_is_resolved_against_project_root(monkeypatch):
    received = _capture(monkeypatch)
    config = DBConfig(
        host="h", port=4000, user="u", password="p", database="d",
        ssl_ca="secrets/tidb-ca.pem",
    )

    database.create_connection(config)

    assert received["ssl_ca"] == str(PROJECT_ROOT / "secrets" / "tidb-ca.pem")


def test_create_connection_preserves_local_mysql_options_without_ca(monkeypatch):
    received = _capture(monkeypatch)
    config = DBConfig(
        host="localhost", port=3306, user="local-user", password="secret",
        database="gedenaz",
    )

    database.create_connection(config)

    assert received == {
        "host": "localhost",
        "port": 3306,
        "user": "local-user",
        "password": "secret",
        "database": "gedenaz",
        "time_zone": "-03:00",
    }


def test_mysql_offset_uses_chile_time():
    assert database._mysql_offset("America/Santiago") in {"-03:00", "-04:00"}


def test_config_reads_timezone_and_identity_flag(monkeypatch):
    monkeypatch.setenv("DB_TIMEZONE", "UTC")
    monkeypatch.setenv("DB_SSL_VERIFY_IDENTITY", "true")
    cfg = get_db_config()
    assert cfg.time_zone == "UTC"
    assert cfg.ssl_verify_identity is True
    monkeypatch.delenv("DB_TIMEZONE")
    monkeypatch.delenv("DB_SSL_VERIFY_IDENTITY")
    cfg = get_db_config()
    assert cfg.time_zone == "America/Santiago"
    assert cfg.ssl_verify_identity is False


def test_env_file_selector_is_supported():
    assert "GEDENAZ_ENV_FILE" in Path(config_module.__file__).read_text(encoding="utf-8")
