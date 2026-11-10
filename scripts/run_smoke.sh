#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m compileall core ai xlights tools tests main.py gui_launcher.py
python main.py --list-profiles
python -m pytest -q \
  tests/test_sequence_builder.py \
  tests/test_effects_orchestrator_bridge.py \
  tests/test_xlights_contract_validator.py \
  tests/test_beta_demo_fixture.py

cat <<'EOF'

Beta smoke foundation complete.

This smoke wrapper proves the repo compiles, the CLI can list profiles, selected contract tests pass,
and the clean-room beta fixture is parseable/generated without private or copyrighted inputs.

It does not claim xLights import success, visual quality, controller/channel safety, or a full
end-to-end beta sequence run. Those gates require separate artifact evidence.
EOF
