"""Explicit gate helpers for the experimental Birdsong v2 overlay.

Birdsong v2 is a separate generative overlay from the older Birdsong/v1 layer.
Keep this gate small and dependency-free so the runtime can decide v2 behavior
without accidentally coupling it to legacy Birdsong flags.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BirdsongV2GateConfig:
    """Conservative runtime gate for the experimental Birdsong v2 path."""

    enabled: bool = False
    auto: bool = False
    confidence: float = 0.0
    min_confidence: float = 0.45


def _finite_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def should_enable_birdsong_v2(config: BirdsongV2GateConfig) -> bool:
    """Return True only when v2 is explicitly enabled or safely auto-enabled.

    The legacy Birdsong/v1 flags should not be passed here. Callers must map
    dedicated v2 flags into this config so a normal `--birdsong` run does not
    silently activate the experimental v2 generator.
    """

    if bool(config.enabled):
        return True
    if not bool(config.auto):
        return False
    confidence = _finite_float(config.confidence, 0.0)
    min_confidence = _finite_float(config.min_confidence, 0.45)
    return confidence >= min_confidence


def describe_birdsong_v2_gate(config: BirdsongV2GateConfig) -> str:
    """Return a stable reason string for logs/reports/tests."""

    if bool(config.enabled):
        return "explicit"
    if not bool(config.auto):
        return "disabled"
    confidence = _finite_float(config.confidence, 0.0)
    min_confidence = _finite_float(config.min_confidence, 0.45)
    if confidence >= min_confidence:
        return "auto_confident"
    return "auto_below_threshold"
