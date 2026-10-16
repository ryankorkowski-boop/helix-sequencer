"""Inspect actual FSEQ channel bytes, separate from native rendering."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any, Sequence


MAX_BYTES = 128 * 1024 * 1024


def _decode(payload: bytes, compression: int, expected: int) -> bytes:
    if compression == 0:
        result = payload
    elif compression == 2:
        decoder = zlib.decompressobj()
        result = decoder.decompress(payload, expected + 1)
        if (not decoder.eof or decoder.unused_data
                or decoder.unconsumed_tail):
            raise ValueError("Invalid or oversized zlib FSEQ block")
    elif compression == 1:
        name = ctypes.util.find_library("zstd")
        if name is None:
            raise ValueError("ZSTD FSEQ inspection needs system libzstd")
        library = ctypes.CDLL(name)
        library.ZSTD_decompress.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t,
        ]
        library.ZSTD_decompress.restype = ctypes.c_size_t
        library.ZSTD_isError.argtypes = [ctypes.c_size_t]
        library.ZSTD_isError.restype = ctypes.c_uint
        output = ctypes.create_string_buffer(expected)
        size = library.ZSTD_decompress(
            output, expected, payload, len(payload))
        if library.ZSTD_isError(size):
            raise ValueError("Invalid ZSTD FSEQ block")
        result = output.raw[:size]
    else:
        raise ValueError(f"Unsupported FSEQ compression: {compression}")
    if len(result) != expected:
        raise ValueError("FSEQ block length does not match its frame interval")
    return result


def read_frames(path: Path) -> tuple[bytes, int, int, int]:
    """Read bounded v1/v2 FSEQ, including native ZSTD and zlib blocks."""
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Diagnostic FSEQ exceeds 128 MiB")
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"PSEQ":
        raise ValueError("Not a complete PSEQ/FSEQ header")
    offset = int.from_bytes(raw[4:6], "little")
    version = raw[7]
    channels, frames = struct.unpack_from("<II", raw, 10)
    step = raw[18]
    if (not channels or not frames or not step
            or channels * frames > MAX_BYTES):
        raise ValueError("Invalid or oversized FSEQ frame dimensions")
    if offset < 20 or offset > len(raw):
        raise ValueError("Invalid FSEQ data offset")
    if version == 1:
        data = _decode(raw[offset:], 0, channels * frames)
    elif version == 2:
        if len(raw) < 32 or offset < 32:
            raise ValueError("Incomplete FSEQ v2 header")
        compression = raw[20] & 15
        count = ((raw[20] & 240) << 4) | raw[21]
        sparse_count = raw[22]
        if 32 + count * 8 + sparse_count * 6 > offset:
            raise ValueError("FSEQ tables overlap the channel data")
        ranges = []
        packed_channels = channels
        if sparse_count:
            ranges = [
                (int.from_bytes(raw[i:i + 3], "little"),
                 int.from_bytes(raw[i + 3:i + 6], "little"))
                for i in range(32 + count * 8,
                               32 + count * 8 + sparse_count * 6, 6)
            ]
            packed_channels = sum(n for _, n in ranges)
            if (packed_channels > channels
                    or any(n == 0 for _, n in ranges)
                    or any(a + n > channels for a, n in ranges)
                    or any(a + n > b for (a, n), (b, _) in
                           zip(ranges, ranges[1:]))):
                raise ValueError("Invalid FSEQ sparse ranges")
        if compression == 0:
            data = _decode(raw[offset:offset + packed_channels * frames], 0,
                           packed_channels * frames)
        else:
            blocks = [struct.unpack_from("<II", raw, 32 + i * 8)
                      for i in range(count)]
            blocks = [(first, size) for first, size in blocks if size]
            if (not blocks or blocks[0][0] != 0
                    or any(a >= b for (a, _), (b, _) in
                           zip(blocks, blocks[1:]))
                    or blocks[-1][0] >= frames):
                raise ValueError("Invalid FSEQ block frame boundaries")
            output = bytearray()
            for index, (first, size) in enumerate(blocks):
                end = (blocks[index + 1][0]
                       if index + 1 < len(blocks) else frames)
                if offset + size > len(raw):
                    raise ValueError("Truncated FSEQ compressed block")
                output.extend(_decode(raw[offset:offset + size], compression,
                                      (end - first) * packed_channels))
                offset += size
            # Native v2.2 may append embedded layout/sequence metadata after
            # the last compressed block. It is not channel data.
            data = bytes(output)
        if ranges:
            expanded = bytearray(frames * channels)
            for frame in range(frames):
                cursor = frame * packed_channels
                for first, count in ranges:
                    begin = frame * channels + first
                    expanded[begin:begin + count] = data[cursor:cursor + count]
                    cursor += count
            data = bytes(expanded)
    else:
        raise ValueError(f"Unsupported FSEQ version: {version}")
    return data, channels, frames, step


def inspect_fseq(path: Path) -> dict[str, Any]:
    data, channels, frames, step = read_frames(path)
    lit = [sum(value > 0 for value in data[i:i + channels])
           for i in range(0, len(data), channels)]
    dark = []
    start: int | None = None
    for index, value in enumerate([*lit, 1]):
        if value == 0 and start is None:
            start = index
        elif value and start is not None:
            dark.append({"start_ms": start * step, "end_ms": index * step})
            start = None
    return {
        "schema": "helix.fseq_channel_evidence.v1",
        "basis": "decoded_rendered_channel_bytes",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "channels": channels, "frames": frames, "frame_ms": step,
        "duration_ms": frames * step,
        "nonzero_samples": sum(lit),
        "nonzero_frames": sum(n > 0 for n in lit),
        "peak_lit_channels": max(lit),
        "mean_lit_fraction": round(sum(lit) / (frames * channels), 6),
        "dark_windows": dark,
        "visual_review": "pending", "controller_validation": "not_tested",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fseq", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-channels", type=int)
    parser.add_argument("--expected-duration-ms", type=int)
    parser.add_argument("--require-nonzero", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = inspect_fseq(args.fseq)
        if (args.expected_channels is not None
                and report["channels"] != args.expected_channels):
            raise ValueError("Native channel count does not match benchmark")
        if (args.expected_duration_ms is not None
                and report["duration_ms"] != args.expected_duration_ms):
            raise ValueError("Native duration does not match benchmark")
        if args.require_nonzero and not report["nonzero_samples"]:
            raise ValueError("Native benchmark rendered entirely black")
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
    except (OSError, ValueError, zlib.error) as exc:
        parser.exit(2, f"native quality check: {exc}\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
