"""Optional real xLights headless render validation (actual FSEQ, not mock preview).

Requires a configured xLights show folder and an installed xLights build that
supports --headless. Never labels XML-only checks as native xLights validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def validate_native_xlights(xlights: Path, show_dir: Path, xsq: Path, timeout_s=180):
    executable, show_dir, xsq = Path(xlights), Path(show_dir), Path(xsq)
    if not executable.is_file():
        raise FileNotFoundError(f"xLights executable not found: {executable}")
    if not show_dir.is_dir() or not (show_dir / "xlights_rgbeffects.xml").exists():
        raise ValueError("Show directory must contain an xlights_rgbeffects.xml layout")
    if not xsq.is_file():
        raise FileNotFoundError(f"Sequence not found: {xsq}")

    with tempfile.TemporaryDirectory(prefix="helix-native-xlights-") as temp:
        output = Path(temp)
        command = [
            str(executable), "--headless", "-s", str(show_dir),
            "--outputdir", str(output), str(xsq)
        ]
        result = subprocess.run(
            command, capture_output=True, text=True,
            timeout=timeout_s, check=False
        )
        products = list(output.glob("*.fseq"))
        render_ok = (result.returncode == 0 and
                     any(p.stat().st_size > 0 for p in products))
        return {
            "native_xlights_render_verified": bool(render_ok),
            "return_code": result.returncode,
            "generated_fseq_count": len(products),
            "output_sizes": {p.name: p.stat().st_size for p in products},
            "stderr_tail": result.stderr[-4000:],
            "stdout_tail": result.stdout[-4000:],
            "command": command,
            "note": "A successful FSEQ render does not confirm physical Light-O-Rama controller wiring.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xsq", type=Path)
    parser.add_argument("--show-dir", type=Path, required=True)
    parser.add_argument("--xlights-exe", type=Path, required=True)
    args = parser.parse_args()
    report = validate_native_xlights(args.xlights_exe, args.show_dir, args.xsq)
    print(json.dumps(report, indent=2))
    if not report["native_xlights_render_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
