from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from music.note_events import NoteEvent, active_notes_at
from render.keyboard_geometry import KeyboardGeometry, generate_keyboard_geometry


PITCH_CLASS_COLORS = (
    "#ff4040",
    "#ff7a28",
    "#ffd23a",
    "#b7ff3d",
    "#4dff70",
    "#39ffd0",
    "#38c7ff",
    "#4677ff",
    "#7c55ff",
    "#c04dff",
    "#ff4fcb",
    "#ff4f84",
)


@dataclass(frozen=True)
class PianoRenderConfig:
    mode: str = "true_piano"
    note_range_start: int = 21
    note_range_end: int = 108
    show_sharps_flats: bool = True
    vertical_scale: float = 1.0
    horizontal_offset: float = 0.0
    key_decay_ms: int = 180
    velocity_affects_brightness: bool = True
    color_mode: str = "classic"
    sustain_render_mode: str = "hold"
    orientation: str = "horizontal"
    projection_mode: str = "literal_keyboard"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def color_for_note(pitch: int, velocity: float, color_mode: str) -> str:
    if color_mode == "classic":
        return "#ffe66d" if velocity < 0.85 else "#ffffff"
    if color_mode == "pitch_class":
        return PITCH_CLASS_COLORS[int(pitch) % 12]
    if color_mode == "velocity_heat":
        v = _clamp(velocity)
        red = 255
        green = int(round(45 + 190 * v))
        blue = int(round(20 + 40 * (1.0 - v)))
        return f"#{red:02x}{green:02x}{blue:02x}"
    if color_mode == "low_to_high_gradient":
        frac = _clamp((int(pitch) - 21) / 87.0)
        red = int(round(60 + 160 * frac))
        green = int(round(100 + 120 * (1.0 - abs(frac - 0.5) * 2.0)))
        blue = int(round(220 - 150 * frac))
        return f"#{red:02x}{green:02x}{blue:02x}"
    return PITCH_CLASS_COLORS[int(pitch) % 12]


def intensity_for_event(event: NoteEvent, timestamp: float, config: PianoRenderConfig) -> float:
    base = _clamp(event.velocity if config.velocity_affects_brightness else 1.0)
    if timestamp <= event.end or config.sustain_render_mode == "hold":
        return base
    decay = max(1, int(config.key_decay_ms)) / 1000.0
    age = max(0.0, timestamp - event.end)
    if config.sustain_render_mode == "pulse":
        return base * (0.55 + 0.45 * math.sin(age * math.pi * 8.0) ** 2) * max(0.0, 1.0 - age / decay)
    return base * max(0.0, 1.0 - age / decay)


def render_true_piano_frame(
    events: Iterable[NoteEvent],
    timestamp: float,
    config: PianoRenderConfig,
    geometry: KeyboardGeometry | None = None,
) -> dict[str, object]:
    geometry = geometry or generate_keyboard_geometry(
        config.note_range_start,
        config.note_range_end,
        show_sharps_flats=config.show_sharps_flats,
        orientation=config.orientation,
    )
    decay_seconds = max(0.0, config.key_decay_ms / 1000.0) if config.sustain_render_mode in {"decay", "pulse"} else 0.0
    active = active_notes_at(events, timestamp, decay_seconds=decay_seconds)
    by_pitch = {event.pitch: event for event in active}
    keys = []
    for key in geometry.keys:
        event = by_pitch.get(key.pitch)
        intensity = intensity_for_event(event, timestamp, config) if event else 0.0
        base_color = "#0b0d12" if key.is_black else "#f5f2e8"
        keys.append(
            {
                **key.to_dict(),
                "active": bool(event),
                "intensity": round(_clamp(intensity), 4),
                "color": color_for_note(key.pitch, event.velocity, config.color_mode) if event else base_color,
            }
        )
    return {
        "mode": "true_piano",
        "timestamp": round(float(timestamp), 4),
        "projection_mode": config.projection_mode,
        "geometry": geometry.to_dict(),
        "keys": keys,
    }


def render_bars_frame(
    events: Iterable[NoteEvent],
    timestamp: float,
    config: PianoRenderConfig,
) -> dict[str, object]:
    decay_seconds = max(0.0, config.key_decay_ms / 1000.0) if config.sustain_render_mode in {"decay", "pulse"} else 0.0
    active = active_notes_at(events, timestamp, decay_seconds=decay_seconds)
    span = max(1, int(config.note_range_end) - int(config.note_range_start))
    bars = []
    for event in active:
        frac = _clamp((event.pitch - config.note_range_start) / span)
        intensity = intensity_for_event(event, timestamp, config)
        duration = max(0.001, event.end - event.start)
        progress = _clamp((timestamp - event.start) / duration)
        if config.orientation == "vertical":
            x, y = 0.0, frac
            width, height = _clamp(intensity), 1.0 / (span + 1)
        else:
            x, y = frac, 0.0
            width, height = 1.0 / (span + 1), _clamp(intensity)
        bars.append(
            {
                "pitch": event.pitch,
                "x": round(x, 4),
                "y": round(y, 4),
                "width": round(width, 4),
                "height": round(height, 4),
                "progress": round(progress, 4),
                "intensity": round(_clamp(intensity), 4),
                "color": color_for_note(event.pitch, event.velocity, config.color_mode),
                "source": event.source,
            }
        )
    return {
        "mode": "bars",
        "timestamp": round(float(timestamp), 4),
        "projection_mode": "abstract_note_grid",
        "bars": sorted(bars, key=lambda item: (item["pitch"], item["x"], item["y"])),
    }


def render_frame(events: Iterable[NoteEvent], timestamp: float, config: PianoRenderConfig) -> dict[str, object]:
    if config.mode == "bars" or config.projection_mode == "abstract_note_grid":
        return render_bars_frame(events, timestamp, config)
    return render_true_piano_frame(events, timestamp, config)
