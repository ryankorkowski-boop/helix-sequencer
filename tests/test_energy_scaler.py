from __future__ import annotations

from core.energy_scaler import scale_section_intensity
from core.band_vocal_face_export import VocalPhonemeTiming


def _make_timing(intensity: float) -> VocalPhonemeTiming:
    return VocalPhonemeTiming(
        performer="singer",
        phoneme="AH",
        start=0.0,
        duration=1.0,
        intensity=intensity,
    )


def test_zero_energy_mutes():
    timings = [_make_timing(1.0)]
    scaled = scale_section_intensity(timings, 0.0)
    assert scaled[0].intensity == 0.0


def test_full_energy_unchanged():
    timings = [_make_timing(0.75)]
    scaled = scale_section_intensity(timings, 1.0)
    assert scaled[0].intensity == 0.75


def test_mid_energy_scales():
    timings = [_make_timing(0.8)]
    scaled = scale_section_intensity(timings, 0.5)
    assert scaled[0].intensity == 0.4


def test_energy_clamped_above_one():
    timings = [_make_timing(0.6)]
    scaled = scale_section_intensity(timings, 5.0)
    assert scaled[0].intensity == 0.6


def test_deterministic_output():
    timings = [_make_timing(0.9)]
    first = scale_section_intensity(timings, 0.3)
    second = scale_section_intensity(timings, 0.3)
    assert first == second
