from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.beat_grid import BeatGrid, generate_beat_grid, snap_ms_to_grid


CRASH_WORDS = ("crash", "cymbal", "china", "splash", "ride")
SNARE_WORDS = ("snare", "clap", "rim")
KICK_WORDS = ("kick", "bass_drum", "bass drum", "bd")
FILL_WORDS = ("fill", "tom", "roll", "flam", "riff")
HAT_WORDS = ("hat", "hihat", "hi-hat", "tick", "shaker")


@dataclass(frozen=True)
class DrumQuantizationReport:
    events_seen: int = 0
    events_changed: int = 0
    crashes: int = 0
    fills: int = 0
    backbeat_hits: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "events_seen": self.events_seen,
            "events_changed": self.events_changed,
            "crashes": self.crashes,
            "fills": self.fills,
            "backbeat_hits": self.backbeat_hits,
        }


def _text_for_event(event: Mapping[str, Any]) -> str:
    parts = []
    for key in ("label", "name", "type", "instrument", "drum", "role", "cue", "part", "track"):
        value = event.get(key)
        if value is not None:
            parts.append(str(value).lower())
    return " ".join(parts)


def classify_drum_event(event: Mapping[str, Any]) -> str:
    text = _text_for_event(event)
    if any(word in text for word in CRASH_WORDS):
        return "crash"
    if any(word in text for word in FILL_WORDS):
        return "fill"
    if any(word in text for word in SNARE_WORDS):
        return "snare"
    if any(word in text for word in KICK_WORDS):
        return "kick"
    if any(word in text for word in HAT_WORDS):
        return "hat"
    return "drum"


def _start_key(event: Mapping[str, Any]) -> str | None:
    for key in ("start_ms", "timestamp_ms", "hit_ms", "time_ms", "impact_ms"):
        if key in event:
            return key
    return None


def _end_key(event: Mapping[str, Any]) -> str | None:
    for key in ("end_ms", "impact_end_ms", "release_ms"):
        if key in event:
            return key
    return None


def _strong_beat_grid(beat_grid: BeatGrid, duration_ms: int) -> list[int]:
    # Quarter-note grid is the safest default for cymbal crashes and section hits.
    grid = BeatGrid(
        bpm=beat_grid.bpm,
        time_signature=beat_grid.time_signature,
        subdivision=4,
        offset_ms=beat_grid.offset_ms,
        beat_track_ms=beat_grid.beat_track_ms,
        mode=beat_grid.mode,
        max_shift_ms=max(beat_grid.max_shift_ms, 70),
    )
    return generate_beat_grid(grid, duration_ms)


def _fine_grid(beat_grid: BeatGrid, duration_ms: int) -> list[int]:
    # Fills can move to sixteenth or thirty-second positions without feeling late.
    grid = BeatGrid(
        bpm=beat_grid.bpm,
        time_signature=beat_grid.time_signature,
        subdivision=max(16, beat_grid.subdivision),
        offset_ms=beat_grid.offset_ms,
        beat_track_ms=beat_grid.beat_track_ms,
        mode=beat_grid.mode,
        max_shift_ms=beat_grid.max_shift_ms,
    )
    return generate_beat_grid(grid, duration_ms)


def quantize_drum_event(event: dict[str, Any], beat_grid: BeatGrid, *, duration_ms: int) -> tuple[bool, str]:
    key = _start_key(event)
    if key is None:
        return False, "unknown"
    try:
        raw_start = int(round(float(event[key])))
    except Exception:
        return False, "unknown"
    kind = classify_drum_event(event)
    base_grid = generate_beat_grid(beat_grid, duration_ms)
    if kind == "crash":
        grid_points = _strong_beat_grid(beat_grid, duration_ms)
        max_shift = max(beat_grid.max_shift_ms, 70)
    elif kind == "fill":
        grid_points = _fine_grid(beat_grid, duration_ms)
        max_shift = max(beat_grid.max_shift_ms, 55)
    elif kind in {"kick", "snare"}:
        grid_points = base_grid
        max_shift = max(beat_grid.max_shift_ms, 45)
    else:
        grid_points = base_grid
        max_shift = beat_grid.max_shift_ms
    snapped_start = snap_ms_to_grid(raw_start, grid_points, max_shift_ms=max_shift, mode=beat_grid.mode)
    delta = snapped_start - raw_start
    event.setdefault("raw_start_ms", raw_start)
    event["snapped_start_ms"] = snapped_start
    event[key] = snapped_start
    if key != "start_ms" and "start_ms" not in event:
        event["start_ms"] = snapped_start
    end_key = _end_key(event)
    if end_key is not None:
        try:
            raw_end = int(round(float(event[end_key])))
        except Exception:
            raw_end = raw_start + 1
        event.setdefault("raw_end_ms", raw_end)
        event[end_key] = max(snapped_start + 1, raw_end + delta)
        event["snapped_end_ms"] = event[end_key]
    return snapped_start != raw_start, kind


def quantize_drum_events(events: Iterable[dict[str, Any]], beat_grid: BeatGrid, *, duration_ms: int) -> DrumQuantizationReport:
    seen = changed = crashes = fills = backbeat = 0
    for event in events:
        seen += 1
        did_change, kind = quantize_drum_event(event, beat_grid, duration_ms=duration_ms)
        changed += int(did_change)
        crashes += int(kind == "crash")
        fills += int(kind == "fill")
        backbeat += int(kind in {"kick", "snare"})
    return DrumQuantizationReport(seen, changed, crashes, fills, backbeat)


def quantize_drum_payload(payload: dict[str, Any], beat_grid: BeatGrid, *, duration_ms: int) -> dict[str, Any]:
    """Find drum-like event dictionaries inside a band payload and quantize them."""

    candidates: list[dict[str, Any]] = []

    def visit(value: Any, parent_key: str = "") -> None:
        if isinstance(value, dict):
            text = f"{parent_key} {_text_for_event(value)}".lower()
            if _start_key(value) and any(token in text for token in (*CRASH_WORDS, *SNARE_WORDS, *KICK_WORDS, *FILL_WORDS, *HAT_WORDS, "drum")):
                candidates.append(value)
            for key, child in value.items():
                visit(child, key)
        elif isinstance(value, list):
            for child in value:
                visit(child, parent_key)

    visit(payload)
    report = quantize_drum_events(candidates, beat_grid, duration_ms=duration_ms)
    payload.setdefault("beat_grid", {})
    if isinstance(payload["beat_grid"], dict):
        payload["beat_grid"]["drummer_quantization"] = report.as_dict()
    return payload
