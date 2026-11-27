import hashlib
import json

import pytest

from core.audio_section_timeline_adapter import timeline_from_audio_analysis
from core.effects_orchestrator_bridge import build_seed_graph, run_effects_orchestration
from core.engine_activation_audit import build_engine_activation_audit
from core.sequence_builder import _clean_engine_args
from core.song_section_choreography import load_song_section_graph


def _analysis(tmp_path, *, reason="spectral_novelty", confidence=0.9, digest=None):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"small audio fixture")
    sha = hashlib.sha256(audio.read_bytes()).hexdigest()
    path = tmp_path / "audio_analysis.json"
    path.write_text(json.dumps({
        "metadata": {
            "analysis_schema": "helix.audio_analysis.v1",
            "duration_ms": 42000,
            "audio_path": str(audio),
            "audio_sha256": sha if digest is None else digest,
        },
        "section_events": [
            {"start_ms": 0, "end_ms": 7000, "section_type": "intro", "strength": 0.2, "confidence": confidence, "reason": reason},
            {"start_ms": 7000, "end_ms": 42000, "section_type": "chorus", "strength": 0.9, "confidence": confidence, "reason": reason},
        ],
    }), encoding="utf-8")
    return path, audio


def test_adapts_matching_audio_and_preserves_real_section_times(tmp_path):
    path, audio = _analysis(tmp_path)
    payload = timeline_from_audio_analysis(path, audio)
    assert payload["duration_seconds"] == 42
    assert payload["sections"][0]["end_seconds"] == 7
    assert payload["sections"][1]["start_seconds"] == 7
    timeline = tmp_path / "timeline.json"
    timeline.write_text(json.dumps(payload), encoding="utf-8")
    graph = load_song_section_graph(timeline, build_seed_graph())
    assert len(graph.intents) == 2
    assert graph.end == 42


@pytest.mark.parametrize("reason,confidence", [
    ("energy_curve_fallback", 0.9),
    ("tail_fill", 0.9),
    ("spectral_novelty", 0.52),
])
def test_rejects_fallback_and_low_confidence(tmp_path, reason, confidence):
    path, audio = _analysis(tmp_path, reason=reason, confidence=confidence)
    with pytest.raises(ValueError, match="fallback or low-confidence"):
        timeline_from_audio_analysis(path, audio)


def test_rejects_wrong_audio_hash(tmp_path):
    path, audio = _analysis(tmp_path, digest="0" * 64)
    with pytest.raises(ValueError, match="SHA-256"):
        timeline_from_audio_analysis(path, audio)


def test_qualified_sibling_analysis_feeds_nine_pass(tmp_path):
    path, audio = _analysis(tmp_path)
    report = run_effects_orchestration([
        "--audio", str(audio), "--output-dir", str(tmp_path / "out"),
    ], write_report=False)
    assert report.invoked is True, report.error
    assert report.section_timeline_source == "audio_analysis"
    assert report.section_timeline_error is None
    assert report.input_intents == 2
    audit = build_engine_activation_audit(["--audio", str(audio)], report)
    orch = audit["engines"]["nine_pass_orchestrator"]
    assert orch["source_sections_validated"] is True
    assert orch["synthetic_seed_only"] is False


def test_low_confidence_analysis_stays_on_the_seed(tmp_path):
    _path, audio = _analysis(tmp_path, confidence=0.52)
    report = run_effects_orchestration([
        "--audio", str(audio), "--output-dir", str(tmp_path / "out"),
    ], write_report=False)
    assert report.invoked is True, report.error
    assert report.section_timeline_source == "synthetic_seed"
    assert report.input_intents == 5
    assert "low-confidence" in report.section_timeline_error
    audit = build_engine_activation_audit(["--audio", str(audio)], report)
    assert audit["engines"]["nine_pass_orchestrator"]["source_sections_validated"] is False


def test_explicit_section_timeline_wins_over_sibling_analysis(tmp_path):
    _analysis(tmp_path, confidence=0.52)
    audio = tmp_path / "song.wav"
    timeline = tmp_path / "sections.json"
    payload = {
        "source": "verified_manual",
        "duration_seconds": 42,
        "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
        "sections": [
            {"label": "verse", "start_seconds": 0, "end_seconds": 42, "energy": 0.4},
        ],
    }
    timeline.write_text(json.dumps(payload), encoding="utf-8")
    report = run_effects_orchestration([
        "--audio", str(audio),
        "--orchestration-sections-json", str(timeline),
        "--output-dir", str(tmp_path / "out"),
    ], write_report=False)
    assert report.invoked is True, report.error
    assert report.section_timeline_source == "orchestration-sections-json"
    assert report.input_intents == 1


def test_audio_analysis_flag_is_not_forwarded_to_the_effect_engine():
    args = ["--audio", "song.wav", "--audio-analysis-json", "audio_analysis.json", "--polish"]
    assert _clean_engine_args(args) == ["--audio", "song.wav", "--polish"]
