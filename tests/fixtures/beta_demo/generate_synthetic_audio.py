#!/usr/bin/env python3
"""Generate a tiny clean-room WAV file for beta smoke tests.

The generated tone is synthetic and contains no copyrighted or private material.
"""

from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path


DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_DURATION_SECONDS = 0.5
DEFAULT_FREQUENCY_HZ = 440.0
DEFAULT_AMPLITUDE = 0.25


def generate_wav(
    output_path: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    duration_seconds: float = DEFAULT_DURATION_SECONDS,
    frequency_hz: float = DEFAULT_FREQUENCY_HZ,
    amplitude: float = DEFAULT_AMPLITUDE,
) -> Path:
    """Write a deterministic mono 16-bit PCM sine wave and return its path."""

    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    if not 0 < amplitude <= 1:
        raise ValueError("amplitude must be in the range (0, 1]")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_samples = int(sample_rate * duration_seconds)
    peak = int(32767 * amplitude)

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for sample_index in range(total_samples):
            t = sample_index / sample_rate
            value = int(peak * math.sin(2 * math.pi * frequency_hz * t))
            frames.extend(value.to_bytes(2, byteorder="little", signed=True))
        wav_file.writeframes(bytes(frames))

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default=Path(__file__).with_name("synthetic_tone.wav"),
        type=Path,
        help="Path to write the generated WAV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated = generate_wav(args.output)
    print(generated)


if __name__ == "__main__":
    main()
