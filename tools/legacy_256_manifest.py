from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping


EXPECTED_SCHEMA = "helix.legacy_256_manifest.v1"


@dataclass(frozen=True)
class Legacy256ManifestValidation:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_legacy_256_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Legacy 256 manifest root must be an object")
    return payload


def validate_legacy_256_manifest(payload: Mapping[str, Any]) -> Legacy256ManifestValidation:
    errors: list[str] = []
    warnings: list[str] = []

    if payload.get("schema") != EXPECTED_SCHEMA:
        errors.append(f"Unexpected schema: {payload.get('schema')!r}")
    if int(payload.get("channel_count", 0) or 0) != 256:
        errors.append("channel_count must be 256")
    if not payload.get("fixture_id"):
        errors.append("fixture_id is required")

    paths = payload.get("paths", {}) or {}
    if not isinstance(paths, Mapping):
        errors.append("paths must be an object")
        paths = {}
    for key in ("local_source_lms_dir", "local_audio_dir", "converted_template_xsq", "converted_layout_file"):
        if not paths.get(key):
            errors.append(f"paths.{key} is required")

    permission = payload.get("permission_status", {}) or {}
    if not isinstance(permission, Mapping):
        errors.append("permission_status must be an object")
        permission = {}
    if permission.get("source_lms_commit_allowed") is True:
        warnings.append("source_lms_commit_allowed is true; verify written permission before committing assets")
    if permission.get("source_lms_local_only_by_default") is not True:
        warnings.append("source_lms_local_only_by_default should remain true unless permission is documented")

    goal = payload.get("quality_goal", {}) or {}
    if not isinstance(goal, Mapping):
        errors.append("quality_goal must be an object")
        goal = {}
    if float(goal.get("min_quality_score", 0.0) or 0.0) < 90.0:
        warnings.append("min_quality_score is below the normal Helix quality bar")
    if int(goal.get("max_rejected_effects", 999999) or 999999) > 28000:
        warnings.append("max_rejected_effects exceeds the general quality gate")

    rules = payload.get("placement_rules", {}) or {}
    if isinstance(rules, Mapping):
        required_true = [
            "avoid_pixel_only_effects",
            "prefer_ac_safe_effects",
            "prefer_low_rejected_effect_count",
            "limit_full_layout_flashes",
        ]
        for key in required_true:
            if rules.get(key) is not True:
                warnings.append(f"placement_rules.{key} should be true for legacy 256 calibration")
    else:
        errors.append("placement_rules must be an object")

    metrics = {
        "channel_count": int(payload.get("channel_count", 0) or 0),
        "channel_family_count": len(list(payload.get("channel_families", []) or [])),
        "profile_direction_count": len(list(payload.get("profile_direction", []) or [])),
    }
    return Legacy256ManifestValidation(
        passed=not errors,
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )


def validate_legacy_256_manifest_file(path: str | Path) -> Legacy256ManifestValidation:
    return validate_legacy_256_manifest(load_legacy_256_manifest(path))
