"""Regression checks for authenticated sampler vocal evidence fail-closed policy."""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "tools/build_sampler_technical_pilot.py"


def test_sampler_builder_parses():
    ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_vocal_evidence_requires_independent_verification():
    source = SOURCE.read_text(encoding="utf-8")
    assert "verification_status" in source
    assert "independently_verified" in source
    assert "source_audio_sha256" in source
    assert "duration_seconds" in source
    assert "No independently isolated sampler singers" in source


def test_singer_cues_require_canonical_submodel_and_role():
    source = SOURCE.read_text(encoding="utf-8")
    assert "part not in model.submodels" in source
    assert "event['role']!=role" in source
    assert "0<=start<end<=256000" in source
