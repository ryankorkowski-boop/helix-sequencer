from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from models.helixia_double_helix import build_giant_double_helix


DOUBLE_HELIX_XLIGHTS_PLAN_SCHEMA = "helixia.double_helix_xlights_plan.v1"
DEFAULT_OUTPUT_PATH = Path("outputs/helixia_double_helix_xlights_plan.json")


def _submodel_line_range(start: int, count: int) -> str:
    end = start + max(0, count - 1)
    return f"{start}-{end}"


def _build_submodel_plan(double_helix: Mapping[str, Any]) -> list[dict[str, Any]]:
    cursor = 1
    rows: list[dict[str, Any]] = []
    for name in sorted(dict(double_helix.get("submodels", {}) or {})):
        nodes = list(double_helix["submodels"][name])
        rows.append(
            {
                "name": name,
                "node_count": len(nodes),
                "line0": _submodel_line_range(cursor, len(nodes)),
                "source_node_ids": nodes,
            }
        )
        cursor += len(nodes)
    return rows


def _effect_placements() -> list[dict[str, Any]]:
    return [
        {
            "placement_id": "helix_audio_input_open",
            "target_submodel": "HELIXIA_DNA_TOP_INPUT",
            "effect": "On",
            "timing_track": "phrase",
            "start_ms": 0,
            "end_ms": 500,
            "source": "audio_in",
            "intent": "loose input particles enter the untwisted top zone",
        },
        {
            "placement_id": "helix_strand_a_spiral",
            "target_submodel": "HELIXIA_DNA_STRAND_A",
            "effect": "Chase",
            "timing_track": "guitar",
            "start_ms": 500,
            "end_ms": 1800,
            "source": "guitar_motion",
            "intent": "right-hand musical motion spirals through strand A",
        },
        {
            "placement_id": "helix_strand_b_spiral",
            "target_submodel": "HELIXIA_DNA_STRAND_B",
            "effect": "Chase",
            "timing_track": "bass",
            "start_ms": 500,
            "end_ms": 1800,
            "source": "bass_motion",
            "intent": "low-frequency motion spirals through strand B",
        },
        {
            "placement_id": "helix_rung_pulses",
            "target_submodel": "HELIXIA_DNA_RUNGS",
            "effect": "Bars",
            "timing_track": "drums",
            "start_ms": 250,
            "end_ms": 2500,
            "source": "drum_hits",
            "intent": "drum hits pulse the colored DNA rungs",
        },
        {
            "placement_id": "helix_core_vocal_sparkle",
            "target_submodel": "HELIXIA_DNA_CORE",
            "effect": "Sparkle",
            "timing_track": "phoneme",
            "start_ms": 100,
            "end_ms": 2600,
            "source": "vocal_phonemes",
            "intent": "vocal/lyric intelligence sparkles through the central twist",
        },
        {
            "placement_id": "helix_output_resolve",
            "target_submodel": "HELIXIA_DNA_BOTTOM_OUTPUT",
            "effect": "Color Wash",
            "timing_track": "phrase",
            "start_ms": 2400,
            "end_ms": 3000,
            "source": "lights_out_resolution",
            "intent": "finished output zone resolves into polished synchronized light",
        },
    ]


def build_double_helix_xlights_plan(double_helix: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build an xLights-facing custom-model plan for the giant double helix.

    This does not mutate the generated xlights_rgbeffects.xml yet. It gives the
    future XML writer an explicit model contract: model attrs, submodel ranges,
    timing tracks, effect placements, and validation gates.
    """
    double_helix = double_helix or build_giant_double_helix()
    submodel_plan = _build_submodel_plan(double_helix)
    effect_placements = _effect_placements()
    must_export = set(double_helix["xlights_export_contract"]["must_export_submodels"])
    planned_submodels = {row["name"] for row in submodel_plan}
    timing_tracks = sorted({placement["timing_track"] for placement in effect_placements})
    return {
        "schema": DOUBLE_HELIX_XLIGHTS_PLAN_SCHEMA,
        "model_id": double_helix["model_id"],
        "display_name": double_helix["display_name"],
        "status": "xlights_custom_model_plan",
        "model_requirements": {
            "name": "HELIXIA_GIANT_DOUBLE_HELIX",
            "DisplayAs": "Custom",
            "target_model_type": "custom_model_with_3d_submodels",
            "node_order": double_helix["xlights_export_contract"]["node_order"],
            "strand_a_nodes": len(double_helix["strand_a"]),
            "strand_b_nodes": len(double_helix["strand_b"]),
            "rung_count": len(double_helix["rungs"]),
            "estimated_custom_nodes": len(double_helix["submodels"]["HELIXIA_DNA_FULL"]),
            "bounds_ft": dict(double_helix["bounds_ft"]),
        },
        "submodel_requirements": submodel_plan,
        "timing_tracks_required": timing_tracks,
        "effect_placements": effect_placements,
        "warnings": [
            "Plan only: do not merge into committed xlights_rgbeffects.xml until custom 3D node-string serialization is implemented.",
            "Submodel line ranges are deterministic planning ranges, not final xLights custom model node buffer coordinates.",
        ],
        "validation": {
            "has_model_requirements": True,
            "all_required_submodels_planned": must_export.issubset(planned_submodels),
            "has_effect_placements": bool(effect_placements),
            "all_effect_targets_planned": all(placement["target_submodel"] in planned_submodels for placement in effect_placements),
            "has_audio_in_zone": "HELIXIA_DNA_TOP_INPUT" in planned_submodels,
            "has_lights_out_zone": "HELIXIA_DNA_BOTTOM_OUTPUT" in planned_submodels,
            "has_drum_rung_plan": any(
                placement["target_submodel"] == "HELIXIA_DNA_RUNGS" and placement["timing_track"] == "drums"
                for placement in effect_placements
            ),
        },
    }


def write_double_helix_xlights_plan(path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    plan = build_double_helix_xlights_plan()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return {
        "path": str(path),
        "schema": plan["schema"],
        "model_id": plan["model_id"],
        "effect_count": len(plan["effect_placements"]),
        "submodel_count": len(plan["submodel_requirements"]),
        "validation": plan["validation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the xLights-facing plan for the Helixia giant double helix.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    print(json.dumps(write_double_helix_xlights_plan(args.output), indent=2))


if __name__ == "__main__":
    main()
