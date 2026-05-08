"""Convert WAV audio into deterministic Style Engine AudioSegments.

This adapter is intentionally dependency-light: it uses Python's standard
library wave module and simple RMS energy windows. It is not the final music
intelligence layer, but it provides a real-audio input path for the Style Engine.
"""

from __future__ import annotations

import audioop
import wave
from pathlib import Path

from tools.style_engine import AudioSegment


def _classify_section(position: float) -> str:
    """Rough musical section estimate from normalized song position."""

    if position < 0.12:
        return "intro"
    if position < 0.45:
        return "verse"
    if position < 0.75:
        return "chorus"
    if position < 0.9:
        return "bridge"
    return "finale"


def _classify_event(energy: float, previous_energy: float) -> str:
    """Classify simple rhythmic events from normalized energy."""

    rise = energy - previous_energy
    if energy <= 0.05:
        return "silence"
    if energy >= 0.85 and rise >= 0.12:
        return "hit"
    if energy >= 0.70:
        return "beat"
    if rise >= 0.18:
        return "build"
    return "texture"


def wav_to_audio_segments(wav_path: str | Path, window_seconds: float = 0.5) -> list[AudioSegment]:
    """Read a WAV file and return deterministic AudioSegments.

    The returned segments contain normalized energy and simple event/section
    labels suitable for feeding HelixStyleEngine.decide().
    """

    path = Path(wav_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")

    with wave.open(str(path), "rb") as wav:
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        channels = wav.getnchannels()
        total_frames = wav.getnframes()
        frames_per_window = max(1, int(sample_rate * window_seconds))
        total_duration = total_frames / float(sample_rate)

        windows: list[tuple[float, float, float]] = []
        start_frame = 0
        while start_frame < total_frames:
            frame_count = min(frames_per_window, total_frames - start_frame)
            raw = wav.readframes(frame_count)
            rms = float(audioop.rms(raw, sample_width)) if raw else 0.0
            start = start_frame / float(sample_rate)
            duration = frame_count / float(sample_rate)
            windows.append((start, duration, rms))
            start_frame += frame_count

    if not windows:
        return []

    max_rms = max(rms for _, _, rms in windows) or 1.0
    segments: list[AudioSegment] = []
    previous_energy = 0.0

    for start, duration, rms in windows:
        energy = min(1.0, rms / max_rms)
        position = min(1.0, start / total_duration) if total_duration else 0.0
        event_type = _classify_event(energy, previous_energy)
        section = _classify_section(position)
        onset_density = max(0.0, min(1.0, energy - previous_energy + 0.5))
        beat_strength = energy if event_type in {"beat", "hit"} else max(0.0, energy * 0.65)

        segments.append(
            AudioSegment(
                start=round(start, 3),
                duration=round(duration, 3),
                section=section,
                event_type=event_type,
                energy=round(energy, 3),
                beat_strength=round(beat_strength, 3),
                onset_density=round(onset_density, 3),
                bass_energy=round(energy, 3),
                vocal_presence=0.0,
            )
        )
        previous_energy = energy

    return segments
