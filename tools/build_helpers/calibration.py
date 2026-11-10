from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from tools.build_helpers.variants import QualityGatePreset, quality_gate_preset


@dataclass(frozen=True)
class EngineQualityGateConfig:
    preset: str
    min_quality_score: float
    min_audit_score: float
    max_rejected_effects: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def engine_quality_gate_config(preset_name: str | None) -> EngineQualityGateConfig:
    preset: QualityGatePreset = quality_gate_preset(preset_name)
    return EngineQualityGateConfig(
        preset=preset.name,
        min_quality_score=preset.min_quality_score,
        min_audit_score=preset.min_audit_score,
        max_rejected_effects=preset.max_rejected_effects,
    )


def apply_quality_gate_overrides(
    base: EngineQualityGateConfig,
    *,
    min_quality_score: float | None = None,
    min_audit_score: float | None = None,
    max_rejected_effects: int | None = None,
) -> EngineQualityGateConfig:
    return EngineQualityGateConfig(
        preset=base.preset,
        min_quality_score=base.min_quality_score if min_quality_score is None else float(min_quality_score),
        min_audit_score=base.min_audit_score if min_audit_score is None else float(min_audit_score),
        max_rejected_effects=base.max_rejected_effects if max_rejected_effects is None else int(max_rejected_effects),
    )


def engine_threshold_kwargs(config: EngineQualityGateConfig) -> dict[str, Any]:
    """Return kwargs matching existing variant-quality helper parameters."""
    return {
        "min_quality_score": config.min_quality_score,
        "min_audit_score": config.min_audit_score,
        "max_rejected_effects": config.max_rejected_effects,
    }


def engine_threshold_cli_args(config: EngineQualityGateConfig) -> list[str]:
    """Return explicit threshold args for existing engine CLI compatibility.

    The current engine still uses historical threshold flag names. Public-facing
    preset names should remain `general`, `showcase`, and `pro`.
    """
    return [
        "--vendor-min-quality-score",
        f"{config.min_quality_score:.1f}",
        "--vendor-min-audit-score",
        f"{config.min_audit_score:.1f}",
        "--vendor-max-rejected-effects",
        str(config.max_rejected_effects),
    ]
