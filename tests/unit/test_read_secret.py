import os
from pathlib import Path
from app.config.env import read_secret, SECRETS_DIR


def test_read_secret_file(tmp_path, monkeypatch):
    secret_file = tmp_path / "MY_SECRET"
    secret_file.write_text("from_file")
    monkeypatch.setattr('app.config.env.SECRETS_DIR', tmp_path)
    monkeypatch.setenv("MY_SECRET", "env_value")
    assert read_secret("MY_SECRET") == "from_file"


def test_read_secret_env(monkeypatch):
    monkeypatch.setattr('app.config.env.SECRETS_DIR', Path("/nonexistent"))
    monkeypatch.setenv("MY_SECRET", "env_value")
    assert read_secret("MY_SECRET") == "env_value"
