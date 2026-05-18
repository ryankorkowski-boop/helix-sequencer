from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping


EXPECTED_SCHEMA = "helix.xlights_effect_contract.v1"
SUPPORTED_EFFECT_NAMES = {"Color Wash", "On", "Bars", "Wave", "Faces", "Twinkle"}


@dataclass(frozen=True)
class XlightsContractValidationReport:
    schema: str = "helix.xlights_contract_validation.v1"
    passed: bool = True
    error_count: int = 0
    warning_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _validate_palette(idx: int, value: object, warnings: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, (list, tuple)):
        warnings.append(f"effect_placements[{idx}] palette should be a list when present.")
        return
    if len(value) < 2:
        warnings.append(f"effect_placements[{idx}] palette has fewer than two colors.")


def validate_xlights_effect_contract(payload: Mapping[str, Any]) -> XlightsContractValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    if payload.get("schema") != EXPECTED_SCHEMA:
        errors.append(f"Unexpected schema: {payload.get('schema')!r}")

    permission = dict(payload.get("permission", {}) or {})
    if not bool(permission.get("allowed", False)):
        errors.append("Render permission is not allowed.")

    placements = payload.get("effect_placements", [])
    if not isinstance(placements, list):
        errors.append("effect_placements must be a list.")
        placements = []
    if bool(payload.get("rendered", False)) and not placements:
        warnings.append("Contract is marked rendered but has no effect placements.")

    supported = dict(payload.get("supported_render_families", {}) or {})
    if not supported:
        warnings.append("supported_render_families is empty.")

    target_names: set[str] = set()
    effect_names: set[str] = set()
    previous_start = -1.0
    for idx, item in enumerate(placements):
        if not isinstance(item, Mapping):
            errors.append(f"effect_placements[{idx}] must be an object.")
            continue
        target = str(item.get("target_model", ""))
        effect_name = str(item.get("effect_name", ""))
        start = _as_float(item.get("start_time"), -1.0)
        end = _as_float(item.get("end_time"), -1.0)
        brightness = _as_float(item.get("brightness_cap"), -1.0)

        if not target:
            errors.append(f"effect_placements[{idx}] missing target_model.")
        else:
            target_names.add(target)
        if effect_name not in SUPPORTED_EFFECT_NAMES:
            errors.append(f"effect_placements[{idx}] has unsupported effect_name: {effect_name!r}")
        else:
            effect_names.add(effect_name)
        if start < 0:
            errors.append(f"effect_placements[{idx}] has negative start_time.")
        if end <= start:
            errors.append(f"effect_placements[{idx}] has end_time <= start_time.")
        if start < previous_start:
            warnings.append(f"effect_placements[{idx}] starts before previous placement; output is not sorted.")
        previous_start = start
        if brightness < 0.0 or brightness > 1.0:
            errors.append(f"effect_placements[{idx}] brightness_cap outside 0..1: {brightness}")
        elif brightness > 0.88:
            warnings.append(f"effect_placements[{idx}] brightness_cap is high: {brightness:.3f}")
        if not item.get("source_visual_intent_id"):
            errors.append(f"effect_placements[{idx}] missing source_visual_intent_id.")
        if not item.get("source_effect_family"):
            errors.append(f"effect_placements[{idx}] missing source_effect_family.")
        _validate_palette(idx, item.get("palette"), warnings)

    metrics = {
        "placement_count": len(placements),
        "unique_target_count": len(target_names),
        "unique_effect_name_count": len(effect_names),
        "skipped_count": int(payload.get("skipped_count", 0) or 0),
        "rendered": bool(payload.get("rendered", False)),
    }
    return XlightsContractValidationReport(
        passed=not errors,
        error_count=len(errors),
        warning_count=len(warnings),
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )


def validate_xlights_effect_contract_file(path: str | Path) -> XlightsContractValidationReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        return XlightsContractValidationReport(
            passed=False,
            error_count=1,
            errors=["Contract file root must be a JSON object."],
        )
    return validate_xlights_effect_contract(payload)
