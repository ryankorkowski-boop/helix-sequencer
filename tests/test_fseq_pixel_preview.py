"""FSEQ V1/V2 real channel decoding and per-node rendered color output."""
from __future__ import annotations

from pathlib import Path
import struct
import zlib

import pytest

from tools.fseq_pixel_preview import FseqReader, pixels_from_csv, render_fseq_preview


def write_fseq(path: Path, *, version=1, frames=(bytes([255, 0, 0, 0, 255, 0]),),
               compression=0, sparse=()):
    count = len(frames[0])
    assert all(len(frame) == count for frame in frames)
    block_count = 1 if compression else 0
    header_size = 28 if version == 1 else 32
    data_offset = header_size + 8 * block_count + 6 * len(sparse)
    header = bytearray(data_offset)
    header[0:4] = b"PSEQ"
    struct.pack_into("<H", header, 4, data_offset)
    header[7] = version
    struct.pack_into("<II", header, 10, count, len(frames))
    header[18] = 50
    contents = b"".join(frames)
    if compression:
        payload = zlib.compress(contents) if compression == 2 else contents
        header[20] = compression
        header[21] = 1
        struct.pack_into("<II", header, 32, 0, len(payload))
    else:
        payload = contents
    if sparse:
        header[22] = len(sparse)
        start = 32 + 8 * block_count
        for i, (channel, length) in enumerate(sparse):
            header[start + i * 6 : start + i * 6 + 3] = channel.to_bytes(3, "little")
            header[start + i * 6 + 3 : start + i * 6 + 6] = length.to_bytes(3, "little")
    path.write_bytes(header + payload)


def test_fseq_v1_exact_channel_colors(tmp_path: Path):
    path = tmp_path / "v1.fseq"
    write_fseq(path, frames=[bytes([255, 10, 2, 0, 70, 255]), bytes([0, 0, 0, 0, 0, 0])])
    reader = FseqReader(path)
    assert reader.info.version == 1
    assert reader.offset_for_channel(1) == 0
    assert reader.offset_for_channel(6) == 5
    assert reader.offset_for_channel(7) is None
    assert list(reader.iter_frames()) == [bytes([255, 10, 2, 0, 70, 255]), bytes(6)]


def test_fseq_v2_sparse_addresses(tmp_path: Path):
    path = tmp_path / "v2sparse.fseq"
    write_fseq(path, version=2, frames=[bytes([7, 8, 9, 11, 12, 13])],
               sparse=[(0, 3), (100, 3)])
    reader = FseqReader(path)
    assert reader.offset_for_channel(1) == 0
    assert reader.offset_for_channel(4) is None
    assert reader.offset_for_channel(101) == 3
    assert reader.offset_for_channel(103) == 5
    assert list(reader.iter_frames()) == [bytes([7, 8, 9, 11, 12, 13])]


def test_fseq_v2_zlib_compressed_blocks(tmp_path: Path):
    path = tmp_path / "v2zlib.fseq"
    frames = [bytes([10, 11, 12]), bytes([1, 2, 3])]
    write_fseq(path, version=2, frames=frames, compression=2)
    reader = FseqReader(path)
    assert reader.info.compression == 2
    assert list(reader.iter_frames()) == frames


def test_fseq_bad_magic_fails_closed(tmp_path: Path):
    path = tmp_path / "bad.fseq"
    path.write_bytes(b"bad file")
    with pytest.raises(ValueError, match="Not an FSEQ"):
        FseqReader(path)


def test_pixel_csv_coordinates_are_respected(tmp_path: Path):
    path = tmp_path / "pixels.csv"
    path.write_text("channel,x,y,kind\n1,10,25,rgb\n101,15,20,white\n")
    nodes = pixels_from_csv(path)
    assert nodes[0].one_based_channel == 1
    assert nodes[0].x == 10 and nodes[0].y == 25
    assert nodes[1].kind == "white"


def test_native_fseq_renders_real_mp4_and_report(tmp_path: Path):
    pytest.importorskip("imageio")
    pytest.importorskip("PIL")
    pytest.importorskip("imageio_ffmpeg")
    path, points = tmp_path / "song.fseq", tmp_path / "pixels.csv"
    write_fseq(path, frames=[
        bytes([255, 0, 0, 0, 255, 0]),
        bytes([0, 0, 255, 255, 255, 255])
    ])
    points.write_text("channel,x,y,kind\n1,10,20,rgb\n4,40,20,rgb\n")
    out = tmp_path / "actual.mp4"
    report = render_fseq_preview(path, out, pixel_map=points, width=64, height=64)
    assert out.exists() and out.stat().st_size > 100
    assert report["frames"] == 2
    assert report["geometry"] == "explicit"
    assert report["native_xlights_effect_render"]
