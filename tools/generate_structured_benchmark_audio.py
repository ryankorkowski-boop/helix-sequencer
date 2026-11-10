#!/usr/bin/env python3
"""Generate deterministic CI-safe benchmark audio for Helix grading.

The file is synthetic and source-clean: no sampled music, no external media, and no
creator/style imitation. It exists to exercise analysis paths that plain sine tones
miss: sections, kick/snare/hat pulses, bass movement, melody-like foreground, and a
finale lift.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf


SR = 44_100


def _env(length: int, attack: float = 0.005, release: float = 0.08) -> np.ndarray:
    env = np.ones(length, dtype=np.float32)
    attack_n = max(1, int(attack * SR))
    release_n = max(1, int(release * SR))
    env[: min(length, attack_n)] = np.linspace(0.0, 1.0, min(length, attack_n), dtype=np.float32)
    env[max(0, length - release_n) :] *= np.linspace(1.0, 0.0, min(length, release_n), dtype=np.float32)
    return env


def _add_tone(buf: np.ndarray, start: float, duration: float, freq: float, amp: float, *, release: float = 0.08) -> None:
    start_i = int(start * SR)
    end_i = min(len(buf), start_i + int(duration * SR))
    if end_i <= start_i:
        return
    t = np.arange(end_i - start_i, dtype=np.float32) / SR
    tone = np.sin(2.0 * np.pi * freq * t).astype(np.float32) * amp
    buf[start_i:end_i] += tone * _env(len(tone), release=release)


def _add_noise_hit(buf: np.ndarray, start: float, duration: float, amp: float, *, seed: int, lowpass_shape: float = 1.0) -> None:
    start_i = int(start * SR)
    end_i = min(len(buf), start_i + int(duration * SR))
    if end_i <= start_i:
        return
    rng = np.random.default_rng(seed)
    hit = rng.normal(0.0, 1.0, end_i - start_i).astype(np.float32)
    # simple decay and crude tonal shaping by cumulative smoothing
    for _ in range(max(0, int(lowpass_shape))):
        hit = np.cumsum(hit)
        hit = hit / max(1e-6, np.max(np.abs(hit)))
    hit *= _env(len(hit), attack=0.001, release=duration * 0.8) * amp
    buf[start_i:end_i] += hit


def _add_kick(buf: np.ndarray, start: float, amp: float = 0.7) -> None:
    start_i = int(start * SR)
    length = int(0.16 * SR)
    end_i = min(len(buf), start_i + length)
    if end_i <= start_i:
        return
    n = end_i - start_i
    t = np.arange(n, dtype=np.float32) / SR
    freq = np.linspace(95.0, 42.0, n, dtype=np.float32)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    hit = np.sin(phase).astype(np.float32) * np.exp(-t * 18.0).astype(np.float32) * amp
    buf[start_i:end_i] += hit


def _add_snare(buf: np.ndarray, start: float, seed: int) -> None:
    _add_noise_hit(buf, start, 0.12, 0.32, seed=seed, lowpass_shape=0)
    _add_tone(buf, start, 0.10, 180.0, 0.12, release=0.05)


def build_audio(duration: float) -> np.ndarray:
    buf = np.zeros(int(duration * SR), dtype=np.float32)
    bpm = 120.0
    beat = 60.0 / bpm

    # Section map: intro, verse, chorus/drop, bridge/breakdown, finale.
    sections = [
        (0.0, 8.0, 0.45, [220, 277, 330, 440]),
        (8.0, 20.0, 0.65, [247, 294, 370, 494]),
        (20.0, 34.0, 0.95, [262, 330, 392, 523]),
        (34.0, 44.0, 0.35, [196, 247, 294, 392]),
        (44.0, duration, 1.0, [294, 370, 440, 587]),
    ]

    for section_i, (start, end, energy, notes) in enumerate(sections):
        end = min(end, duration)
        if end <= start:
            continue
        # Pad/foundation chord.
        chord_dur = end - start
        for note_i, freq in enumerate(notes[:3]):
            _add_tone(buf, start, chord_dur, freq, 0.035 * energy / (note_i + 1), release=0.4)

        # Bass movement on beats.
        beat_t = start
        beat_index = 0
        while beat_t < end:
            root = notes[0] / 2.0
            bass_freq = root if beat_index % 4 != 3 else root * 1.5
            _add_tone(buf, beat_t, 0.22, bass_freq, 0.16 * energy, release=0.12)
            if energy > 0.5:
                _add_kick(buf, beat_t, 0.45 * energy)
            if beat_index % 4 in (1, 3) and energy > 0.55:
                _add_snare(buf, beat_t + 0.01, seed=section_i * 1000 + beat_index)
            if energy > 0.7:
                _add_noise_hit(buf, beat_t + beat / 2.0, 0.035, 0.055 * energy, seed=9000 + section_i * 1000 + beat_index, lowpass_shape=0)
            beat_t += beat
            beat_index += 1

        # Melody/foreground phrase every two beats.
        phrase_t = start + beat
        phrase_index = 0
        while phrase_t < end:
            freq = notes[phrase_index % len(notes)] * (2.0 if energy > 0.8 and phrase_index % 5 == 0 else 1.0)
            _add_tone(buf, phrase_t, 0.18 if energy < 0.8 else 0.12, freq, 0.11 * energy, release=0.06)
            phrase_t += beat * (1.5 if energy > 0.8 else 2.0)
            phrase_index += 1

        # Transition lift at section end.
        if end < duration:
            for i in range(8):
                t = max(start, end - 1.2 + i * 0.15)
                _add_tone(buf, t, 0.08, notes[-1] * (1.0 + i * 0.08), 0.055 + 0.035 * energy, release=0.04)

    peak = float(np.max(np.abs(buf))) or 1.0
    return (buf / peak * 0.82).astype(np.float32)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic structured Helix benchmark WAV.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--duration", type=float, default=60.0)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    audio = build_audio(args.duration)
    sf.write(args.output, audio, SR)
    print(f"Wrote {args.output} ({args.duration:.1f}s, {SR} Hz)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
