"""Percussion classification and canonical snowman mapping boundary.

Detection, scheduling, motion and illumination keep their existing owners and
thresholds. This module assembles their unchanged outputs for the master path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from core.lazy_imports import LazyModule
from core.stage_metrics import timed_stage
from xlights import xsq_writer as base
from animation import drummer_motion
from effects import drum_effects
from mapping import drum_mapper

np = LazyModule("numpy")


@dataclass(frozen=True)
class PercussionMarks:
    kicks: list[int]
    snares: list[int]
    hats: list[int]


@timed_stage("drums.onset_classification")
def classify_percussion_onsets(audio: base.Audio, onset_ms: list[int]) -> PercussionMarks:
    hats: list[int] = []
    snares: list[int] = []
    kicks: list[int] = []
    for t_ms in onset_ms:
        centroid = base.nearest(audio.times_s, audio.centroid, t_ms / 1000.0)
        if not np.isfinite(centroid):
            continue
        if centroid >= 4500:
            hats.append(t_ms)
        elif centroid >= 2200:
            snares.append(t_ms)
        else:
            kicks.append(t_ms)
    hats = base.compress_times_ms(hats, base.scaled_gap(24))
    snares = base.compress_times_ms(snares, base.scaled_gap(36))
    kicks = base.compress_times_ms(kicks, base.scaled_gap(46))
    return PercussionMarks(kicks, snares, hats)


def apply_stem_percussion(marks: PercussionMarks, stems: Any) -> PercussionMarks:
    kicks, snares, hats = marks.kicks, marks.snares, marks.hats
    if stems.drum_kicks_ms:
        kicks = base.compress_times_ms(stems.drum_kicks_ms, base.scaled_gap(44))
    if stems.drum_snares_ms:
        snares = base.compress_times_ms(stems.drum_snares_ms, base.scaled_gap(32))
    if stems.drum_hats_ms:
        hats = base.compress_times_ms(stems.drum_hats_ms, base.scaled_gap(22))
    return PercussionMarks(kicks, snares, hats)


@timed_stage("drums.mapping")
def build_drum_cues(
    parts: list[Any],
    *,
    part_label: Callable[[list[Any], int], str],
    drum_event_streams: dict[str, list[Any]] | None,
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    releases: list[int],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    resolved = drum_mapper.resolve_drum_streams(
        drum_event_streams,
        fallback_kicks=kicks,
        fallback_snares=snares,
        fallback_hats=hats,
        fallback_cymbals=releases,
    )
    events = list(resolved["events"])
    mapped = list(resolved["mapped_events"])
    motions = drummer_motion.build_drummer_motion(events)
    effect_cues = drum_effects.build_drum_effect_cues(events)
    cues: list[dict[str, Any]] = []
    for idx, item in enumerate(mapped):
        start_ms = int(item["timestamp_ms"])
        drum_type = str(item["drum_type"])
        effect = effect_cues[idx] if idx < len(effect_cues) else {}
        cue = {
            "performer": "drummer",
            "start_ms": start_ms,
            "end_ms": int(effect.get("end_ms", start_ms + 140)),
            "kind": drum_type,
            "section": part_label(parts, start_ms),
            "submodel": item["submodel"],
            "composite_submodels": list(item.get("composite_submodels", [item["submodel"]])),
            "velocity": item["velocity"],
            "confidence": item["confidence"],
            "frequency_band_info": item["frequency_band_info"],
            "cluster_id": item["cluster_id"],
            "source": item["source"],
            "visual_effect": effect,
        }
        if drum_type == "kick":
            cue["frames"] = ["kick_center", "kick_mid", "kick_outer"]
        elif drum_type == "snare":
            cue["frames"] = ["snare_burst"]
        elif drum_type == "hihat":
            cue["frames"] = ["hat_flash"]
        elif drum_type == "cymbal":
            cue["frames"] = ["cymbal_frame_1", "cymbal_frame_2", "cymbal_frame_3", "cymbal_frame_4"]
            cue["shimmer"] = True
        elif drum_type == "tom":
            cue["frames"] = ["tom_bounce"]
        else:
            cue["frames"] = ["drum_bus_pulse"]
        cues.append(cue)
    kit = sorted({str(item["drum_type"]) for item in mapped if item["drum_type"] != "drum_bus"})
    if any(str(item["drum_type"]) == "drum_bus" for item in mapped):
        kit.append("drum_bus")
    debug = {
        "fallback_mode": resolved["fallback_mode"],
        "counts": resolved["counts"],
        "motion_events": motions,
        "effect_cues": effect_cues,
        "mapping": mapped,
    }
    return cues, kit, debug

