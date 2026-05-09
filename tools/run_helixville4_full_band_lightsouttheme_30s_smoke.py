from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_helixville4_full_band_lightsouttheme_30s.py"
OUT = ROOT / "test_runs" / "helixville4_full_band_lightsouttheme_30s"
REPORT = OUT / "full_band_lightsouttheme_30s.smoke.json"


def main() -> int:
    command = [sys.executable, str(RUNNER), "--output-dir", str(OUT)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    payload = {
        "schema": "helixville4.full_band_lightsouttheme_30s.smoke.v1",
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "expected_outputs": {
            "layout": str(OUT / "xlights_rgbeffects.xml"),
            "manifest": str(OUT / "helixia_manifest.json"),
            "run_report": str(OUT / "full_band_lightsouttheme_30s.run.json"),
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
