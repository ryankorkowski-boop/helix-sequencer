from __future__ import annotations

import numpy as np
import pytest

from audio.drummer_v3 import ANALYSIS_HOP_LENGTH, ANALYSIS_N_FFT, ANALYSIS_SAMPLE_RATE, CONTEXT_N_FFT, analyze_drummer_samples
from tools.render_drummer_v3_preview import _active_targets_for_frame, _frame_time_ms

SEEDS = {"kick": 1, "tom_floor": 2, "tom_mid": 3, "tom_high": 4, "snare": 5, "hihat": 6, "cymbal": 7}


def _band_noise(sr: int, duration: float, low_hz: float, high_hz: float, rng: np.random.Generator) -> np.ndarray:
    n = int(round(sr * duration))
    raw = rng.standard_normal(n)
    spectrum = np.fft.rfft(raw)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    spectrum[(freqs < low_hz) | (freqs > high_hz)] = 0.0
    signal = np.fft.irfft(spectrum, n=n)
    return signal / max(float(np.max(np.abs(signal))), 1e-9)


def _isolated_hit(sr: int, kind: str, *, onset: float = 0.300) -> np.ndarray:
    y = np.zeros(int(round(sr * 1.2)), dtype=np.float32)
    rng = np.random.default_rng(SEEDS[kind])
    start = int(round(onset * sr))
    if kind == "kick":
        duration = 0.22; t = np.arange(int(sr * duration)) / sr
        hit = (np.sin(2 * np.pi * 70 * t) + 0.35 * np.sin(2 * np.pi * 110 * t)) * np.exp(-t * 20)
    elif kind == "tom_floor":
        duration = 0.25; t = np.arange(int(sr * duration)) / sr
        hit = (np.sin(2*np.pi*130*t) + 0.80*np.sin(2*np.pi*260*t) + 0.35*np.sin(2*np.pi*390*t)) * np.exp(-t*13)
    elif kind == "tom_mid":
        duration = 0.22; t = np.arange(int(sr * duration)) / sr
        hit = (0.40*np.sin(2*np.pi*180*t) + np.sin(2*np.pi*310*t) + 0.55*np.sin(2*np.pi*520*t)) * np.exp(-t*15)
    elif kind == "tom_high":
        duration = 0.20; t = np.arange(int(sr * duration)) / sr
        hit = (0.90*np.sin(2*np.pi*480*t) + 0.50*np.sin(2*np.pi*760*t)) * np.exp(-t*18)
    elif kind == "snare":
        duration = 0.16; t = np.arange(int(sr * duration)) / sr
        hit = 0.35*np.sin(2*np.pi*210*t)*np.exp(-t*26) + _band_noise(sr,duration,600,3000,rng)*np.exp(-t*28)
    elif kind == "hihat":
        duration = 0.07; t = np.arange(int(sr * duration)) / sr
        hit = _band_noise(sr,duration,5000,14000,rng)*np.exp(-t*65)
    elif kind == "cymbal":
        duration = 0.65; t = np.arange(int(sr * duration)) / sr
        hit = _band_noise(sr,duration,4000,14000,rng)*np.exp(-t*5.5)
    else:
        raise ValueError(kind)
    hit = np.asarray(hit, dtype=np.float32)
    y[start:start + len(hit)] += hit[: len(y) - start]
    return y


@pytest.mark.parametrize(("kind","expected_type","tom_class"), [
    ("kick","kick",None), ("snare","snare",None), ("hihat","hihat",None), ("cymbal","cymbal",None),
    ("tom_floor","tom","floor"), ("tom_mid","tom","mid"), ("tom_high","tom","high"),
])
def test_isolated_hits_keep_identity_remove_release_edges_and_refine_attack(kind, expected_type, tom_class) -> None:
    events, diagnostics = analyze_drummer_samples(_isolated_hit(44100, kind), 44100)
    typed = [event for event in events if event.drum_type == expected_type]
    assert len(events) == len(typed) == 1, [(event.timestamp, event.drum_type) for event in events]
    event = typed[0]
    assert abs(event.timestamp - 0.300) <= 0.002
    assert float(event.frequency_band_info["attack_contrast"]) >= 1.05
    if tom_class is not None:
        assert event.frequency_band_info["tom_class"] == tom_class
    assert diagnostics["analysis_sample_rate"] == ANALYSIS_SAMPLE_RATE
    assert diagnostics["analysis_hop_length"] == ANALYSIS_HOP_LENGTH
    assert diagnostics["analysis_n_fft"] == ANALYSIS_N_FFT
    assert diagnostics["context_n_fft"] == CONTEXT_N_FFT


@pytest.mark.parametrize("kind", list(SEEDS))
def test_44100_and_48000_sources_converge(kind: str) -> None:
    first, first_diag = analyze_drummer_samples(_isolated_hit(44100, kind), 44100)
    second, second_diag = analyze_drummer_samples(_isolated_hit(48000, kind), 48000)
    signature = lambda rows: [(event.drum_type, event.frequency_band_info.get("tom_class")) for event in rows]
    assert signature(first) == signature(second)
    assert len(first) == len(second) == 1
    assert abs(first[0].timestamp - second[0].timestamp) <= 0.002
    assert first_diag["source_sample_rate"] == 44100
    assert second_diag["source_sample_rate"] == 48000
    assert first_diag["analysis_sample_rate"] == second_diag["analysis_sample_rate"] == 44100


def test_60fps_preview_uses_nearest_frame_for_hit_start() -> None:
    start_ms, event_ms, fps = 9500, 10990, 60
    frame_index = round((event_ms - start_ms) * fps / 1000.0)
    frame_ms = _frame_time_ms(start_ms, frame_index, fps)
    assert abs(frame_ms - event_ms) <= 500.0 / fps
    target = "HX_SNOWMAN_DRUMMER_V3_KICK"
    assert target in _active_targets_for_frame([(event_ms, event_ms + 150, target)], frame_ms, fps)
