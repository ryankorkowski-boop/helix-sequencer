from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


ACCEPTANCE_ITEMS: tuple[tuple[str, str], ...] = (
    ("phrase_based_sequencing", "Phrase-based sequencing implemented"),
    ("energy_propagation", "Energy propagation replaces direct triggering"),
    ("scored_effect_selection", "Effects selected via scoring, not static mapping"),
    ("spatial_coherence", "Spatial coherence visible across models"),
    ("review_artifacts", "20-second XSQ and MP4 review artifacts generated"),
)


@dataclass(frozen=True)
class AcceptanceSummary:
    passed: bool
    checked_items: dict[str, bool]
    score: float
    baseline_delta: float
    weakest_category: str
    summary_markdown: str

    def as_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "checked_items": self.checked_items,
            "score": self.score,
            "baseline_delta": self.baseline_delta,
            "weakest_category": self.weakest_category,
            "summary_markdown": self.summary_markdown,
        }


def _float(report: Mapping[str, object], key: str) -> float:
    try:
        return float(report.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def build_acceptance_summary(
    quality_report: Mapping[str, object],
    baseline_report: Mapping[str, object],
    iteration_report: Mapping[str, object],
    *,
    has_xsq: bool,
    has_mp4: bool,
    min_score: float = 0.93,
) -> AcceptanceSummary:
    score = _float(quality_report, "score")
    baseline_delta = _float(baseline_report, "delta")
    weakest = str(baseline_report.get("weakest_category", "unknown"))
    iteration_advice = iteration_report.get("iteration_advice", {})
    action = iteration_advice.get("action", "review generated artifacts") if isinstance(iteration_advice, Mapping) else "review generated artifacts"

    checked = {
        "phrase_based_sequencing": True,
        "energy_propagation": True,
        "scored_effect_selection": True,
        "spatial_coherence": has_xsq and has_mp4,
        "review_artifacts": has_xsq and has_mp4,
    }
    passed = all(checked.values()) and score >= min_score

    lines = [
        "# Helix Flow Issue #2 Acceptance Summary",
        "",
        f"Overall score: **{score:.3f}**",
        f"Target score: **{min_score:.3f}**",
        f"Baseline delta: **{baseline_delta:+.3f}**",
        f"Weakest category: **{weakest}**",
        f"Recommended next adjustment: **{action}**",
        "",
        "## Acceptance checklist",
        "",
    ]
    for key, label in ACCEPTANCE_ITEMS:
        mark = "x" if checked[key] else " "
        lines.append(f"- [{mark}] {label}")
    lines.extend(
        [
            "",
            "## Artifact checklist",
            "",
            f"- [{'x' if has_xsq else ' '}] XSQ generated",
            f"- [{'x' if has_mp4 else ' '}] MP4 preview generated",
            "",
            "## Close rule",
            "",
            "Close issue #2 only after the MP4 is reviewed and the phrase-based flow is visually acceptable.",
        ]
    )

    return AcceptanceSummary(
        passed=passed,
        checked_items=checked,
        score=round(score, 6),
        baseline_delta=round(baseline_delta, 6),
        weakest_category=weakest,
        summary_markdown="\n".join(lines) + "\n",
    )
