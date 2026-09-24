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


def test_orchestrator_adds_musical_salience_and_adaptive_timing(monkeypatch, tmp_path: Path):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not-real-audio")

    class _Kick:
        timestamp = 1.0
        confidence = 0.9
        velocity = 0.85
        drum_type = "kick"
        cluster_id = 1
        frequency_band_info = {}

    class _Snare:
        timestamp = 1.03
        confidence = 0.8
        velocity = 0.9
        drum_type = "snare"
        cluster_id = 2
        frequency_band_info = {}

    monkeypatch.setattr(orchestrator, "_duration_ms", lambda _: 3000)
    monkeypatch.setattr(
        orchestrator,
        "detect_drum_event_streams_from_file",
        lambda *args, **kwargs: {"drums": [_Kick(), _Snare()]},
    )

    result = orchestrator.build_musical_event_map(
        audio,
        config=orchestrator.AudioIntelligenceConfig(
            use_stem_analysis=False,
            chord_grouping=False,
        ),
    )

    assert result.events
    assert all("musical_importance" in event.metadata for event in result.events)
    assert result.diagnostics["adaptive_timing_events"] >= 1
    assert result.diagnostics["musical_intelligence"]["important_event_count"] >= 1


def test_chord_grouping_preserves_polyphony():
    from audio.musical_event_model import MusicalEvent
    from audio.musical_intelligence import detect_chord_groups

    events = [
        MusicalEvent(1000, "note", 0.9, 0.8, pitch_midi=60, instrument="keyboard"),
        MusicalEvent(1010, "note", 0.85, 0.75, pitch_midi=64, instrument="keyboard"),
        MusicalEvent(1020, "note", 0.88, 0.72, pitch_midi=67, instrument="keyboard"),
    ]

    chords = detect_chord_groups(events)
    assert len(chords) == 1
    assert chords[0].kind == "harmony_chord"
    assert chords[0].metadata["pitches_midi"] == [60, 64, 67]


def test_orchestrator_imports_canonical_notes_and_beats(monkeypatch, tmp_path: Path):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not-real-audio")

    class _Beat:
        time_ms = 1000
        confidence = 0.91
        strength = 0.88
        label = "beat"
        metadata = {"downbeat": True}

    class _Note:
        timestamp_ms = 1010
        duration_ms = 180
        pitch_hz = 261.63
        midi_note = 60
        note_name = "C4"
        velocity = 0.84
        confidence = 0.93
        source_stem = "mix_harmonic"

    class _Analysis:
        beat_events = [_Beat()]
        note_events = [_Note()]

    monkeypatch.setattr(orchestrator, "_duration_ms", lambda _: 2000)
    monkeypatch.setattr(orchestrator, "detect_drum_event_streams_from_file", lambda *args, **kwargs: {})
    monkeypatch.setattr(orchestrator, "analyze_audio_file", lambda *args, **kwargs: _Analysis())

    result = orchestrator.build_musical_event_map(
        audio,
        config=orchestrator.AudioIntelligenceConfig(
            use_stem_analysis=False,
            adaptive_timing=True,
            chord_grouping=False,
        ),
    )

    notes = [event for event in result.events if event.kind == "note_event"]
    beats = [event for event in result.events if event.kind == "beat_downbeat"]
    assert len(notes) == 1
    assert notes[0].pitch_midi == 60
    assert notes[0].metadata["note_name"] == "C4"
    assert len(beats) == 1
    assert beats[0].metadata["downbeat"] is True
    assert result.diagnostics["canonical_note_events_imported"] == 1
    assert result.diagnostics["canonical_timing_events_imported"] == 1
    assert result.diagnostics["beat_map_available"] is True
