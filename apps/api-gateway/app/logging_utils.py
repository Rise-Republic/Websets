import re
import sys
from loguru import logger

SENSITIVE_FIELDS = ["password", "secret", "token", "api_key", "jwt", "email", "prompt"]
_PATTERN = re.compile(rf"({'|'.join(SENSITIVE_FIELDS)})\s*[:=]\s*([^\s,]+)", re.IGNORECASE)


def redact_message(message: str) -> str:
    """Replace sensitive values in a log message with '<redacted>'."""
    if not isinstance(message, str):
        return message
    return _PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", message)


def _patch_record(record):
    record["message"] = redact_message(record["message"])


def configure_logging(level: str = "INFO", json: bool = False) -> None:
    """Configure loguru with redaction.

    Parameters
    ----------
    level: str
        Minimum log level to output.
    json: bool, optional
        When True logs are serialized to JSON for easier ingestion by
        log aggregation systems.
    """

    logger.remove()
    logger.configure(patcher=_patch_record)

    if json:
        logger.add(sys.stdout, level=level, serialize=True)
    else:
        logger.add(
            sys.stdout,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )
