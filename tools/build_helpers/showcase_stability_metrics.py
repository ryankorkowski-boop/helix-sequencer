"""Showcase stability metrics (Phase 6).

This module augments Phase 5 calibration reports with stability indicators.

It is fully deterministic and uses only synthetic calibration outputs.
No renderer coupling. No training data. No external ingestion.

Metrics:
- Winner Volatility Index (WVI)
- Flip Threshold Bias (FTB)
- Pass Stability Ratio (PSR)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping, Optional

from tools.build_helpers.showcase_calibration import run_calibration_report


@dataclass(frozen=True)
class StabilityMetrics:
    winner_volatility_index: int
    flip_threshold_bias: Optional[float]
    pass_stability_ratio: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def compute_stability_metrics(bias_sweep: Iterable[Mapping[str, Any]]) -> StabilityMetrics:
    sweep: List[Mapping[str, Any]] = list(bias_sweep)
    if not sweep:
        return StabilityMetrics(
            winner_volatility_index=0,
            flip_threshold_bias=None,
            pass_stability_ratio=1.0,
        )

    winners = [entry.get("winner") for entry in sweep]
    transitions = 0
    flip_threshold = None

    last = winners[0]
    for bias_entry, winner in zip(sweep, winners):
        if winner != last:
            transitions += 1
            if flip_threshold is None:
                flip_threshold = float(bias_entry.get("bias", 0.0))
            last = winner

    baseline_pass = set(sweep[0].get("passed_variants", []) or [])
    stable_steps = 0
    for entry in sweep:
        if set(entry.get("passed_variants", []) or []) == baseline_pass:
            stable_steps += 1

    psr = stable_steps / len(sweep)

    return StabilityMetrics(
        winner_volatility_index=transitions,
        flip_threshold_bias=flip_threshold,
        pass_stability_ratio=round(psr, 4),
    )


def run_calibration_with_stability(preset: str = "showcase") -> Dict[str, Any]:
    """Run Phase 5 calibration and attach Phase 6 stability metrics."""

    report = run_calibration_report(preset=preset)
    sweep = report.get("bias_sweep", [])
    metrics = compute_stability_metrics(sweep)

    augmented = dict(report)
    augmented["stability_metrics"] = metrics.as_dict()
    return augmented
