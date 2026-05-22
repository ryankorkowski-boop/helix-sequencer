#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/ci/run_required_checks.py
