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
    assert report["source"].startswith("FSEQ channel data")
    assert report["native_xlights_origin_verified_by_this_tool"] is False


def test_rgb_wire_color_order_can_be_configured(tmp_path: Path):
    path = tmp_path / "wire.csv"
    path.write_text("channel,x,y,kind\n1,0,0,grb\n")
    assert pixels_from_csv(path)[0].kind == "grb"


def test_compressed_fseq_noncontiguous_blocks_fail(tmp_path: Path):
    path = tmp_path / "broken.fseq"
    write_fseq(path, version=2, frames=[bytes([12, 13, 14])], compression=2)
    buf = bytearray(path.read_bytes())
    struct.pack_into("<I", buf, 32, 42)  # must start at frame 0
    path.write_bytes(buf)
    with pytest.raises(ValueError, match="Noncontiguous FSEQ"):
        list(FseqReader(path).iter_frames())


def test_fseq_v2_historical_raw_first_block(tmp_path: Path):
    path = tmp_path / "legacyzlib.fseq"
    original = bytes([9, 10, 11])
    write_fseq(path, version=2, frames=[original], compression=2)
    buf = bytearray(path.read_bytes())
    raw_offset = 32 + 8
    struct.pack_into("<I", buf, 36, len(original))
    path.write_bytes(buf[:raw_offset] + original)
    assert list(FseqReader(path).iter_frames()) == [original]


def test_comparison_decoder_keeps_dark_sparse_gaps_and_fractional_rate(tmp_path):
    from tools.layout_bench.xlights_fseq import load_fseq
    path = tmp_path / "repacked.fseq"
    write_fseq(path, version=2, compression=2, sparse=[(30, 3), (63, 3)],
               frames=[bytes([1, 2, 3, 4, 5, 6])])
    data = bytearray(path.read_bytes())
    data[18] = 40
    path.write_bytes(data)
    packed = load_fseq(path)
    assert packed.sparse_start == 30
    assert next(packed.rows()).tolist() == [1, 2, 3] + [0] * 30 + [4, 5, 6]
    data[18] = 33
    path.write_bytes(data)
    assert load_fseq(path).fps() == pytest.approx(1000 / 33)


def test_native_reuse_requires_inputs_and_intact_decodable_output(tmp_path, monkeypatch):
    from tools.layout_bench import xlights_fseq as bench
    binary = tmp_path / "xLights"
    binary.write_bytes(b"test executable identity")
    monkeypatch.setenv("XLIGHTS_BIN", str(binary))
    paths = {key: tmp_path / key for key in ("layout_xml", "xsq_path", "media_path")}
    for path in paths.values():
        path.write_bytes(b"old")
    target, show = tmp_path / "show.fseq", tmp_path / "show"
    calls = []
    def producer(binary, layout, sequence, audio, directory):
        calls.append(sequence.read_bytes())
        output = directory / "output.fseq"
        write_fseq(output, version=2)
        return output, "test-version"
    monkeypatch.setattr(bench, "_run_xlights", producer)
    def render():
        return bench.render_sequence_to_fseq(**paths, fseq_path=target, show_dir=show)
    target.write_bytes(b"x" * 1024)
    assert render() == render() == "test-version"
    assert len(calls) == 1
    for key in paths:
        paths[key].write_bytes(b"new")
        render()
    assert len(calls) == 4
    target.write_bytes(b"x" * target.stat().st_size)
    render()
    assert len(calls) == 5


def test_comparison_panel_reuse_checks_bytes_and_render_inputs(tmp_path, monkeypatch):
    from tools.layout_bench import render_comparisons as bench
    calls = []
    def encode(panel, output):
        calls.append(panel["title"])
        output.write_bytes(b"panel output" * 1100)
        return {"fps": 20.0, "report": []}
    monkeypatch.setattr(bench, "_encode_panel", encode)
    layout = tmp_path / "layout.xml"
    layout.write_text("<xrgb/>")
    fseq = tmp_path / "source.fseq"
    write_fseq(fseq, version=2)
    monkeypatch.setattr(bench, "_ffmpeg", lambda: str(layout))
    panel = {"layout": layout, "fseq": fseq, "title": "one", "channels": 6}
    output = tmp_path / "panel.mp4"
    output.write_bytes(b"x" * 12000)
    bench.write_panel_mp4(panel, output)
    bench.write_panel_mp4(panel, output)
    panel["title"] = "two"
    bench.write_panel_mp4(panel, output)
    output.write_bytes(b"x" * output.stat().st_size)
    bench.write_panel_mp4(panel, output)
    assert calls == ["one", "two", "two"]


def test_direct_30fps_encode_preserves_one_second_source_clock(tmp_path):
    imageio = pytest.importorskip("imageio.v2")
    pytest.importorskip("PIL")
    pytest.importorskip("imageio_ffmpeg")
    source, points = tmp_path / "source.fseq", tmp_path / "pixels.csv"
    write_fseq(source, frames=[bytes([0, 255, 0])] * 20)
    points.write_text("channel,x,y,kind\n1,10,20,grb\n")
    out = tmp_path / "direct.mp4"
    report = render_fseq_preview(source, out, pixel_map=points, width=128, height=128,
                                 output_fps=30)
    assert report["frames"] == 20
    assert report["source_fps"] == 20
    assert report["output_fps"] == 30
    assert report["bright_node_samples"] == 20
    with imageio.get_reader(str(out)) as reader:
        assert reader.get_meta_data()["fps"] == pytest.approx(30)
        assert reader.count_frames() == 30
    assert b"HELIX_PROVENANCE_V1" in out.read_bytes()
