#!/usr/bin/env sh
set -eu
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" "$(dirname "$0")/scripts/bootstrap.py"

