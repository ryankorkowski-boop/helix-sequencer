from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.build_demo_snowman_stage_pack import build_demo_snowman_stage_pack


STAGE_PACK_MANIFEST_SCHEMA = "helix.stage_pack_export_manifest.v1"
DEFAULT_OUTPUT_PATH = Path("outputs/demo_snowman_stage_pack_manifest.json")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _cue_effect(cue: Mapping[str, Any]) -> str:
    xlights = dict(cue.get("xlights", {}) or {})
    if xlights.get("effect"):
        return str(xlights["effect"])
    visual = dict(cue.get("visual_effect", {}) or {})
    if visual.get("effect"):
        return str(visual["effect"])
    if cue.get("kind") == "phoneme_face":
        return "Faces"
    if cue.get("kind") == "floor_piano_sweep":
        return "Chase"
    return "On"


def _cue_timing_track(cue: Mapping[str, Any], performer_name: str) -> str:
    xlights = dict(cue.get("xlights", {}) or {})
    if xlights.get("timing_track"):
        return str(xlights["timing_track"])
    if performer_name in {"singer", "female_singer"}:
        return "phoneme" if cue.get("kind") == "phoneme_face" else "word"
    if performer_name == "drummer":
        return "drums"
    if performer_name == "bassist":
        return "bass"
    if performer_name == "guitarist":
        return "guitar"
    if performer_name == "floor_piano":
        return str(cue.get("source", "stage_prop"))
    return "default"


def _cue_intensity(cue: Mapping[str, Any]) -> float:
    if "intensity" in cue:
        return round(_safe_float(cue.get("intensity")), 3)
    if "velocity" in cue:
        return round(_safe_float(cue.get("velocity")), 3)
    expression = dict(cue.get("expression", {}) or {})
    if "brightness" in expression:
        return round(_safe_float(expression.get("brightness")), 3)
    visual = dict(cue.get("visual_effect", {}) or {})
    if "intensity" in visual:
        return round(_safe_float(visual.get("intensity")), 3)
    return 0.5


def _cue_confidence(cue: Mapping[str, Any]) -> float:
    if "confidence" in cue:
        return round(_safe_float(cue.get("confidence")), 3)
    return 0.5


def _row_for_cue(*, cue: Mapping[str, Any], performer_name: str, performer_kind: str, index: int) -> dict[str, Any]:
    target_submodel = str(
        dict(cue.get("xlights", {}) or {}).get("target_submodel")
        or cue.get("submodel")
        or ""
    )
    start_ms = _safe_int(cue.get("start_ms"), 0)
    end_ms = max(start_ms + 1, _safe_int(cue.get("end_ms"), start_ms + 1))
    return {
        "row_id": f"{performer_kind}:{performer_name}:{index:04d}",
        "performer_kind": performer_kind,
        "performer": performer_name,
        "role": str(cue.get("role", performer_name)),
        "kind": str(cue.get("kind", "cue")),
        "target_model": str(cue.get("target_model", performer_name)),
        "target_submodel": target_submodel,
        "effect": _cue_effect(cue),
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
        "timing_track": _cue_timing_track(cue, performer_name),
        "source": str(cue.get("source", cue.get("role", performer_name))),
        "confidence": _cue_confidence(cue),
        "intensity": _cue_intensity(cue),
        "xlights": dict(cue.get("xlights", {}) or {}),
    }


def _iter_member_rows(stage_pack: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    for member_name, member_payload in sorted(dict(stage_pack.get("band_members", {}) or {}).items()):
        for index, cue in enumerate(list(member_payload.get("reactive_cues", []) or [])):
            yield _row_for_cue(cue=cue, performer_name=member_name, performer_kind="band_member", index=index)


def _iter_prop_rows(stage_pack: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    for prop_name, prop_payload in sorted(dict(stage_pack.get("stage_props", {}) or {}).items()):
        for index, cue in enumerate(list(prop_payload.get("reactive_cues", []) or [])):
            yield _row_for_cue(cue=cue, performer_name=prop_name, performer_kind="stage_prop", index=index)


def build_stage_pack_export_manifest(stage_pack: Mapping[str, Any]) -> dict[str, Any]:
    """Flatten a reactive stage pack into export rows for xLights translation."""
    rows = sorted(
        [*_iter_member_rows(stage_pack), *_iter_prop_rows(stage_pack)],
        key=lambda row: (row["start_ms"], row["performer_kind"], row["performer"], row["target_submodel"]),
    )
    timing_tracks = sorted({row["timing_track"] for row in rows})
    target_submodels = sorted({row["target_submodel"] for row in rows if row["target_submodel"]})
    return {
        "schema": STAGE_PACK_MANIFEST_SCHEMA,
        "source_schema": stage_pack.get("schema"),
        "pack_id": stage_pack.get("pack_id"),
        "status": "stage_pack_export_manifest",
        "row_count": len(rows),
        "timing_tracks": timing_tracks,
        "target_submodels": target_submodels,
        "rows": rows,
        "validation": {
            "has_rows": bool(rows),
            "all_rows_have_targets": all(bool(row["target_submodel"]) for row in rows),
            "all_rows_have_positive_duration": all(row["duration_ms"] > 0 for row in rows),
            "includes_faces_effect": any(row["effect"] == "Faces" for row in rows),
            "includes_drum_track": "drums" in timing_tracks,
            "includes_floor_piano_hooks": any(
                row["performer"] == "floor_piano" and row["source"] == "player_piano_hook" for row in rows
            ),
        },
    }


def build_demo_stage_pack_export_manifest() -> dict[str, Any]:
    return build_stage_pack_export_manifest(build_demo_snowman_stage_pack())


def write_demo_stage_pack_export_manifest(path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    manifest = build_demo_stage_pack_export_manifest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"path": str(path), "schema": manifest["schema"], "row_count": manifest["row_count"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a flattened export manifest for the demo snowman stage pack.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    print(json.dumps(write_demo_stage_pack_export_manifest(args.output), indent=2))


if __name__ == "__main__":
    main()
