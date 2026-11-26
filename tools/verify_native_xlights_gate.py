"""Fail closed unless native xLights produces a fresh FSEQ for a staged XSQ."""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zlib


def inspect_fseq(path: Path) -> dict[str, int]:
    with path.open("rb") as src:
        header = src.read(20)
        if len(header) != 20 or header[:4] != b"PSEQ":
            raise ValueError(f"Invalid FSEQ header: {path}")
        offset = struct.unpack_from("<H", header, 4)[0]
        channels, frames, step = struct.unpack_from("<IIB", header, 10)
        major = header[7]
        if not (20 <= offset < path.stat().st_size and channels and frames and step and major in {1, 2}):
            raise ValueError(f"FSEQ has no usable frame payload: {path}")
        compression = 0
        blocks = []
        if major == 2:
            extensions = src.read(12)
            if len(extensions) != 12 or offset < 32:
                raise ValueError("Truncated FSEQ v2 header")
            compression = extensions[0] & 0x0F
            count = ((extensions[0] & 0xF0) << 4) | extensions[1]
            if compression not in {0, 1, 2} or 32 + count * 8 + extensions[2] * 6 > offset:
                raise ValueError("Invalid FSEQ compression table")
            blocks = [(first, size) for first, size in struct.iter_unpack("<II", src.read(count * 8)) if size]
        if not compression:
            blocks = [(0, channels * frames)]
        if not blocks or blocks[0][0] != 0:
            raise ValueError("FSEQ is missing the first frame block")

        decompress = None
        if compression == 1:
            library = ctypes.util.find_library("zstd")
            if not library:
                raise ValueError("libzstd is required to inspect the pinned renderer's FSEQ")
            decompress = ctypes.CDLL(library).ZSTD_decompress
            decompress.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t)
            decompress.restype = ctypes.c_size_t

        src.seek(offset)
        active_frames = 0
        for (first, size), (last, _) in zip(blocks, [*blocks[1:], (frames, 0)]):
            if not first < last <= frames or size > path.stat().st_size - src.tell():
                raise ValueError("Invalid FSEQ frame block")
            expected = channels * (last - first)
            packed = src.read(size)
            if decompress is not None:
                data = ctypes.create_string_buffer(expected)
                if decompress(data, expected, packed, size) != expected:
                    raise ValueError("Unreadable zstd FSEQ frame block")
                decoded = data.raw
            elif compression == 2:
                decoded = zlib.decompress(packed)
            else:
                decoded = packed
            if len(decoded) != expected:
                raise ValueError("FSEQ frame block has the wrong size")
            active_frames += sum(bool(decoded[i:i + channels].strip(b"\x00"))
                                 for i in range(0, expected, channels))
        if not active_frames:
            raise ValueError("Native FSEQ rendered no active channels")
    return {"channels": channels, "frames": frames, "step_ms": step, "active_frames": active_frames}


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
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], check=True)
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
