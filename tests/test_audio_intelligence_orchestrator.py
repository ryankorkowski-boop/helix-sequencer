from pathlib import Path

import audio.audio_intelligence_orchestrator as orchestrator


class _FakeEvent:
    timestamp = 1.25
    confidence = 0.8
    velocity = 0.9
    drum_type = "snare"
    cluster_id = 4
    frequency_band_info = {"high_ratio": 0.7}


def test_orchestrator_normalizes_existing_drum_detector(monkeypatch, tmp_path: Path):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not-real-audio")

    monkeypatch.setattr(orchestrator, "_duration_ms", lambda _: 5000)
    monkeypatch.setattr(
        orchestrator,
        "detect_drum_event_streams_from_file",
        lambda *args, **kwargs: {"snare": [_FakeEvent()]},
    )

    result = orchestrator.build_musical_event_map(
        audio,
        config=orchestrator.AudioIntelligenceConfig(use_stem_analysis=False),
    )
    assert result.duration_ms == 5000
    assert result.providers == ["helix.drum_detection"]
    assert len(result.events) == 1
    assert result.events[0].kind == "drum_snare"
    assert result.events[0].time_ms == 1250
    assert result.events[0].confidence == 0.8
    assert result.diagnostics["direct_drum_events_emitted"] == 1
    assert result.diagnostics["fused_events"] == 1


def test_orchestrator_reports_missing_audio(tmp_path: Path):
    result = orchestrator.build_musical_event_map(tmp_path / "missing.wav")
    assert result.duration_ms == 0
    assert result.events == []
    assert "audio_not_found" in result.diagnostics["error"]


def test_orchestrator_exposes_instrument_and_vocal_cues(monkeypatch, tmp_path: Path):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not-real-audio")

    class _Vocal:
        start_ms = 1500
        end_ms = 1800
        confidence = 0.82
        energy = 0.74
        role = "harmony"
        performer_hint = "all_vocalists"
        source_reason = "test_classifier"

    class _Stem:
        source = "test"
        bass_peaks_ms = [500, 1500]
        vocal_peaks_ms = [1000]
        drum_event_streams = {}
        background_vocal_events = [_Vocal()]
        stem_features = {
            "other": {
                "onset_events": [
                    {"time_ms": 700, "confidence": 0.8, "strength": 0.8},
                    {"time_ms": 900, "confidence": 0.7, "strength": 0.7},
                ]
            }
        }

    monkeypatch.setattr(orchestrator, "_duration_ms", lambda _: 3000)
    monkeypatch.setattr(orchestrator, "detect_drum_event_streams_from_file", lambda *args, **kwargs: {})
    monkeypatch.setattr(orchestrator, "build_stem_analysis", lambda *args, **kwargs: _Stem())

    result = orchestrator.build_musical_event_map(audio)
    kinds = {event.kind for event in result.events}

    assert "instrument_pluck" in kinds
    assert "instrument_picking" in kinds
    assert "vocal_onset" in kinds
    assert "vocal_harmony" in kinds
    assert result.diagnostics["instrument_events_emitted"] >= 5
