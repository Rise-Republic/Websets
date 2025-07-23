#!/usr/bin/env python3
"""Check Vault connectivity and secret availability."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.secrets.vault import cli_test_connection

if __name__ == "__main__":
    cli_test_connection()
