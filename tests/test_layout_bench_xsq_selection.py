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
