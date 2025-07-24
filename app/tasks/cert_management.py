"""Celery tasks for certificate management."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from subprocess import run, CalledProcessError

from loguru import logger

from .celery_app import celery_app

CERT_DIR = os.getenv("CERT_DIR", "certs")
WARN_DAYS = int(os.getenv("CERT_EXPIRY_WARN_DAYS", "30"))


def _get_expiration(cert_path: Path) -> datetime:
    result = run(
        ["openssl", "x509", "-enddate", "-noout", "-in", str(cert_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    end_str = result.stdout.strip().split("=", 1)[1]
    return datetime.strptime(end_str, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=timezone.utc
    )


def _check(cert_dir: str = CERT_DIR, warn_days: int = WARN_DAYS) -> Dict[str, int]:
    expiring: Dict[str, int] = {}
    now = datetime.now(timezone.utc)
    for crt in Path(cert_dir).glob("*.crt"):
        try:
            expires = _get_expiration(crt)
        except CalledProcessError as exc:
            logger.error(f"Failed to read {crt}: {exc}")
            continue
        days_left = (expires - now).days
        if days_left <= warn_days:
            logger.warning(f"Certificate {crt.name} expires in {days_left} days")
            expiring[crt.name] = days_left
    return expiring


@celery_app.task
def check_certificate_expiration() -> Dict[str, int]:
    """Log and return certificates expiring soon."""
    return _check()
