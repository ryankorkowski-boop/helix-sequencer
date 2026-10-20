"""Inspect actual FSEQ channel bytes, separate from native rendering."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import struct
import zlib
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence


MAX_BYTES = 128 * 1024 * 1024


@lru_cache(maxsize=1)
def _zstd_library():
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
    return library


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
        library = _zstd_library()
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
            # Native V2 header channel count is the packed width; sparse
            # destinations may start beyond that width (standalone models).
            if (packed_channels != channels
                    or any(n == 0 for _, n in ranges)
                    or any(a + n > b for (a, n), (b, _) in
                           zip(ranges, ranges[1:]))):
                raise ValueError("Invalid FSEQ sparse ranges")
            channels = max(a + n for a, n in ranges)
            if channels * frames > MAX_BYTES:
                raise ValueError("Invalid or oversized expanded sparse dimensions")
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


# Inspection may span a full song without allocating its expanded sparse movie.
# Keep the original per-block memory bound; total decoded work is also bounded.
MAX_SHOW_BYTES = 16 * 1024 * 1024 * 1024
MAX_SHOW_FRAMES = 1_000_000


def _stream_activity(path: Path) -> tuple[list[int], int, int, int]:
    import numpy as np
    size = path.stat().st_size
    if size > MAX_SHOW_BYTES:
        raise ValueError("FSEQ exceeds bounded full-show inspection size")
    with path.open('rb') as stream:
        fixed = stream.read(32)
        if len(fixed) < 20 or fixed[:4] != b'PSEQ':
            raise ValueError("Not a complete PSEQ/FSEQ header")
        offset = int.from_bytes(fixed[4:6], 'little')
        version = fixed[7]
        packed, frames = struct.unpack_from('<II', fixed, 10)
        step = fixed[18]
        if (not packed or not frames or not step or frames > MAX_SHOW_FRAMES
                or packed > MAX_BYTES or packed * frames > MAX_SHOW_BYTES):
            raise ValueError("Invalid or oversized FSEQ frame dimensions")
        if offset < 20 or offset > size:
            raise ValueError("Invalid FSEQ data offset")
        channels = packed
        compression = 0
        blocks = []
        if version == 2:
            if len(fixed) < 32 or offset < 32:
                raise ValueError("Incomplete FSEQ v2 header")
            compression = fixed[20] & 15
            count = ((fixed[20] & 240) << 4) | fixed[21]
            sparse_count = fixed[22]
            if 32 + count * 8 + sparse_count * 6 > offset:
                raise ValueError("FSEQ tables overlap the channel data")
            stream.seek(0)
            header = stream.read(offset)
            if sparse_count:
                ranges = [(int.from_bytes(header[i:i+3], 'little'),
                           int.from_bytes(header[i+3:i+6], 'little'))
                          for i in range(32 + count * 8,
                                         32 + count * 8 + sparse_count * 6, 6)]
                if (sum(n for _, n in ranges) != packed or any(n == 0 for _, n in ranges)
                        or any(a + n > b for (a, n), (b, _) in zip(ranges, ranges[1:]))):
                    raise ValueError("Invalid FSEQ sparse ranges")
                channels = max(a + n for a, n in ranges)
                if channels * frames > MAX_SHOW_BYTES:
                    raise ValueError("Invalid or oversized expanded sparse dimensions")
            if compression:
                blocks = [struct.unpack_from('<II', header, 32 + i * 8) for i in range(count)]
                blocks = [(first, length) for first, length in blocks if length]
                if (not blocks or blocks[0][0] != 0 or blocks[-1][0] >= frames
                        or any(a >= b for (a, _), (b, _) in zip(blocks, blocks[1:]))):
                    raise ValueError("Invalid FSEQ block frame boundaries")
        elif version != 1:
            raise ValueError(f"Unsupported FSEQ version: {version}")
        lit: list[int] = []

        def add(data):
            # Sparse holes are zero; counts are identical without expanding
            # millions of nonexistent channels into RAM for every frame.
            values = np.frombuffer(data, dtype=np.uint8).reshape(-1, packed)
            lit.extend(np.count_nonzero(values, axis=1).tolist())

        stream.seek(offset)
        if compression:
            for index, (first, length) in enumerate(blocks):
                end = blocks[index+1][0] if index+1 < len(blocks) else frames
                expected = (end - first) * packed
                if expected > MAX_BYTES or length > MAX_BYTES:
                    raise ValueError("FSEQ compressed block exceeds bounded inspection memory")
                payload = stream.read(length)
                if len(payload) != length:
                    raise ValueError("Truncated FSEQ compressed block")
                add(_decode(payload, compression, expected))
        else:
            expected = packed * frames
            if size - offset < expected or (version == 1 and size - offset != expected):
                raise ValueError("FSEQ block length does not match its frame interval")
            per_chunk = max(1, (4 * 1024 * 1024) // packed)
            for first in range(0, frames, per_chunk):
                length = min(per_chunk, frames - first) * packed
                add(_decode(stream.read(length), 0, length))
        if len(lit) != frames:
            raise ValueError("Decoded FSEQ frame count differs from header")
    return lit, channels, frames, step


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def inspect_fseq(path: Path) -> dict[str, Any]:
    lit, channels, frames, step = _stream_activity(path)
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
        "sha256": _file_sha256(path),
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
