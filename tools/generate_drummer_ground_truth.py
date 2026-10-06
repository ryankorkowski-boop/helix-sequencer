#!/usr/bin/env python3
"""Generate the deterministic Drummer V3 verification WAV and event manifest."""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

import numpy as np

from tools.drummer_ground_truth_oracle import GroundTruthEvent, fixture_events

SAMPLE_RATE = 44100
DURATION = 20.0


def _add_event(audio: np.ndarray, event: GroundTruthEvent, rng: np.random.Generator) -> None:
    start = int(round(event.time * SAMPLE_RATE))
    if start >= len(audio):
        return
    length = min(int(max(event.duration, 0.02) * SAMPLE_RATE), len(audio) - start)
    if length <= 0:
        return
    t = np.arange(length, dtype=np.float64) / SAMPLE_RATE
    decay = max(0.025, event.duration * 0.75)
    env = np.exp(-t / decay)
    target = event.target
    if target == "KICK":
        signal = np.sin(2 * np.pi * (58.0 - 16.0 * np.minimum(t / 0.18, 1.0)) * t) * 0.90
    elif target == "SNARE":
        signal = 0.24 * np.sin(2 * np.pi * 190.0 * t) + 0.62 * rng.normal(size=length)
    elif target == "HI_HAT":
        signal = 0.30 * rng.normal(size=length)
        signal = np.concatenate(([signal[0]], np.diff(signal)))
    elif target == "TOM_HIGH":
        signal = 0.72 * np.sin(2 * np.pi * 175.0 * t)
    elif target == "TOM_MID":
        signal = 0.74 * np.sin(2 * np.pi * 125.0 * t)
    elif target == "TOM_FLOOR":
        signal = 0.78 * np.sin(2 * np.pi * 90.0 * t)
    else:
        signal = 0.55 * rng.normal(size=length)
        signal = np.concatenate(([signal[0]], np.diff(signal)))
    audio[start:start + length] += (signal * env).astype(np.float32)


def generate(wav_path: Path, events_path: Path, duration: float = DURATION) -> None:
    duration = float(duration)
    count = int(round(SAMPLE_RATE * duration))
    audio = np.zeros(count, dtype=np.float32)
    rng = np.random.default_rng(42)
    events = fixture_events(duration)
    for event in events:
        _add_event(audio, event, rng)
    audio = np.clip(audio, -0.95, 0.95)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes((audio * 32767).astype(np.int16).tobytes())
    payload = [
        {"time": round(event.time, 4), "duration": round(event.duration, 4), "event": event.target}
        for event in events
    ]
    events_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {wav_path} and {events_path}; {len(events)} known events; duration={duration:.3f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wav", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=DURATION)
    args = parser.parse_args()
    generate(args.wav, args.events, args.duration)
