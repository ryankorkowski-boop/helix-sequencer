"""Numeric pitch-selection and confidence regressions, independent of loop layout."""
from types import SimpleNamespace

import numpy as np
import pytest

from core import audio_intelligence as ai


def pitch_fixture(monkeypatch, magnitudes, frequencies=None):
    magnitudes = np.asarray(magnitudes, dtype=np.float32)
    if frequencies is None:
        frequencies = np.full_like(magnitudes, 440.0)
    monkeypatch.setattr(ai.bounded_audio, "hpss", lambda y, sr: (y, y))
    monkeypatch.setattr(ai, "librosa", SimpleNamespace(
        stft=lambda *args, **kwargs: np.ones_like(magnitudes),
        piptrack=lambda **kwargs: (np.asarray(frequencies), magnitudes),
        frames_to_time=lambda frames, **kwargs: frames / 100.0,
        hz_to_midi=lambda hz: 69 + 12 * np.log2(hz / 440.0),
    ))


def test_confidence_uses_one_global_peak_and_preserves_note_timing(monkeypatch):
    pitch_fixture(monkeypatch, [[2, 4, 3, 1, 0], [1, 1, 2, 0, 0]])
    reductions = []

    class ObservedNumpy:
        def __getattr__(self, name):
            return getattr(np, name)

        def max(self, values):
            reductions.append(np.shape(values))
            return np.max(values)

    monkeypatch.setattr(ai, "np", ObservedNumpy())
    notes, raw = ai._extract_note_candidates(
        np.zeros(512), 22050, source_stem="piano", config=ai.AudioAnalysisConfig())
    assert reductions == [(5,)]  # one global reduction of bounded frame peaks
    assert [item["confidence"] for item in raw] == [.5, 1., .75, .25]
    assert len(notes) == 1
    assert (notes[0].timestamp_ms, notes[0].duration_ms, notes[0].midi_note) == (0, 110, 69)
    assert notes[0].velocity == notes[0].confidence == 1.
    assert notes[0].source_stem == "piano"


def test_nonfinite_magnitudes_do_not_hide_valid_frequency_bins(monkeypatch):
    pitch_fixture(monkeypatch, [[np.nan, np.inf, 0, -1], [2, 1, 0, -2]],
                  [[440, 440, 440, 440], [880, 880, 880, 880]])
    notes, raw = ai._extract_note_candidates(
        np.zeros(512), 22050, source_stem="guitar", config=ai.AudioAnalysisConfig())
    assert [item["time_ms"] for item in raw] == [0, 10]
    assert [item["midi_note"] for item in raw] == [81, 81]
    assert [item["confidence"] for item in raw] == [1., .5]
    assert len(notes) == 1 and notes[0].midi_note == 81


@pytest.mark.parametrize("hz", [np.nan, np.inf, -1., 0.])
def test_invalid_frequency_cannot_produce_midi_or_note(monkeypatch, hz):
    pitch_fixture(monkeypatch, [[1, 2]], [[hz, hz]])
    notes, raw = ai._extract_note_candidates(
        np.zeros(512), 22050, source_stem="other", config=ai.AudioAnalysisConfig())
    assert notes == raw == []


@pytest.mark.parametrize("magnitudes", [np.zeros((2, 5)), np.zeros((0, 5)),
                                         np.zeros((2, 0)), np.full((2, 5), np.nan)])
def test_silence_empty_and_invalid_spectra_do_not_fabricate_notes(monkeypatch, magnitudes):
    pitch_fixture(monkeypatch, magnitudes)
    notes, raw = ai._extract_note_candidates(
        np.zeros(512), 22050, source_stem="piano", config=ai.AudioAnalysisConfig())
    assert notes == raw == []
