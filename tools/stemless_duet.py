"""Conservative, opt-in stemless duet estimates from a verified mixed recording.

This is *not* vocal identity separation or evidence of an independent singer.
Only generate a second mouth lane when existing vocal activity and two distinct
persistent pitch tracks coincide. Never claim these estimates are stems.
"""
from __future__ import annotations

import numpy as np
import librosa


def estimate_duet(audio, source_energy, source_shapes, *, frames=720, sr=11025):
    """Return two 20-Hz mouth lanes, energies and an auditable estimate.

    The original source vocal lane gates every event. Pitch evidence can
    suppress or support the harmony lane, but cannot manufacture activity in
    instrumental or silent intervals absent from that source vocal gate.
    """
    source_energy = np.asarray(source_energy, dtype=np.float32)
    source_shapes = np.asarray(source_shapes)
    if source_energy.ndim != 2 or source_energy.shape[1] != 2 or source_shapes.shape != source_energy.shape:
        raise ValueError("Expected two original source vocal lanes")
    if len(source_energy) != frames:
        raise ValueError("Original source frame count mismatch")
    if not np.isfinite(source_energy).all() or np.any(source_energy < 0):
        raise ValueError("Invalid source vocal energy")
    y, rate = librosa.load(str(audio), sr=sr, mono=True)
    hop = max(1, round(rate / 20))
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    pitch, mag = librosa.piptrack(S=spec, sr=rate, fmin=130, fmax=1050, threshold=.15)
    confidence = np.zeros(frames, dtype=np.float32)
    for i in range(min(frames, pitch.shape[1])):
        candidates = np.flatnonzero((pitch[:, i] > 0) & (mag[:, i] > 0))
        if len(candidates) < 2:
            continue
        ordered = candidates[np.argsort(mag[candidates, i])[::-1]]
        strongest = float(mag[ordered[0], i])
        first = float(pitch[ordered[0], i])
        for idx in ordered[1:]:
            second = float(pitch[idx, i])
            semitones = abs(12 * np.log2(second / first))
            # Avoid octave harmonics and adjacent bins from the same voice.
            if 2.0 <= semitones <= 10.0 and abs(semitones - 12.0) > 1.0:
                confidence[i] = min(1.0, float(mag[idx, i]) / max(strongest, 1e-9))
                break
    # Require 3 consecutive 50-ms frames to avoid percussive pitch spikes.
    persistent = np.convolve((confidence >= .30).astype(np.int8), np.ones(3, dtype=np.int8), mode="same") == 3
    lead = np.clip(source_energy[:, 0], 0, 1)
    vocal_gate = (lead > .12) & (source_shapes[:, 0] != 0)
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
        "second_lane_active_frames": int(second.sum()),
        "method": "original vocal activity gated by persistent non-octave dual-pitch evidence",
        "limitations": ["Harmonic instruments may mimic a second pitch",
                        "Harmony mouth shapes borrow lead syllables",
                        "Not eligible as independent vocal-source proof"],
    }
