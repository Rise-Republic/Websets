import os
import sys
import pytest

# Ensure app module path is available
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))
)

import importlib


def load_config():
    if 'app.config' in sys.modules:
        del sys.modules['app.config']
    return importlib.import_module('app.config')


def test_disable_vault_in_production_exits(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DISABLE_VAULT", "true")
    monkeypatch.setenv("CI", "false")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    with pytest.raises(SystemExit):
        config = load_config()
        config.get_settings()


def test_missing_vault_vars_in_production_exits(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CI", "false")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("DISABLE_VAULT", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    with pytest.raises(SystemExit):
        config = load_config()
        config.get_settings()
