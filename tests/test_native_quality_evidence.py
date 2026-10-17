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
    struct.pack_into("<II", header, 10, 3, 3)
    header[18] = 50
    header[20:23] = bytes([2, 1, 1])
    compressed = zlib.compress(bytes([255, 0, 128]))
    struct.pack_into("<II", header, 32, 0, len(compressed))
    header[40:46] = bytes([1, 0, 0, 1, 0, 0])
    path = tmp_path / "sparse.fseq"
    # Native v2.2 can append embedded layout/sequence data after the blocks.
    path.write_bytes(header + compressed + b"embedded metadata")
    data, channels, frames, step = read_frames(path)
    assert (channels, frames, step) == (3, 3, 50)
    assert data == bytes([0, 255, 0, 0, 0, 0, 0, 128, 0])
    assert inspect_fseq(path)["nonzero_samples"] == 2


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
