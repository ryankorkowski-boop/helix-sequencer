from __future__ import annotations

from typing import Any, Mapping

from core.beat_grid import BeatGrid, generate_beat_grid, snap_timing_events
from core import snowman_band


_TIMING_LIST_KEYS = {
    "lyric_words",
    "lyric_lines",
    "phoneme_events",
    "vocal_role_events",
    "song_parts",
    "part_hits",
    "vocal_emotion_events",
    "face_activation_events",
    "face_timing_events",
    "performer_emphasis_events",
    "lyric_timing_track",
    "word_timing_track",
    "phoneme_timing_track",
    "performer_vocal_routes",
    "faces_effect_instructions",
    "song_part_markers",
    "part_hit_markers",
    "sequence_effect_instructions",
    "lyric_timing_tracks",
    "phoneme_timing_tracks",
    "faces_effect_placements",
    "song_part_timing_markers",
    "emotion_palette_timeline",
}


def _infer_duration_ms(payload: Mapping[str, Any]) -> int:
    duration = int(float(payload.get("duration_seconds", 0.0) or 0.0) * 1000.0)

    def visit(value: Any) -> None:
        nonlocal duration
        if isinstance(value, Mapping):
            for key in ("end_ms", "timestamp_ms", "start_ms", "hit_ms", "impact_end_ms"):
                if key in value:
                    try:
                        duration = max(duration, int(round(float(value[key]))))
                    except Exception:
                        pass
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for key in ("global_timeline", "timing_intelligence", "xlights_translation", "cues", "emotion"):
        visit(payload.get(key))
    return max(duration + 1000, 1)


def _snap_dict_event(event: dict[str, Any], grid_points: list[int], beat_grid: BeatGrid) -> None:
    start_key = "start_ms" if "start_ms" in event else "timestamp_ms" if "timestamp_ms" in event else "hit_ms" if "hit_ms" in event else "preview_start_ms" if "preview_start_ms" in event else ""
    if not start_key:
        return
    try:
        raw_start = int(round(float(event[start_key])))
    except Exception:
        return
    snapped_start = snap_timing_events([raw_start], grid_points, max_shift_ms=beat_grid.max_shift_ms, mode=beat_grid.mode)[0]
    delta = snapped_start - raw_start
    event.setdefault("raw_start_ms", raw_start)
    event.setdefault("snapped_start_ms", snapped_start)
    event[start_key] = snapped_start
    if start_key != "start_ms" and "start_ms" not in event:
        event["start_ms"] = snapped_start
    if "end_ms" in event:
        try:
            raw_end = int(round(float(event["end_ms"])))
            event.setdefault("raw_end_ms", raw_end)
            event["end_ms"] = max(snapped_start + 1, raw_end + delta)
            event.setdefault("snapped_end_ms", event["end_ms"])
        except Exception:
            pass
    for key in ("impact_end_ms",):
        if key in event:
            try:
                event[key] = max(snapped_start + 1, int(round(float(event[key]))) + delta)
            except Exception:
                pass


def snap_snowman_band_payload_to_grid(payload: dict[str, Any], beat_grid: BeatGrid, *, duration_ms: int | None = None) -> dict[str, Any]:
    """Snap all timing dictionaries emitted by the snowman band planner.

    This activates Issue #41 for the band plan without changing the legacy
    ``build_snowman_band_plan`` signature. Raw timing metadata is preserved on
    every snapped dictionary so the self-improving scorer can measure rhythmic
    accuracy from generated payloads.
    """

    duration = duration_ms or _infer_duration_ms(payload)
    grid_points = generate_beat_grid(beat_grid, duration)

    def visit(value: Any, parent_key: str = "") -> None:
        if isinstance(value, list):
            if parent_key in _TIMING_LIST_KEYS:
                for item in value:
                    if isinstance(item, dict):
                        _snap_dict_event(item, grid_points, beat_grid)
            for item in value:
                visit(item, parent_key)
        elif isinstance(value, dict):
            for key, child in value.items():
                visit(child, key)

    visit(payload)
    debug = payload.setdefault("debug", {})
    if isinstance(debug, dict):
        debug["beat_grid_snapped"] = True
        debug["beat_grid_subdivision"] = beat_grid.subdivision
        debug["beat_grid_mode"] = beat_grid.mode
        debug["beat_grid_point_count"] = len(grid_points)
    payload.setdefault("beat_grid", {})
    if isinstance(payload["beat_grid"], dict):
        payload["beat_grid"].update(
            {
                "snapped": True,
                "subdivision": beat_grid.subdivision,
                "mode": beat_grid.mode,
                "max_shift_ms": beat_grid.max_shift_ms,
            }
        )
    return payload


def build_snowman_band_plan_with_grid(*, beat_grid: BeatGrid | None = None, snap_timing: bool = True, duration_ms: int | None = None, **kwargs: Any) -> dict[str, Any]:
    """Build a snowman band plan and optionally align all emitted timing to grid."""

    payload = snowman_band.build_snowman_band_plan(**kwargs)
    if snap_timing and beat_grid is not None:
        return snap_snowman_band_payload_to_grid(payload, beat_grid, duration_ms=duration_ms)
    return payload
