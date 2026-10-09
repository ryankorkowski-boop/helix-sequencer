"""Review-only compatibility wrapper for the sixth distinct source song.

Running from an actual .py entrypoint (rather than stdin) is required because
run_showcase_audio_batch finishes native xLights previews with spawned workers.
This leaves the existing five-track pipeline and original MP3 files unchanged.
"""
from __future__ import annotations

import sys

from tools import run_showcase_audio_batch as batch


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/run_audiolights_30s_review.py /path/to/xlights/AppRun")
    xlights = sys.argv[1]
    batch.TRACKS = (("Helix_Audiolights", "Helix Audiolights"),) + batch.TRACKS[1:]
    sys.argv = [
        "tools/run_audiolights_30s_review.py",
        "--audio-dir", "outputs/30s_clips",
        "--track", "Helix_Audiolights",
        "--output", "outputs/six_up_Helix_Audiolights",
        "--workers", "2",
        "--xlights", xlights,
    ]
    batch.main()


if __name__ == "__main__":
    main()
