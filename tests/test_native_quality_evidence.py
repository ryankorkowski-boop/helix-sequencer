from __future__ import annotations

import json
import struct
import subprocess
import sys
import zlib
import pytest

from tools.quality.native import inspect_fseq, read_frames


def fseq_v1(data, channels=2, frames=4):
    header = bytearray(28)
    header[:4] = b"PSEQ"
    struct.pack_into("<H", header, 4, 28)
    header[7] = 1
    struct.pack_into("<II", header, 10, channels, frames)
    header[18] = 50
    return bytes(header) + data


def test_inspector_measures_channel_bytes_not_effect_presence(tmp_path):
    path = tmp_path / "native.fseq"
    path.write_bytes(fseq_v1(bytes([0, 0, 255, 0, 128, 64, 0, 0])))
    report = inspect_fseq(path)
    assert report["frames"] == 4
    assert report["nonzero_samples"] == 3
    assert report["nonzero_frames"] == 2
    assert report["peak_lit_channels"] == 2
    assert report["mean_lit_fraction"] == .375
    assert report["dark_windows"] == [
        {"start_ms": 0, "end_ms": 50},
        {"start_ms": 150, "end_ms": 200},
    ]
    assert report["visual_review"] == "pending"
    assert report == inspect_fseq(path)


def test_sparse_zlib_blocks_expand_to_physical_channels(tmp_path):
    header = bytearray(46)
    header[:4] = b"PSEQ"
    struct.pack_into("<H", header, 4, 46)
    header[6:8] = bytes([2, 2])
    # Native header stores the packed width, not the expanded channel span.
    struct.pack_into("<II", header, 10, 1, 3)
    header[18] = 50
    header[20:23] = bytes([2, 1, 1])
    compressed = zlib.compress(bytes([255, 0, 128]))
    struct.pack_into("<II", header, 32, 0, len(compressed))
    header[40:46] = bytes([1, 0, 0, 1, 0, 0])
    path = tmp_path / "sparse.fseq"
    # Native v2.2 can append embedded layout/sequence data after the blocks.
    path.write_bytes(header + compressed + b"embedded metadata")
    data, channels, frames, step = read_frames(path)
    assert (channels, frames, step) == (2, 3, 50)
    assert data == bytes([0, 255, 0, 0, 0, 128])
    assert inspect_fseq(path)["nonzero_samples"] == 2


def test_sparse_destination_beyond_packed_width_and_expansion_guard(tmp_path, monkeypatch):
    from tools.quality import native
    header = bytearray(46)
    header[:4] = b'PSEQ'
    struct.pack_into('<H', header, 4, 46)
    header[6:8] = bytes([2, 2])
    struct.pack_into('<II', header, 10, 1, 2)
    header[18] = 25
    header[20:23] = bytes([2, 1, 1])
    compressed = zlib.compress(bytes([100, 200]))
    struct.pack_into('<II', header, 32, 0, len(compressed))
    header[40:46] = bytes([5, 0, 0, 1, 0, 0])
    path = tmp_path/'standalone.fseq'
    path.write_bytes(header + compressed)
    data, channels, frames, step = read_frames(path)
    assert (channels, frames, step) == (6, 2, 25)
    assert data == bytes([0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 200])
    monkeypatch.setattr(native, 'MAX_BYTES', 64)
    header[40:43] = bytes([200, 0, 0])
    path.write_bytes(header + compressed)
    with pytest.raises(ValueError, match='expanded sparse'):
        read_frames(path)


@pytest.mark.parametrize("payload", [
    b"", b"not an fseq",
    fseq_v1(bytes(7)),
    fseq_v1(bytes(8), channels=0),
    fseq_v1(bytes(8), frames=0),
])
def test_corrupt_fseq_cannot_produce_evidence(tmp_path, payload):
    path = tmp_path / "broken.fseq"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        inspect_fseq(path)


def test_cli_rejects_black_render_and_does_not_write_success_report(tmp_path):
    path = tmp_path / "black.fseq"
    path.write_bytes(fseq_v1(bytes(8)))
    report = tmp_path / "evidence.json"
    command = [sys.executable, "-m", "tools.quality.native", str(path),
               "--require-nonzero", "--output", str(report)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2
    assert "entirely black" in result.stderr
    assert not report.exists()
    path.write_bytes(fseq_v1(bytes([0, 0, 255, 0, 128, 64, 0, 0])))
    subprocess.run(command, capture_output=True, check=True)
    assert json.loads(report.read_text())["nonzero_samples"] == 3


def test_streaming_dense_activity_matches_existing_inspector(tmp_path):
    path = tmp_path/'native.fseq'
    path.write_bytes(fseq_v1(bytes([0, 0, 255, 0, 128, 64, 0, 0])))
    assert inspect_fseq(path, streaming=True) == inspect_fseq(path)


def test_streaming_sparse_timeline_keeps_allocation_fence(tmp_path, monkeypatch):
    from tools.quality import native
    header = bytearray(46)
    header[:4] = b'PSEQ'
    struct.pack_into('<H', header, 4, 46)
    header[6:8] = bytes([2, 2])
    struct.pack_into('<II', header, 10, 1, 4)
    header[18] = 50
    header[20:23] = bytes([2, 1, 1])
    compressed = zlib.compress(bytes([0, 255, 0, 128]))
    struct.pack_into('<II', header, 32, 0, len(compressed))
    header[40:46] = bytes([200, 0, 0, 1, 0, 0])
    path = tmp_path/'sparse.fseq'
    path.write_bytes(header + compressed)
    monkeypatch.setattr(native, 'MAX_BYTES', 128)
    with pytest.raises(ValueError, match='expanded sparse'):
        read_frames(path)
    report = inspect_fseq(path, streaming=True)
    assert report['channels'] == 201 and report['nonzero_samples'] == 2
    assert report['dark_windows'] == [dict(start_ms=0, end_ms=50), dict(start_ms=100, end_ms=150)]


def test_streaming_oversized_block_refused_before_decompression(tmp_path, monkeypatch):
    from tools.quality import native
    header = bytearray(40)
    header[:4] = b'PSEQ'
    struct.pack_into('<H', header, 4, 40)
    header[6:8] = bytes([2, 2])
    struct.pack_into('<II', header, 10, 1, 100)
    header[18] = 50
    header[20:22] = bytes([2, 1])
    compressed = zlib.compress(bytes(100))
    struct.pack_into('<II', header, 32, 0, len(compressed))
    path = tmp_path/'oversized.fseq'
    path.write_bytes(header + compressed)
    monkeypatch.setattr(native, 'MAX_BYTES', 64)
    with pytest.raises(ValueError, match='oversized streaming FSEQ block'):
        inspect_fseq(path, streaming=True)


def test_streaming_truncated_compression_is_not_accepted(tmp_path):
    header = bytearray(40)
    header[:4] = b'PSEQ'
    struct.pack_into('<H', header, 4, 40)
    header[6:8] = bytes([2, 2])
    struct.pack_into('<II', header, 10, 1, 10)
    header[18] = 50
    header[20:22] = bytes([2, 1])
    compressed = zlib.compress(bytes(10))
    struct.pack_into('<II', header, 32, 0, len(compressed))
    path = tmp_path/'truncated.fseq'
    path.write_bytes(header + compressed[:-1])
    with pytest.raises(ValueError, match='Truncated streaming FSEQ block'):
        inspect_fseq(path, streaming=True)
