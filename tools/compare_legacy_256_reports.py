from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class Legacy256ReportSummary:
    label: str
    path: str
    quality_score: float = 0.0
    audit_score: float = 0.0
    rejected_effects: int = 0
    shortlist_score: float = 0.0
    musical_coherence: float = 0.0
    section_coverage: float = 0.0
    overlap_ratio: float = 0.0
    clutter_ratio: float = 0.0
    coverage_score: float = 0.0
    structure_score: float = 0.0
    family_diversity_score: float = 0.0
    comparison_score: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Legacy256ComparisonReport:
    schema: str = "helix.legacy_256_comparison.v1"
    winner: str = ""
    summaries: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _audit_final(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    audit = payload.get("audit", {}) or {}
    if isinstance(audit, Mapping) and isinstance(audit.get("final"), Mapping):
        return audit.get("final", {}) or {}
    return audit if isinstance(audit, Mapping) else {}


def _comparison_score(summary: Legacy256ReportSummary) -> float:
    # Legacy 256 scoring values cleanliness and musical/section discipline over density.
    rejected_penalty = min(18.0, max(0, summary.rejected_effects - 2000) / 1000.0)
    clutter_penalty = min(10.0, summary.clutter_ratio * 42.0)
    overlap_penalty = min(8.0, summary.overlap_ratio * 45.0)
    score = (
        summary.quality_score * 0.28
        + summary.audit_score * 0.20
        + summary.musical_coherence * 0.16
        + (summary.section_coverage * 100.0) * 0.12
        + summary.coverage_score * 0.08
        + summary.structure_score * 0.06
        + summary.family_diversity_score * 0.05
        + summary.shortlist_score * 0.05
        - rejected_penalty
        - clutter_penalty
        - overlap_penalty
    )
    return round(max(0.0, score), 4)


def summarize_report(path: str | Path, label: str | None = None) -> Legacy256ReportSummary:
    report_path = Path(path)
    warnings: list[str] = []
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Report root must be an object: {report_path}")

    quality = payload.get("quality", {}) or {}
    component_scores = quality.get("component_scores", {}) if isinstance(quality, Mapping) else {}
    audit = _audit_final(payload)
    validation = payload.get("validation", {}) or {}
    shortlist = payload.get("shortlist", {}) or {}

    summary = Legacy256ReportSummary(
        label=label or report_path.stem.replace(".report", ""),
        path=str(report_path),
        quality_score=_as_float(_nested(payload, "quality", "score")),
        audit_score=_as_float(audit.get("score")),
        rejected_effects=_as_int(_nested(payload, "validation", "rejected_effects_count")),
        shortlist_score=_as_float(shortlist.get("score") or payload.get("shortlist_score")),
        musical_coherence=_as_float(audit.get("musical_coherence")),
        section_coverage=_as_float(audit.get("section_coverage")),
        overlap_ratio=_as_float(audit.get("overlap_ratio")),
        clutter_ratio=_as_float(audit.get("clutter_ratio")),
        coverage_score=_as_float(component_scores.get("coverage") if isinstance(component_scores, Mapping) else 0.0),
        structure_score=_as_float(component_scores.get("structure") if isinstance(component_scores, Mapping) else 0.0),
        family_diversity_score=_as_float(component_scores.get("family_diversity") if isinstance(component_scores, Mapping) else 0.0),
        warnings=warnings,
    )
    quality_score = _comparison_score(summary)
    warnings = list(warnings)
    if summary.rejected_effects > 18000:
        warnings.append("Rejected effects exceed showcase legacy 256 target.")
    if summary.clutter_ratio > 0.12:
        warnings.append("Clutter ratio is high for legacy 256 calibration.")
    if summary.section_coverage < 0.75:
        warnings.append("Section coverage is low for legacy 256 calibration.")
    return Legacy256ReportSummary(**(summary.to_dict() | {"comparison_score": quality_score, "warnings": warnings}))


def compare_reports(paths: Iterable[str | Path]) -> Legacy256ComparisonReport:
    summaries = [summarize_report(path) for path in paths]
    sorted_summaries = sorted(
        summaries,
        key=lambda item: (
            item.comparison_score,
            item.quality_score,
            item.audit_score,
            -item.rejected_effects,
        ),
        reverse=True,
    )
    warnings: list[str] = []
    if not sorted_summaries:
        warnings.append("No reports were provided.")
    winner = sorted_summaries[0].label if sorted_summaries else ""
    return Legacy256ComparisonReport(
        winner=winner,
        summaries=[item.to_dict() for item in sorted_summaries],
        warnings=warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare Legacy 256 Helix report.json outputs.")
    parser.add_argument("reports", nargs="+", help="Report JSON paths to compare")
    parser.add_argument("--output", help="Optional JSON output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = compare_reports(args.reports)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.to_json() + "\n", encoding="utf-8")
        print({"output": str(output), "winner": report.winner})
    else:
        print(report.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
