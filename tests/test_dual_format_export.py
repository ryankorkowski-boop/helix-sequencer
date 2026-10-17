"""Tests for the existing legacy LMS converter bridge."""
from pathlib import Path
import pytest
from tools.dual_format_export import export_from_xsq


def test_xsq_only_copies_source_without_mapping(tmp_path):
    source = tmp_path / "original.xsq"
    source.write_text("<xsequence/>")
    results = export_from_xsq(source, tmp_path / "output", output_format="xsq")
    assert results["xsq"].read_bytes() == source.read_bytes()


def test_both_requires_explicit_controller_mapping(tmp_path):
    source = tmp_path / "original.xsq"
    source.write_text("<xsequence/>")
    with pytest.raises(ValueError, match="mapping CSV"):
        export_from_xsq(source, tmp_path / "output", output_format="both")
    assert not (tmp_path / "output").exists()


def test_existing_output_never_overwritten(tmp_path):
    source = tmp_path / "original.xsq"
    source.write_text("<xsequence/>")
    target = tmp_path / "output"
    target.mkdir()
    (target / "Performance.xsq").write_text("old")
    with pytest.raises(FileExistsError):
        export_from_xsq(source, target, output_format="xsq")
    assert (target / "Performance.xsq").read_text() == "old"


def test_missing_source_fails_before_output(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_from_xsq(tmp_path / "missing.xsq", tmp_path / "output", output_format="xsq")
