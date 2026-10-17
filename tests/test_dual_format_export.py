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


def test_cli_xsq_copy(tmp_path, capsys):
    from tools.dual_format_export import main
    source = tmp_path / 'source.xsq'
    source.write_text('<xsequence/>')
    output = tmp_path / 'generated'
    assert main([str(source), str(output), '--format', 'xsq']) == 0
    assert (output / 'Performance.xsq').read_text() == '<xsequence/>'
    assert 'Performance.xsq' in capsys.readouterr().out


def test_existing_lms_sidecar_is_never_deleted(tmp_path):
    source = tmp_path / 'source.xsq'
    source.write_text('<xsequence/>')
    destination = tmp_path / 'output'
    destination.mkdir()
    sidecar = destination / 'Performance.lms_validation.json'
    sidecar.write_text('approved evidence')
    with pytest.raises(FileExistsError, match='sidecar'):
        export_from_xsq(source, destination, output_format='both', mapping_csv=tmp_path / 'unused.csv')
    assert sidecar.read_text() == 'approved evidence'
    assert not (destination / 'Performance.xsq').exists()


def test_source_named_performance_xsq_is_preserved(tmp_path):
    source = tmp_path / 'Performance.xsq'
    original = '<xsequence>keep me</xsequence>'
    source.write_text(original)
    with pytest.raises(ValueError, match='Input XSQ'):
        export_from_xsq(source, tmp_path, output_format='xsq')
    assert source.read_text() == original
