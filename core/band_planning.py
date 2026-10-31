"""Shared production stage for synchronized band and performer plans."""
from __future__ import annotations

from typing import Any, Callable, Mapping

from core import band_sync, snowman_band


def build_band_plans(
    *,
    parsed_layout: Any,
    parts: list[Any],
    lyric_events: list[Any],
    note_events: list[Any],
    beat_ms: list[int],
    onset_ms: list[int],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    build_lifts: list[int],
    releases: list[int],
    song_length_ms: int,
    chronoflow_payload: Mapping[str, Any] | None = None,
    multiband: Any = None,
    enable_lyrics: bool = True,
    background_vocal_events: list[Any] | None = None,
    drum_event_streams: dict[str, list[Any]] | None = None,
    require_keyboard_source_ownership: bool = False,
    keyboard_ownership_threshold: float = 0.7,
    log_fn: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Route shared musical evidence and consumer-specific options once.

    Keyboard ownership belongs to performer planning, not the shared timeline.
    Preserve independent failure recovery and expose failures in diagnostics.
    """
    try:
        sync_payload = band_sync.build_band_sync_plan(
            parts=parts,
            beat_ms=beat_ms,
            onset_ms=onset_ms,
            vocal_peaks=vocal_peaks,
            bass_peaks=bass_peaks,
            note_events=note_events,
            background_vocal_events=background_vocal_events or [],
            drum_event_streams=drum_event_streams or {},
            song_length_ms=song_length_ms,
        )
    except Exception as exc:
        if log_fn:
            log_fn(f"[WARN] Band synchronization skipped: {exc!r}")
        sync_payload = {
            "schema": "helix.band_sync.v1", "timeline": [], "state_frames": [],
            "debug": {"planning_error": {"type": type(exc).__name__, "message": str(exc)}},
        }
    try:
        band_payload = snowman_band.build_snowman_band_plan(
            parsed_layout=parsed_layout,
            parts=parts,
            lyric_events=lyric_events,
            note_events=note_events,
            beat_ms=beat_ms,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            build_lifts=build_lifts,
            releases=releases,
            chronoflow_payload=chronoflow_payload,
            band_sync_payload=sync_payload,
            multiband=multiband,
            enable_lyrics=enable_lyrics,
            background_vocal_events=background_vocal_events or [],
            drum_event_streams=drum_event_streams or {},
            require_keyboard_source_ownership=require_keyboard_source_ownership,
            keyboard_ownership_threshold=keyboard_ownership_threshold,
        )
    except Exception as exc:
        if log_fn:
            log_fn(f"[WARN] Snowman band planning skipped: {exc!r}")
        band_payload = {
            "enabled": False, "face_routing": {}, "performers": {},
            "kit": {"components": []}, "layout_mapping": {},
            "visualizer_overlay": {"lyrics_enabled": False, "soundtunnel_lyrics": []},
            "cues": {},
            "debug": {
                "total_cue_count": 0, "lyric_cues": 0,
                "planning_error": {"type": type(exc).__name__, "message": str(exc)},
            },
        }
    return sync_payload, band_payload
