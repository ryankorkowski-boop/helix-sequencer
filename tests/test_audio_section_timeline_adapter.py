import hashlib
import json

import pytest

from core.audio_section_timeline_adapter import timeline_from_audio_analysis
from core.effects_orchestrator_bridge import build_seed_graph
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
