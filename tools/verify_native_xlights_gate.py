"""Fail closed unless native xLights produces a fresh FSEQ for a staged XSQ."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess


def inspect_fseq(path: Path) -> dict[str, int]:
    with path.open("rb") as src:
        header = src.read(20)
    if len(header) != 20 or header[:4] != b"PSEQ":
        raise ValueError(f"Invalid FSEQ header: {path}")
    offset = struct.unpack_from("<H", header, 4)[0]
    channels, frames, step = struct.unpack_from("<IIB", header, 10)
    if not (20 <= offset < path.stat().st_size and channels and frames and step):
        raise ValueError(f"FSEQ has no usable frame payload: {path}")
    return {"channels": channels, "frames": frames, "step_ms": step}


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlights", required=True, type=Path)
    parser.add_argument("--show", required=True, type=Path, help="Disposable show folder")
    parser.add_argument("--xsq", required=True, type=Path)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", args.commit) or commit != args.commit:
        parser.error("Requested commit does not match the exact checkout")
    show = args.show.resolve()
    xsq = args.xsq.resolve()
    if xsq.parent != show or xsq.suffix.lower() != ".xsq" or not xsq.is_file():
        parser.error("Supply a real XSQ staged directly in the disposable show folder")
    if not (show / "xlights_rgbeffects.xml").is_file():
        parser.error("The disposable show folder must contain xlights_rgbeffects.xml")
    native = args.xlights.resolve(strict=True)
    input_hashes = {
        "audio_input_sha256": sha256(args.audio),
        "layout_input_sha256": sha256(show / "xlights_rgbeffects.xml"),
        "template_input_sha256": sha256(args.template),
    }
    fseq = xsq.with_suffix(".fseq")
    if fseq.exists() or args.evidence.exists():
        parser.error("Use a fresh output directory; existing FSEQ/evidence cannot pass the gate")
    xsq_hash = sha256(xsq)
    subprocess.run([str(native), "-r", "-s", str(show), str(xsq)], cwd=show, check=True, timeout=300)
    details = inspect_fseq(fseq)
    evidence = {
        "scope": "native_xsq_open_and_fseq_render_smoke",
        "commit": commit,
        "renderer_sha256": sha256(native),
        "xsq_input_sha256": xsq_hash,
        **input_hashes,
        "fseq_sha256": sha256(fseq),
        **details,
        "drummer_oracle": "not_evaluated",
        "annotated_faces": "not_evaluated",
    }
    with args.evidence.open("x", encoding="utf-8") as output:
        json.dump(evidence, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
