"""Native xLights headless XSQ -> FSEQ render with retained output option.

Generated FSEQ can feed tools/fseq_pixel_preview.py for real pixel output.
This never infers LOR controller addresses or silently treats the XML preview
as a native render.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from contextlib import nullcontext


def validate_native_xlights(
    xlights: Path, show_dir: Path, xsq: Path,
    timeout_s: int = 300, output_dir: Path | None = None,
):
    executable, show_dir, xsq = Path(xlights), Path(show_dir), Path(xsq)
    if not executable.is_file():
        raise FileNotFoundError(f"xLights executable not found: {executable}")
    if not show_dir.is_dir() or not (show_dir / "xlights_rgbeffects.xml").exists():
        raise ValueError("Show directory must contain xlights_rgbeffects.xml")
    if not xsq.is_file():
        raise FileNotFoundError(f"Sequence not found: {xsq}")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        context = nullcontext(output_dir)
    else:
        context = TemporaryDirectory(prefix="helix-native-xlights-")
    with context as path:
        output = Path(path)
        # Never mistake an old FSEQ for this run's success.
        before = {
            p.name: (p.stat().st_size, p.stat().st_mtime_ns)
            for p in output.glob("*.fseq")
        }
        command = [
            str(executable), "--headless", "-s", str(show_dir),
            "--outputdir", str(output), str(xsq)
        ]
        result = subprocess.run(
            command, capture_output=True, text=True,
            timeout=timeout_s, check=False,
        )
        produced = [
            p for p in output.glob("*.fseq")
            if p.stat().st_size > 0 and
            before.get(p.name) != (p.stat().st_size, p.stat().st_mtime_ns)
        ]
        render_ok = (result.returncode == 0 and bool(produced))
        return {
            "native_xlights_render_verified": bool(render_ok),
            "return_code": result.returncode,
            "generated_fseq_count": len(produced),
            "fseq_paths": [str(p) for p in produced] if output_dir else [],
            "output_sizes": {p.name: p.stat().st_size for p in produced},
            "persistent_output": bool(output_dir),
            "stderr_tail": result.stderr[-4000:],
            "stdout_tail": result.stdout[-4000:],
            "command": command,
            "note": "A successful FSEQ render does not verify Light-O-Rama controller wiring.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xsq", type=Path)
    parser.add_argument("--show-dir", type=Path, required=True)
    parser.add_argument("--xlights-exe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path,
                        help="Keep real FSEQ artifacts here; otherwise temporary")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    report = validate_native_xlights(
        args.xlights_exe, args.show_dir, args.xsq,
        timeout_s=args.timeout, output_dir=args.output_dir
    )
    print(json.dumps(report, indent=2))
    if not report["native_xlights_render_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
