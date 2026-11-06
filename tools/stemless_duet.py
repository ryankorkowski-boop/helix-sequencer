"""Conservative, opt-in stemless duet estimates from a verified mixed recording.

This is *not* vocal identity separation or evidence of an independent singer.
Only generate a second mouth lane when existing vocal activity and two distinct
persistent pitch tracks coincide. Never claim these estimates are stems.
"""
from __future__ import annotations

import numpy as np
import librosa
from models.band_sampler_logic import SHAPE_NAMES


def estimate_duet(audio, source_energy, source_shapes, *, frames=720, sr=12000,
                  frame_ms=50):
    """Return two source-clock mouth lanes, energies and an auditable estimate.

    The original source vocal lane gates every event. Pitch evidence can
    suppress or support the harmony lane, but cannot manufacture activity in
    instrumental or silent intervals absent from that source vocal gate.
    """
    source_energy = np.asarray(source_energy, dtype=np.float32)
    source_shapes = np.asarray(source_shapes)
    if (not isinstance(frames, (int, np.integer)) or frames < 1
            or frame_ms not in (10, 25, 50)):
        raise ValueError("Expected positive frames and a 10, 25 or 50 ms source clock")
    if source_energy.ndim != 2 or source_energy.shape[1] != 2 or source_shapes.shape != source_energy.shape:
        raise ValueError("Expected two original source vocal lanes")
    if len(source_energy) != frames:
        raise ValueError("Original source frame count mismatch")
    if not np.isfinite(source_energy).all() or np.any(source_energy < 0):
        raise ValueError("Invalid source vocal energy")
    if (not np.isfinite(source_shapes).all()
            or np.any(source_shapes != np.floor(source_shapes))
            or np.any(source_shapes < 0) or np.any(source_shapes >= len(SHAPE_NAMES))):
        raise ValueError("Invalid source mouth shapes")
    y, rate = librosa.load(str(audio), sr=sr, mono=True)
    hop = max(1, round(rate * frame_ms / 1000))
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    pitch, mag = librosa.piptrack(S=spec, sr=rate, fmin=130, fmax=1050, threshold=.15)
    confidence = np.zeros(frames, dtype=np.float32)
    # Index by source time, not repeated rounded-hop increments. 11025/20 is
    # fractional and previously accumulated clock drift on longer recordings.
    columns = np.rint(np.arange(frames) * frame_ms * rate / (1000 * hop)).astype(int)
    in_audio = np.arange(frames) * frame_ms / 1000 < len(y) / rate
    for i in np.flatnonzero(in_audio & (columns < pitch.shape[1])):
        column = columns[i]
        candidates = np.flatnonzero((pitch[:, column] > 0) & (mag[:, column] > 0))
        if len(candidates) < 2:
            continue
        ordered = candidates[np.argsort(mag[candidates, column])[::-1]]
        strongest = float(mag[ordered[0], column])
        first = float(pitch[ordered[0], column])
        for idx in ordered[1:]:
            second = float(pitch[idx, column])
            semitones = abs(12 * np.log2(second / first))
            # Avoid octave harmonics and adjacent bins from the same voice.
            if 2.0 <= semitones <= 10.0 and abs(semitones - 12.0) > 1.0:
                confidence[i] = min(1.0, float(mag[idx, column]) / max(strongest, 1e-9))
                break
    # Require 150 ms of evidence at either native pose or acoustic-cache rate.
    # Full convolution + explicit crop also preserves one-frame input shape.
    window = int(np.ceil(150 / frame_ms))
    counts = np.convolve((confidence >= .30).astype(int), np.ones(window, dtype=int), mode="full")
    persistent = counts[(window - 1)//2:(window - 1)//2 + frames] == window
    lead = np.clip(source_energy[:, 0], 0, 1)
    vocal_gate = (lead > .12) & (source_shapes[:, 0] != 0) & in_audio
    second = vocal_gate & persistent
    energy = np.zeros((frames, 2), dtype=np.float32)
    shapes = np.zeros((frames, 2), dtype=source_shapes.dtype)
    energy[:, 0] = np.where(vocal_gate, lead, 0)
    shapes[:, 0] = np.where(vocal_gate, source_shapes[:, 0], 0)
    energy[:, 1] = np.where(second, np.minimum(lead * .75, confidence), 0)
    # Reuse the estimated shared syllable shape; this is not phoneme
    # identification for the second singer.
    shapes[:, 1] = np.where(second, source_shapes[:, 0], 0)
    return energy, shapes, {
        "mode": "stemless_mixed_audio_estimate",
        "independent_voice_identity_proven": False,
        "independent_vocal_stems": False,
        "frame_ms": frame_ms,
        "frames": int(frames),
        "persistence_ms": window * frame_ms,
        "second_lane_active_frames": int(second.sum()),
        "method": "original vocal activity gated by persistent non-octave dual-pitch evidence",
        "limitations": ["Harmonic instruments may mimic a second pitch",
                        "Harmony mouth shapes borrow lead syllables",
                        "Not eligible as independent vocal-source proof"],
    }
