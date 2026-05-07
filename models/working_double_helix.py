from __future__ import annotations

from typing import Any, Iterable, Mapping

from models.helixia_double_helix import build_giant_double_helix


WORKING_DOUBLE_HELIX_SCHEMA = "helixia.working_double_helix.v1"


SOURCE_TO_HELIX_TARGET = {
    "singer": "HELIXIA_DNA_CORE",
    "female_singer": "HELIXIA_DNA_CORE",
    "guitarist": "HELIXIA_DNA_STRAND_A",
    "bassist": "HELIXIA_DNA_STRAND_B",
    "drummer": "HELIXIA_DNA_RUNGS",
    "floor_piano": "HELIXIA_DNA_RUNG_EVEN",
}


TRACK_TO_EFFECT = {
    "phoneme": "Sparkle",
    "word": "On",
    "guitar": "Chase",
    "bass": "Chase",
    "drums": "Bars",
    "notes": "On",
    "phrase": "Color Wash",
    "beat": "On",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.5) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_working_double_helix() -> dict[str, Any]:
    """Build the static working double-helix package."""
    geometry = build_giant_double_helix()
    return {
        "schema": WORKING_DOUBLE_HELIX_SCHEMA,
        "role": "giant_double_helix",
        "status": "working_centerpiece_slice",
        "model_id": geometry["model_id"],
        "display_name": geometry["display_name"],
        "geometry": geometry,
        "required_submodels": sorted(geometry["submodels"]),
        "xlights_export_contract": dict(geometry["xlights_export_contract"]),
        "validation": {
            "has_geometry": bool(geometry),
            "has_required_submodels": all(bool(geometry["submodels"].get(name)) for name in geometry["submodels"]),
            "has_audio_in_zone": bool(geometry["submodels"].get("HELIXIA_DNA_TOP_INPUT")),
            "has_lights_out_zone": bool(geometry["submodels"].get("HELIXIA_DNA_BOTTOM_OUTPUT")),
        },
    }


def _cue_to_helix(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    performer = str(row.get("performer", ""))
    timing_track = str(row.get("timing_track", ""))
    source = str(row.get("source", performer))
    target = SOURCE_TO_HELIX_TARGET.get(performer, "HELIXIA_DNA_CORE")
    if source == "phrase_hit" or timing_track == "phrase":
        target = "HELIXIA_DNA_FULL"
    if source == "audio_in":
        target = "HELIXIA_DNA_TOP_INPUT"
    start_ms = _safe_int(row.get("start_ms"), 0)
    end_ms = max(start_ms + 1, _safe_int(row.get("end_ms"), start_ms + 160))
    intensity = max(0.12, min(1.0, _safe_float(row.get("intensity"), 0.5)))
    confidence = max(0.0, min(1.0, _safe_float(row.get("confidence"), 0.5)))
    return {
        "cue_id": f"helix_reactive_{index:04d}",
        "performer": "giant_double_helix",
        "source_performer": performer,
        "source_target_submodel": str(row.get("target_submodel", "")),
        "role": "helix_centerpiece_reaction",
        "kind": f"helix_from_{performer or 'unknown'}",
        "start_ms": start_ms,
        "end_ms": end_ms,
        "submodel": target,
        "effect": TRACK_TO_EFFECT.get(timing_track, str(row.get("effect", "On"))),
        "timing_track": timing_track or "stage_manifest",
        "source": source,
        "intensity": round(intensity, 3),
        "confidence": round(confidence, 3),
        "xlights": {
            "effect": TRACK_TO_EFFECT.get(timing_track, str(row.get("effect", "On"))),
            "timing_track": timing_track or "stage_manifest",
            "target_submodel": target,
        },
        "intent": _intent_for_target(target, performer, source),
    }


def _intent_for_target(target: str, performer: str, source: str) -> str:
    if target == "HELIXIA_DNA_STRAND_A":
        return "guitar and melodic motion spiral through strand A"
    if target == "HELIXIA_DNA_STRAND_B":
        return "bass and low-frequency motion spiral through strand B"
    if target == "HELIXIA_DNA_RUNGS":
        return "drum hits pulse the colored DNA rungs"
    if target == "HELIXIA_DNA_RUNG_EVEN":
        return "floor-piano key presses flash alternating helix rungs"
    if target == "HELIXIA_DNA_FULL":
        return "phrase hit resolves across the full double helix"
    if target == "HELIXIA_DNA_TOP_INPUT":
        return "audio input enters the untwisted top zone"
    return f"{performer or source} intelligence sparkles through the helix core"


def _entry_audio_in_cue(first_start_ms: int = 0) -> dict[str, Any]:
    return {
        "cue_id": "helix_audio_in_0000",
        "performer": "giant_double_helix",
        "source_performer": "helix_input",
        "source_target_submodel": "audio_input",
        "role": "audio_in_open",
        "kind": "audio_in_top_input",
        "start_ms": max(0, first_start_ms - 300),
        "end_ms": max(1, first_start_ms + 220),
        "submodel": "HELIXIA_DNA_TOP_INPUT",
        "effect": "On",
        "timing_track": "phrase",
        "source": "audio_in",
        "intensity": 0.72,
        "confidence": 1.0,
        "xlights": {"effect": "On", "timing_track": "phrase", "target_submodel": "HELIXIA_DNA_TOP_INPUT"},
        "intent": "audio input enters the untwisted top zone",
    }


def _exit_lights_out_cue(last_end_ms: int) -> dict[str, Any]:
    return {
        "cue_id": "helix_lights_out_9999",
        "performer": "giant_double_helix",
        "source_performer": "helix_output",
        "source_target_submodel": "lights_output",
        "role": "lights_out_resolve",
        "kind": "lights_out_bottom_output",
        "start_ms": max(0, last_end_ms - 280),
        "end_ms": max(last_end_ms + 1, last_end_ms + 420),
        "submodel": "HELIXIA_DNA_BOTTOM_OUTPUT",
        "effect": "Color Wash",
        "timing_track": "phrase",
        "source": "lights_out",
        "intensity": 0.9,
        "confidence": 1.0,
        "xlights": {"effect": "Color Wash", "timing_track": "phrase", "target_submodel": "HELIXIA_DNA_BOTTOM_OUTPUT"},
        "intent": "finished lights-out output resolves at the base of the sculpture",
    }


def build_reactive_double_helix_from_manifest_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build double-helix reactive cues from flattened stage-pack manifest rows."""
    payload = build_working_double_helix()
    manifest_rows = sorted(list(rows), key=lambda row: (_safe_int(row.get("start_ms"), 0), str(row.get("performer", ""))))
    cues = [_cue_to_helix(row, index) for index, row in enumerate(manifest_rows)]
    if manifest_rows:
        first_start = min(_safe_int(row.get("start_ms"), 0) for row in manifest_rows)
        last_end = max(_safe_int(row.get("end_ms"), 0) for row in manifest_rows)
        cues.insert(0, _entry_audio_in_cue(first_start))
        cues.append(_exit_lights_out_cue(last_end))
    geometry_submodels = set(payload["geometry"]["submodels"])
    cue_targets = sorted({cue["submodel"] for cue in cues})
    source_performers = sorted({cue["source_performer"] for cue in cues})
    payload.update(
        {
            "status": "reactive_centerpiece_slice",
            "reactive_cues": cues,
            "reactive_debug": {
                "schema": "helixia.working_double_helix.reactivity.v1",
                "source_row_count": len(manifest_rows),
                "cue_count": len(cues),
                "cue_targets": cue_targets,
                "source_performers": source_performers,
                "uses_singers": any(name in source_performers for name in ("singer", "female_singer")),
                "uses_guitar": "guitarist" in source_performers,
                "uses_bass": "bassist" in source_performers,
                "uses_drums": "drummer" in source_performers,
                "uses_floor_piano": "floor_piano" in source_performers,
                "has_audio_in_cue": any(cue["source"] == "audio_in" for cue in cues),
                "has_lights_out_cue": any(cue["source"] == "lights_out" for cue in cues),
            },
            "validation": {
                **dict(payload["validation"]),
                "has_reactive_cues": bool(cues),
                "reactive_cues_target_existing_submodels": all(cue["submodel"] in geometry_submodels for cue in cues),
                "has_stage_pack_source_rows": bool(manifest_rows),
                "has_audio_in_and_lights_out": any(cue["source"] == "audio_in" for cue in cues)
                and any(cue["source"] == "lights_out" for cue in cues),
            },
        }
    )
    return payload


def build_reactive_double_helix_from_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Build double-helix reactive cues from a full stage-pack export manifest."""
    return build_reactive_double_helix_from_manifest_rows(list(manifest.get("rows", []) or []))
