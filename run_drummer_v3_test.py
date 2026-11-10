#!/usr/bin/env python3
"""Run Drummer V3 test with crumdemo.wav audio from desktop."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DESKTOP_AUDIO = Path.home() / "Desktop" / "414" / "drumdemo.wav"
OUTPUT_DIR = ROOT / "test_runs" / "drummer_v3_test"


def main() -> int:
    """Run the export_helix_flow_review_artifacts with Drummer V3 and desktop audio."""
    if not DESKTOP_AUDIO.exists():
        print(f"ERROR: Audio file not found: {DESKTOP_AUDIO}", file=sys.stderr)
        print(f"Expected: {DESKTOP_AUDIO}", file=sys.stderr)
        return 1

    print(f"Audio file: {DESKTOP_AUDIO}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"File size: {DESKTOP_AUDIO.stat().st_size / (1024*1024):.2f} MB")

    command = [
        sys.executable,
        "-m",
        "tools.export_helix_flow_review_artifacts",
        "--output-dir",
        str(OUTPUT_DIR),
        "--audio",
        str(DESKTOP_AUDIO),
    ]

    print(f"\nRunning: {' '.join(command)}\n")
    result = subprocess.run(command, cwd=ROOT)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
