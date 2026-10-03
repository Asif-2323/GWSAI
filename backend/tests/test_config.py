import importlib
import sys


def test_settings_reads_mongo_uri_from_mongo_uri_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb+srv://example.mongodb.net/")
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("MONGODB_DB_NAME", raising=False)

    sys.modules.pop("config", None)
    config_module = importlib.import_module("config")

    assert config_module.settings.mongodb_uri == "mongodb+srv://example.mongodb.net/"
