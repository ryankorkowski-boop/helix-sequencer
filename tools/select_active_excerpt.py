"""Select a high-activity excerpt from authentic audio without substituting media.

The score combines RMS energy and positive spectral change; it is deterministic.
Only a time range is returned. The caller must preserve and verify source audio.
"""
from __future__ import annotations

import argparse
import json
import numpy as np


def select_excerpt(samples: np.ndarray, sample_rate: int, seconds: float = 36.0,
                   hop_seconds: float = 0.1) -> dict:
    """Return a sample-accurate excerpt interval and relative activity score."""
    if sample_rate <= 0 or seconds <= 0 or hop_seconds <= 0:
        raise ValueError("sample_rate, seconds and hop_seconds must be positive")
    audio = np.asarray(samples, dtype=np.float64)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if audio.ndim != 1 or not len(audio) or not np.all(np.isfinite(audio)):
        raise ValueError("Expected nonempty finite mono or multichannel audio")
    excerpt_n = min(len(audio), round(seconds * sample_rate))
    hop = max(1, round(hop_seconds * sample_rate))
    frame_n = max(256, min(2048, round(sample_rate * 0.046)))
    starts = np.arange(0, len(audio), hop)
    energy = np.empty(len(starts))
    flux = np.empty(len(starts))
    previous = None
    for i, start in enumerate(starts):
        frame = audio[start:start + frame_n]
        if len(frame) < frame_n:
            frame = np.pad(frame, (0, frame_n - len(frame)))
        energy[i] = np.sqrt(np.mean(frame * frame))
        spectrum = np.abs(np.fft.rfft(frame * np.hanning(frame_n)))
        spectrum /= max(float(spectrum.sum()), 1e-12)
        flux[i] = 0 if previous is None else np.maximum(spectrum - previous, 0).sum()
        previous = spectrum
    def normalized(values: np.ndarray) -> np.ndarray:
        scale = np.percentile(values, 95)
        return np.clip(values / scale, 0, 1) if scale > 0 else np.zeros_like(values)
    activity = 0.65 * normalized(energy) + 0.35 * normalized(flux)
    # Evaluate only full-duration windows, never padded tail windows.
    max_start = len(audio) - excerpt_n
    valid = starts <= max_start
    cumulative = np.r_[0.0, np.cumsum(activity)]
    end_indices = np.searchsorted(starts, starts[valid] + excerpt_n, side="left")
    window_scores = (cumulative[end_indices] - cumulative[np.flatnonzero(valid)]) / np.maximum(end_indices - np.flatnonzero(valid), 1)
    best = int(np.argmax(window_scores))
    start_sample = int(starts[best])
    return {"start_seconds": start_sample / sample_rate,
            "end_seconds": (start_sample + excerpt_n) / sample_rate,
            "duration_seconds": excerpt_n / sample_rate,
            "activity_score": float(window_scores[best]),
            "sample_rate": sample_rate}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", help="Real source WAV/MP3 readable by soundfile")
    parser.add_argument("--seconds", type=float, default=36.0)
    args = parser.parse_args()
    import soundfile as sf
    audio, sr = sf.read(args.audio, always_2d=False)
    print(json.dumps(select_excerpt(audio, sr, args.seconds), indent=2))


if __name__ == "__main__":
    main()
