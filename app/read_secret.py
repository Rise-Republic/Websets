from pathlib import Path
import os
from typing import Optional

SECRETS_DIR = Path('/run/secrets')


def read_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read a secret from /run/secrets/<name> if present, else from env."""
    path = SECRETS_DIR / name
    if path.exists():
        try:
            return path.read_text().strip()
        except Exception:
            pass
    return os.getenv(name, default)
