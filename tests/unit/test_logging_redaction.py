from loguru import logger
import json

from app.logging_utils import configure_logging, redact_message


def test_redact_message():
    msg = "token=abcd password=mysecret email=user@example.com prompt: secret query"
    redacted = redact_message(msg)
    assert "abcd" not in redacted
    assert "mysecret" not in redacted
    assert "user@example.com" not in redacted
    assert "prompt: secret" not in redacted
    assert "token=<redacted>" in redacted
    assert "password=<redacted>" in redacted
    assert "email=<redacted>" in redacted


def test_logging_filter(caplog):
    configure_logging("INFO")
    logger.add(caplog.handler, level="INFO")
    with caplog.at_level("INFO"):
        logger.info("user email=test@example.com token=abc123")
    assert "test@example.com" not in caplog.text
    assert "abc123" not in caplog.text
    assert "email=<redacted>" in caplog.text
    assert "token=<redacted>" in caplog.text


def test_json_logging_format():
    """Logs should be serialized to JSON when enabled."""
    logs = []
    configure_logging("INFO", json=True)
    logger.add(lambda m: logs.append(m), level="INFO", serialize=True)
    logger.info("user email=test@example.com token=abc123")

    assert logs, "no log captured"
    log_entry = json.loads(logs[0])
    text = log_entry.get("text", "")
    assert "test@example.com" not in text
    assert "abc123" not in text
    assert "<redacted>" in text
