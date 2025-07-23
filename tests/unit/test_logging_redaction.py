from loguru import logger

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
