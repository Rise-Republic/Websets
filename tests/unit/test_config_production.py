import os
import sys
import pytest

# Ensure app module path is available
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))
)

import app.config as config


def test_disable_vault_in_production_exits(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DISABLE_VAULT_FOR_LOCAL_DEV", "true")
    monkeypatch.setenv("CI", "false")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        config.validate_settings()


def test_missing_vault_vars_in_production_exits(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CI", "false")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("DISABLE_VAULT_FOR_LOCAL_DEV", raising=False)
    with pytest.raises(SystemExit):
        config.validate_settings()
