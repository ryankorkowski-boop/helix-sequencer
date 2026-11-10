"""
Phase 5: Showcase Calibration Harness

This module provides a deterministic synthetic calibration harness
for evaluating ranking stability under controlled `showcase_bias` sweeps.

Design goals:
- Fully synthetic inputs
- No renderer coupling
- No training data
- Deterministic repeatability
- JSON-serializable output
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict

from tools.build_helpers.explainable_variant_scoring import rank_variants


@dataclass(frozen=True)
class BiasSweepResult:
    bias: float
    winner: str | None
    passed_variants: List[str]

    def as_dict(self) -> dict:
        return asdict(self)


def generate_synthetic_variants() -> List[dict]:
    """
    Generate a deterministic synthetic variant set.
    These are intentionally structured to create near-boundary
    ranking conditions.
    """
    base = {
        "quality_score": 95.0,
        "audit_score": 88.0,
        "rejected_effects": 9000,
        "restraint": {"score": 0.9},
        "section_identity": {"score": 0.85},
        "palette_discipline": {"score": 0.9},
        "motif_memory": {"score": 0.8},
        "prop_roles": {"score": 0.85},
        "manual_lock_respect": {"score": 1.0},
    }

    strong = dict(base)
    strong.update({
        "variant_id": "strong",
        "showcase_score": 0.55,
    })

    artistic = dict(base)
    artistic.update({
        "variant_id": "artistic",
        "palette_discipline": {"score": 0.7},
        "showcase_score": 0.95,
    })

    safe = dict(base)
    safe.update({
        "variant_id": "safe",
        "quality_score": 93.5,
        "showcase_score": 0.4,
    })

    return [strong, artistic, safe]


def sweep_bias(
    preset: str = "showcase",
    step: float = 0.05,
) -> List[BiasSweepResult]:
    """
    Sweep showcase_bias from 0.0 up to preset cap.
    """
    variants = generate_synthetic_variants()

    # Determine cap via ranking with large requested bias
    max_probe = rank_variants(
        variants,
        preset=preset,
        weights={"showcase_bias": 1.0},
    )

    # Extract actual cap indirectly by observing clamp behavior
    # (since clamp is enforced inside scoring logic)
    cap = 0.40 if preset == "showcase" else 0.25

    results: List[BiasSweepResult] = []

    bias = 0.0
    while bias <= cap + 1e-9:
        report = rank_variants(
            variants,
            preset=preset,
            weights={"showcase_bias": round(bias, 4)},
        )

        passed = [v.variant_id for v in report.variants if v.passed]

        results.append(
            BiasSweepResult(
                bias=round(bias, 4),
                winner=report.winner,
                passed_variants=passed,
            )
        )

        bias += step

    return results


def run_calibration_report(preset: str = "showcase") -> Dict:
    """
    Produce structured calibration report.
    """
    sweep = sweep_bias(preset=preset)

    winner_transitions = []
    last_winner = None

    for entry in sweep:
        if entry.winner != last_winner:
            winner_transitions.append({
                "bias": entry.bias,
                "winner": entry.winner,
            })
            last_winner = entry.winner

    return {
        "preset": preset,
        "bias_sweep": [e.as_dict() for e in sweep],
        "winner_transitions": winner_transitions,
    }
