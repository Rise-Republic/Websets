#!/usr/bin/env python3
"""Detect plaintext secret usage in configuration files.

This script scans for sensitive environment variables like VAULT_TOKEN or
MINIO_ROOT_PASSWORD being specified directly rather than via their
corresponding *_FILE variants. It is intended to run in CI to prevent
accidental commits of plaintext secrets.
"""

from __future__ import annotations

import re
import sys
from loguru import logger
from pathlib import Path

# Environment variables that should only be provided via *_FILE
SENSITIVE_VARS = [
    "VAULT_TOKEN",
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "POSTGRES_ENCRYPTION_KEY",
]

FILES_TO_SCAN = [
    Path(".env"),
    Path("docker-compose.yml"),
]

FILES_TO_SCAN += list(Path("k8s").glob("*.yaml"))


def contains_plaintext(line: str, var: str) -> bool:
    """Return True if the line contains the variable without `_FILE` usage."""
    # Strip comments
    line_no_comments = line.split("#", 1)[0]
    pattern = rf"\b{re.escape(var)}\b(?!_FILE)"
    return re.search(pattern, line_no_comments) is not None


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Scan a file and return list of violations."""
    matches: list[tuple[int, str, str]] = []
    if not path.exists():
        return matches
    with path.open() as f:
        for i, line in enumerate(f, 1):
            for var in SENSITIVE_VARS:
                if contains_plaintext(line, var):
                    matches.append((i, var, line.rstrip()))
    return matches


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    violations: dict[Path, list[tuple[int, str, str]]] = {}

    for file_path in FILES_TO_SCAN:
        full_path = repo_root / file_path
        matches = scan_file(full_path)
        if matches:
            violations[file_path] = matches

    if violations:
        logger.error("Plaintext secrets detected:")
        for path, matches in violations.items():
            for line_no, var, line in matches:
                logger.error(f"{path}:{line_no}: {var} -> {line}")
        return 1

    logger.info("No plaintext secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
