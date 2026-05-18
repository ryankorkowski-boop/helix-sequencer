from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from helix_intent.render_gate import evaluate_render_permission


SUPPORTED_RENDER_FAMILIES = {
    "soft_wash": "Color Wash",
    "outline_pulse": "On",
    "energy_wave": "Bars",
    "directional_sweep": "Wave",
    "melody_trail": "Wave",
    "matrix_pulse": "Bars",
    "lyric_pulse": "Faces",
    "character_hit": "On",
    "beat_pulse": "On",
    "sparkle_accent": "Twinkle",
    "support_pulse": "On",
}

PALETTE_BY_COLOR_STRATEGY = {
    "classic_christmas": ("#ff0000", "#00ff66", "#ffffff"),
    "electric_winter": ("#2bd9ff", "#5a6cff", "#ffffff"),
    "cinematic_blue_gold": ("#1f5f8b", "#ffcf4a", "#fff8dc"),
    "party_neon": ("#ff4d8d", "#00f5d4", "#7f52ff"),
    "spatial_helix": ("#2bd9ff", "#7f52ff", "#ffffff"),
    "warm_white_gold": ("#fff8dc", "#ffcf4a", "#ffffff"),
    "default": ("#ffffff", "#00ffff", "#ff00ff"),
}


@dataclass(frozen=True)
class XlightsEffectPlacement:
    start_time: float
    end_time: float
    target_model: str
    effect_name: str
    render_style: str
    brightness_cap: float
    source_visual_intent_id: str
    source_effect_family: str
    color_strategy: str = "default"
    curve_strategy: str = "section_envelope"
    palette: tuple[str, str, str] = PALETTE_BY_COLOR_STRATEGY["default"]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["palette"] = list(self.palette)
        return data


@dataclass(frozen=True)
class XlightsEffectContractReport:
    schema: str = "helix.xlights_effect_contract.v1"
    rendered: bool = False
    output_json: str = ""
    placement_count: int = 0
    skipped_count: int = 0
    skipped_effect_families: list[str] = field(default_factory=list)
    permission: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _visual_intent_map(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    out: dict[str, Mapping[str, Any]] = {}
    for item in list(plan.get("visual_intents", []) or []):
        if isinstance(item, Mapping):
            intent_id = str(item.get("id", ""))
            if intent_id:
                out[intent_id] = item
    return out


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _palette_for_visual_intent(visual: Mapping[str, Any]) -> tuple[str, str, str]:
    raw = str(visual.get("color_strategy", "default") or "default").lower()
    return PALETTE_BY_COLOR_STRATEGY.get(raw, PALETTE_BY_COLOR_STRATEGY["default"])


def build_xlights_effect_contract(
    placement_plan: Mapping[str, Any],
    *,
    minimum_quality_score: float = 0.6,
) -> tuple[list[XlightsEffectPlacement], XlightsEffectContractReport]:
    permission = evaluate_render_permission(placement_plan, minimum_quality_score=minimum_quality_score)
    if not permission.allowed:
        return [], XlightsEffectContractReport(rendered=False, permission=permission.to_dict())

    intents = _visual_intent_map(placement_plan)
    placements: list[XlightsEffectPlacement] = []
    skipped: list[str] = []
    for item in list(placement_plan.get("prop_effect_intents", []) or []):
        if not isinstance(item, Mapping):
            continue
        family = str(item.get("effect_family", ""))
        effect_name = SUPPORTED_RENDER_FAMILIES.get(family)
        if effect_name is None:
            skipped.append(family or "unknown")
            continue
        intent_id = str(item.get("visual_intent_id", ""))
        visual = intents.get(intent_id, {})
        start_time = _as_float(visual.get("start_time"), 0.0)
        end_time = _as_float(visual.get("end_time"), start_time)
        if end_time <= start_time:
            end_time = start_time + 0.25
        placements.append(
            XlightsEffectPlacement(
                start_time=round(start_time, 4),
                end_time=round(end_time, 4),
                target_model=str(item.get("target_prop", "")),
                effect_name=effect_name,
                render_style=str(item.get("render_style", "per_model")),
                brightness_cap=round(_as_float(item.get("brightness_cap"), 0.6), 4),
                source_visual_intent_id=intent_id,
                source_effect_family=family,
                color_strategy=str(visual.get("color_strategy", "default") or "default"),
                curve_strategy=str(item.get("curve_type", visual.get("curve_strategy", "section_envelope")) or "section_envelope"),
                palette=_palette_for_visual_intent(visual),
            )
        )
    return placements, XlightsEffectContractReport(
        rendered=True,
        placement_count=len(placements),
        skipped_count=len(skipped),
        skipped_effect_families=sorted(set(skipped)),
        permission=permission.to_dict(),
    )


def write_xlights_effect_contract(
    placement_plan: Mapping[str, Any],
    output_path: str | Path,
    *,
    minimum_quality_score: float = 0.6,
) -> XlightsEffectContractReport:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    placements, report = build_xlights_effect_contract(placement_plan, minimum_quality_score=minimum_quality_score)
    payload = report.to_dict() | {
        "output_json": str(path),
        "effect_placements": [placement.to_dict() for placement in placements],
        "supported_render_families": dict(SUPPORTED_RENDER_FAMILIES),
        "palette_by_color_strategy": {key: list(value) for key, value in PALETTE_BY_COLOR_STRATEGY.items()},
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return XlightsEffectContractReport(
        rendered=report.rendered,
        output_json=str(path),
        placement_count=report.placement_count,
        skipped_count=report.skipped_count,
        skipped_effect_families=report.skipped_effect_families,
        permission=report.permission,
    )
