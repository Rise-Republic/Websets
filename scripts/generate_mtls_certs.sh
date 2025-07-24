#!/bin/bash
# Wrapper for generate_mtls_certs.py for backward compatibility
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/generate_mtls_certs.py" "$@"

