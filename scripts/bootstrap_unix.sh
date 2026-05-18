#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
"$SCRIPT_DIR/run_smoke.sh"
