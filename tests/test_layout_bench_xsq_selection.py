"""Regression coverage for strict canonical layout-bench XSQ selection."""
from pathlib import Path

import pytest

from tools.layout_bench.render_comparisons import find_xsq


def _folder(tmp_path: Path) -> Path:
    folder = tmp_path / "ac16_lor"
    folder.mkdir()
    return folder


def test_exact_song_stem_not_prefix(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Bells of Mathmas Remix,auto.xsq").write_text("other")
    expected = folder / "Bells of Mathmas,auto.xsq"
    expected.write_text("correct")
    assert find_xsq(tmp_path, "ac16_lor", "Bells of Mathmas") == expected


def test_glob_metacharacters_are_literal(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Song A,auto.xsq").write_text("wrong")
    expected = folder / "Song [A],auto.xsq"
    expected.write_text("correct")
    assert find_xsq(tmp_path, "ac16_lor", "Song [A]") == expected


def test_ambiguous_canonical_sequences_fail_closed(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Track,auto.xsq").write_text("one")
    (folder / "Track,alternate.xsq").write_text("two")
    with pytest.raises(ValueError, match="Ambiguous canonical XSQ"):
        find_xsq(tmp_path, "ac16_lor", "Track")


def test_orchestrated_sidecar_is_not_canonical(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Track,orchestrated.xsq").write_text("sidecar")
    expected = folder / "Track,auto.xsq"
    expected.write_text("canonical")
    assert find_xsq(tmp_path, "ac16_lor", "Track") == expected


def test_missing_sequence_fails(tmp_path):
    _folder(tmp_path)
    with pytest.raises(FileNotFoundError, match="No canonical XSQ"):
        find_xsq(tmp_path, "ac16_lor", "Missing")


def test_stitch_rejects_incomplete_panel_count(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    with pytest.raises(ValueError, match="9, 12 or 16"):
        stitch_panels([], tmp_path / "song.mp3", tmp_path / "out.mp4", "Title", "Description")


def test_stitch_rejects_missing_panel_before_encoding(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"placeholder")
    with pytest.raises(FileNotFoundError, match="Missing comparison panel"):
        stitch_panels([tmp_path / f"panel_{i}.mp4" for i in range(9)], soundtrack, tmp_path / "out.mp4", "Title", "Description")


def test_stitch_rejects_missing_soundtrack_before_encoding(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"placeholder")
    with pytest.raises(FileNotFoundError, match="Missing comparison soundtrack"):
        stitch_panels(panels, tmp_path / "missing.mp3", tmp_path / "out.mp4", "Title", "Description")


def test_failed_comparison_encode_preserves_previous_mp4(tmp_path, monkeypatch):
    import subprocess
    from tools.layout_bench import render_comparisons as comparisons

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"panel")
    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"audio")
    destination = tmp_path / "approved.mp4"
    destination.write_bytes(b"previous valid video")

    def fail_encode(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stderr=b"simulated failure")

    monkeypatch.setattr(comparisons, "_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(comparisons.subprocess, "run", fail_encode)
    with pytest.raises(RuntimeError, match="Comparison encode"):
        comparisons.stitch_panels(panels, soundtrack, destination, "Title", "Description")

    assert destination.read_bytes() == b"previous valid video"
    assert not list(tmp_path.glob("*.banner.png"))
    assert not list(tmp_path.glob("tmp*/comparison.mp4"))
