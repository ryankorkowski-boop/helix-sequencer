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

    result = orchestrator.build_musical_event_map(audio)
    assert result.duration_ms == 5000
    assert result.providers == ["helix.drum_detection"]
    assert len(result.events) == 1
    assert result.events[0].kind == "drum_snare"
    assert result.events[0].time_ms == 1250
    assert result.events[0].confidence == 0.8
    assert result.diagnostics["drum_events_emitted"] == 1


def test_orchestrator_reports_missing_audio(tmp_path: Path):
    result = orchestrator.build_musical_event_map(tmp_path / "missing.wav")
    assert result.duration_ms == 0
    assert result.events == []
    assert "audio_not_found" in result.diagnostics["error"]
