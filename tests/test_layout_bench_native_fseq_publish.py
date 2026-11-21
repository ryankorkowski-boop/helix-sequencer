"""Fail-closed validation for native xLights FSEQ cache publication."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.layout_bench import xlights_fseq


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
    assert not xlights_fseq.receipt_path(destination).exists()
