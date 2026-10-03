#!/usr/bin/env bash
set -euo pipefail
: "${AUDIO_URL:?Set AUDIO_URL to a directly downloadable audio URL}"
mkdir -p test_runs/drummer_ground_truth/audio
curl -fL --retry 3 --retry-all-errors "$AUDIO_URL" -o test_runs/drummer_ground_truth/audio/input.mp3
python - <<'PY'
from pathlib import Path
p=Path('test_runs/drummer_ground_truth/audio/input.mp3')
if p.stat().st_size < 10000:
    raise SystemExit(f'Audio download suspiciously small: {p.stat().st_size} bytes')
print(f'Using audio: {p} ({p.stat().st_size} bytes)')
PY
