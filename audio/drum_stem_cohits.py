"""Kick and snare recovery on a separated drum stem.

This pass is only valid for a Demucs or Moises drum stem. It does not run on
the full mix or on a local HPSS substitute.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from audio.drum_classification import DrumEvent

SOURCE = "v3_stem_multiband_cohit"


@dataclass(frozen=True)
class StemCohitConfig:
    sample_rate: int = 44100
    hop: int = 441
    n_fft: int = 4096
    kick_band: tuple[float, float] = (40.0, 100.0)
    snare_body_band: tuple[float, float] = (160.0, 300.0)
    snare_wire_band: tuple[float, float] = (2000.0, 5000.0)
    kick_rise_db: float = 10.0
    snare_body_rise_db: float = 9.0
    snare_wire_rise_db: float = 6.0
    level_window_db: float = 12.0
    kick_dominance_db: float = 0.0
    reference_ms: int = 120
    min_gap_ms: int = 110
    pair_tolerance_ms: int = 20
    dedupe_ms: int = 60


def _band_rise(spec, freqs, band, ref_frames):
    from scipy.ndimage import minimum_filter1d
    lo, hi = band
    energy = 10.0 * np.log10(spec[(freqs >= lo) & (freqs < hi)].sum(axis=0) + 1e-10)
    floor = minimum_filter1d(energy, ref_frames, origin=(ref_frames - 1) // 2)
    return energy, energy - floor


def _peaks(rise, energy, threshold, window_db, wait):
    import librosa
    picks = librosa.util.peak_pick(rise, pre_max=4, post_max=4, pre_avg=4, post_avg=4, delta=0.5, wait=wait)
    loud = np.percentile(energy, 90) - window_db
    return np.asarray([p for p in picks if rise[p] >= threshold and energy[p] >= loud], dtype=int)


def detect_stem_cohits(y, sr, existing=(), config: StemCohitConfig = StemCohitConfig()):
    import librosa
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    report = {
        "method": SOURCE,
        "config": asdict(config),
        "added": {"kick": 0, "snare": 0},
        "measured": {"kick": 0, "snare": 0},
        "deduped": {"kick": 0, "snare": 0},
    }
    if y.size == 0 or sr <= 0 or y.size < config.n_fft:
        return [], report
    if sr != config.sample_rate:
        y = librosa.resample(y, orig_sr=sr, target_sr=config.sample_rate)
        sr = config.sample_rate
    spec = np.abs(librosa.stft(y, n_fft=config.n_fft, hop_length=config.hop)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=config.n_fft)
    frame_ms = 1000.0 * config.hop / sr
    ref = max(2, round(config.reference_ms / frame_ms))
    wait = max(1, round(config.min_gap_ms / frame_ms))
    k_energy, k_rise = _band_rise(spec, freqs, config.kick_band, ref)
    b_energy, b_rise = _band_rise(spec, freqs, config.snare_body_band, ref)
    w_energy, w_rise = _band_rise(spec, freqs, config.snare_wire_band, ref)
    kicks = _peaks(k_rise, k_energy, config.kick_rise_db, config.level_window_db, wait)
    kicks = np.asarray([k for k in kicks if k_energy[k] >= b_energy[k] + config.kick_dominance_db], dtype=int)
    bodies = _peaks(b_rise, b_energy, config.snare_body_rise_db, config.level_window_db, wait)
    wires = _peaks(w_rise, w_energy, config.snare_wire_rise_db, config.level_window_db, wait)
    tol = max(1, round(config.pair_tolerance_ms / frame_ms))
    snares = np.asarray([b for b in bodies if wires.size and np.min(np.abs(wires - b)) <= tol], dtype=int)
    report["measured"] = {"kick": int(kicks.size), "snare": int(snares.size)}
    have = {"kick": [], "snare": []}
    for event in existing:
        if event.drum_type in have:
            have[event.drum_type].append(event.timestamp_ms)
    added = []
    for family, frames, energy, rise in (("kick", kicks, k_energy, k_rise), ("snare", snares, b_energy, b_rise)):
        loud = float(np.percentile(energy, 99)) if energy.size else 0.0
        prior = np.asarray(sorted(have[family]), dtype=float)
        for index, frame in enumerate(frames):
            ms = frame * frame_ms
            if prior.size and np.min(np.abs(prior - ms)) <= config.dedupe_ms:
                report["deduped"][family] += 1
                continue
            velocity = float(np.clip(1.0 + (energy[frame] - loud) / 24.0, 0.12, 1.0))
            confidence = float(np.clip(0.45 + rise[frame] / 60.0, 0.45, 0.9))
            info = {
                "stem_cohit": 1.0,
                "band_rise_db": round(float(rise[frame]), 2),
                "band_level_db": round(float(energy[frame]), 2),
            }
            added.append(DrumEvent(
                round(ms / 1000.0, 4), round(velocity, 3), round(confidence, 3),
                info, -1, family, SOURCE,
            ))
            report["added"][family] += 1
    added.sort(key=lambda event: event.timestamp)
    return added, report
