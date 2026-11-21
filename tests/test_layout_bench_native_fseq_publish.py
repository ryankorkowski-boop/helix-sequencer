"""Fail-closed validation for native xLights FSEQ cache publication."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.layout_bench import xlights_fseq
from tools.layout_bench.render_cache import receipt_path


@pytest.mark.parametrize(
    "declared,step,decoded",
    [(0, 50, 0), (3, 0, 3), (3, 50, 2)],
)
def test_native_render_rejects_empty_invalid_or_truncated_fseq(
    tmp_path, monkeypatch, declared, step, decoded
):
    source = tmp_path / "native.fseq"
    source.write_bytes(b"native")
    binary = tmp_path / "xLights"
    binary.write_bytes(b"binary")
    layout = tmp_path / "layout.xml"
    layout.write_text("<layout/>")
    xsq = tmp_path / "song.xsq"
    xsq.write_text("<sequence/>")
    media = tmp_path / "song.wav"
    media.write_bytes(b"audio")
    destination = tmp_path / "result.fseq"

    class FakeReader:
        info = SimpleNamespace(frames=declared, step_ms=step)

        def __init__(self, path):
            pass

        def iter_frames(self):
            for _ in range(decoded):
                yield b"frame"

    monkeypatch.setattr(xlights_fseq, "xlights_binary", lambda: binary)
    monkeypatch.setattr(xlights_fseq, "_run_xlights", lambda *args: (source, "2026.19"))
    monkeypatch.setattr(xlights_fseq, "FseqReader", FakeReader)
    with pytest.raises(ValueError, match="no playable frames|frame count mismatch"):
        xlights_fseq.render_sequence_to_fseq(
            layout_xml=layout,
            xsq_path=xsq,
            media_path=media,
            fseq_path=destination,
            show_dir=tmp_path / "show",
        )
    assert not destination.exists()
    assert not receipt_path(destination).exists()


def test_native_render_publishes_verified_frames_and_reuses_cache(tmp_path, monkeypatch):
    source = tmp_path / "native.fseq"
    source.write_bytes(b"verified-native-frames")
    binary = tmp_path / "xLights"
    binary.write_bytes(b"binary")
    layout = tmp_path / "layout.xml"
    layout.write_text("<layout/>")
    xsq = tmp_path / "song.xsq"
    xsq.write_text("<sequence/>")
    media = tmp_path / "song.wav"
    media.write_bytes(b"audio")
    destination = tmp_path / "result.fseq"
    calls = []

    class FakeReader:
        info = SimpleNamespace(frames=3, step_ms=50)

        def __init__(self, path):
            pass

        def iter_frames(self):
            yield b"a"
            yield b"b"
            yield b"c"

    def fake_xlights(*args):
        calls.append(True)
        return source, "2026.19"

    monkeypatch.setattr(xlights_fseq, "xlights_binary", lambda: binary)
    monkeypatch.setattr(xlights_fseq, "_run_xlights", fake_xlights)
    monkeypatch.setattr(xlights_fseq, "FseqReader", FakeReader)
    kwargs = dict(
        layout_xml=layout, xsq_path=xsq, media_path=media,
        fseq_path=destination, show_dir=tmp_path / "show"
    )
    assert xlights_fseq.render_sequence_to_fseq(**kwargs) == "2026.19"
    assert destination.read_bytes() == b"verified-native-frames"
    assert receipt_path(destination).is_file()
    assert xlights_fseq.render_sequence_to_fseq(**kwargs) == "2026.19"
    assert len(calls) == 1


def test_native_render_regenerates_corrupted_cached_fseq(tmp_path, monkeypatch):
    source = tmp_path / "native.fseq"
    source.write_bytes(b"native-good")
    binary = tmp_path / "xLights"
    binary.write_bytes(b"binary")
    layout = tmp_path / "layout.xml"
    layout.write_text("<layout/>")
    xsq = tmp_path / "song.xsq"
    xsq.write_text("<sequence/>")
    media = tmp_path / "song.wav"
    media.write_bytes(b"audio")
    destination = tmp_path / "result.fseq"
    calls = []

    class FakeReader:
        info = SimpleNamespace(frames=1, step_ms=50)

        def __init__(self, path):
            pass

        def iter_frames(self):
            yield b"frame"

    def fake_xlights(*args):
        calls.append(True)
        return source, "2026.19"

    monkeypatch.setattr(xlights_fseq, "xlights_binary", lambda: binary)
    monkeypatch.setattr(xlights_fseq, "_run_xlights", fake_xlights)
    monkeypatch.setattr(xlights_fseq, "FseqReader", FakeReader)
    kwargs = dict(
        layout_xml=layout, xsq_path=xsq, media_path=media,
        fseq_path=destination, show_dir=tmp_path / "show"
    )
    xlights_fseq.render_sequence_to_fseq(**kwargs)
    destination.write_bytes(b"corrupted!!")
    assert xlights_fseq.render_sequence_to_fseq(**kwargs) == "2026.19"
    assert destination.read_bytes() == b"native-good"
    assert len(calls) == 2


def test_native_render_regenerates_receipt_without_version(tmp_path, monkeypatch):
    import json

    source = tmp_path / "native.fseq"
    source.write_bytes(b"native-good")
    binary = tmp_path / "xLights"
    binary.write_bytes(b"binary")
    layout = tmp_path / "layout.xml"
    layout.write_text("<layout/>")
    xsq = tmp_path / "song.xsq"
    xsq.write_text("<sequence/>")
    media = tmp_path / "song.wav"
    media.write_bytes(b"audio")
    destination = tmp_path / "result.fseq"
    calls = []

    class FakeReader:
        info = SimpleNamespace(frames=1, step_ms=50)

        def __init__(self, path):
            pass

        def iter_frames(self):
            yield b"frame"

    def fake_xlights(*args):
        calls.append(True)
        return source, "2026.19"

    monkeypatch.setattr(xlights_fseq, "xlights_binary", lambda: binary)
    monkeypatch.setattr(xlights_fseq, "_run_xlights", fake_xlights)
    monkeypatch.setattr(xlights_fseq, "FseqReader", FakeReader)
    kwargs = dict(
        layout_xml=layout, xsq_path=xsq, media_path=media,
        fseq_path=destination, show_dir=tmp_path / "show"
    )
    xlights_fseq.render_sequence_to_fseq(**kwargs)
    receipt = receipt_path(destination)
    metadata = json.loads(receipt.read_text())
    del metadata["version"]
    receipt.write_text(json.dumps(metadata))
    assert xlights_fseq.render_sequence_to_fseq(**kwargs) == "2026.19"
    assert len(calls) == 2
    assert json.loads(receipt.read_text())["version"] == "2026.19"
