from pathlib import Path

import numpy as np

from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams


def test_raw_mix_kick_evidence_is_recorded():
    sr = 48_000
    t = np.arange(sr, dtype=np.float32) / sr
    kick = np.exp(-t * 45.0) * np.sin(2 * np.pi * 70 * t)
    streams = detect_drum_event_streams(kick, sr, DrumDetectionConfig())
    events = streams["kick_events"]
    assert events
    assert any("raw_kick_low01" in e.frequency_band_info for e in events)


def test_detection_preserves_independent_stream_keys():
    streams = detect_drum_event_streams(np.zeros(48_000, dtype=np.float32), 48_000)
    assert set(streams) == {
        "kick_events", "snare_events", "tom_events", "hihat_events", "cymbal_events", "drum_bus_events"
    }
