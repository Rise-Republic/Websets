#!/bin/bash
# Wrapper to run the Python certificate generator for backward compatibility
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/generate_mtls_certs.py" "$@"

