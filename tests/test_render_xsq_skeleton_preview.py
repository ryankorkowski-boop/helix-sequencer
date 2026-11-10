from __future__ import annotations

from pathlib import Path

from tools.export_demo_xsq import export_demo_xsq
from tools.render_xsq_skeleton_preview import parse_skeleton_xsq, render_skeleton_preview


def test_parse_skeleton_xsq_reads_demo_export(tmp_path: Path) -> None:
    xsq = export_demo_xsq(tmp_path / "demo.xsq")

    sequence_name, model_name, events = parse_skeleton_xsq(xsq)

    assert sequence_name == "HelixDemoVocal"
    assert model_name == "HX_SNOWMAN_SINGER"
    assert events
    assert events == sorted(events, key=lambda item: (item.start, item.index, item.performer, item.phoneme))
    assert all(event.duration > 0 for event in events)
    assert all(0.0 <= event.intensity <= 1.0 for event in events)


def test_render_skeleton_preview_creates_mp4(tmp_path: Path) -> None:
    xsq = export_demo_xsq(tmp_path / "demo.xsq")

    mp4 = render_skeleton_preview(xsq, width=320, height=180, fps=6)

    assert mp4.exists()
    assert mp4.suffix == ".mp4"
    assert mp4.stat().st_size > 0


def test_render_skeleton_preview_is_repeatable_pathwise(tmp_path: Path) -> None:
    xsq = export_demo_xsq(tmp_path / "demo.xsq")

    first = render_skeleton_preview(xsq, width=320, height=180, fps=6)
    first_size = first.stat().st_size
    second = render_skeleton_preview(xsq, width=320, height=180, fps=6)

    assert second == first
    assert second.exists()
    assert second.stat().st_size == first_size
