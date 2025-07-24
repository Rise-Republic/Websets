#!/usr/bin/env python3
"""Check certificate expiration dates and log warnings."""

import os
import subprocess
from loguru import logger
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

CERT_DIR = os.getenv("CERT_DIR", "certs")
WARN_DAYS = int(os.getenv("CERT_EXPIRY_WARN_DAYS", "30"))


def _get_expiration(cert_path: Path) -> datetime:
    """Return the expiration datetime for a certificate."""
    result = subprocess.run(
        ["openssl", "x509", "-enddate", "-noout", "-in", str(cert_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    end_str = result.stdout.strip().split("=", 1)[1]
    return datetime.strptime(end_str, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=timezone.utc
    )


def check_certificates(
    cert_dir: str = CERT_DIR, warn_days: int = WARN_DAYS
) -> Dict[str, int]:
    """Return a mapping of certificate name to days remaining if expiring soon."""
    expiring: Dict[str, int] = {}
    now = datetime.now(timezone.utc)
    for crt in Path(cert_dir).glob("*.crt"):
        try:
            expires = _get_expiration(crt)
        except subprocess.CalledProcessError as exc:
            logger.error("Failed to read %s: %s", crt, exc)
            continue
        days_left = (expires - now).days
        if days_left <= warn_days:
            logger.warning(
                "Certificate %s expires in %s days",
                crt.name,
                days_left,
            )
            expiring[crt.name] = days_left
    return expiring


if __name__ == "__main__":
    check_certificates()
