"""Report-only output quality aggregation for Helix Phase 2A.

This module provides a safe callable hook for post-generation reporting. It
combines the advisory helpers from Slices 2-10 into one report payload without
rendering effects, writing XSQ content, mutating layouts, or changing candidate
selection. Callers can invoke this after generation and persist the returned JSON
beside normal output artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from tools.build_helpers.explainable_variant_scoring import rank_variants
from tools.build_helpers.gui_quality_options import GuiQualityOptions, normalize_gui_quality_options
from tools.build_helpers.manual_locks import ManualLockError, parse_manual_lock_file
from tools.build_helpers.motif_memory import score_motif_memory
from tools.build_helpers.palette_discipline import score_palette_discipline
from tools.build_helpers.prop_roles import summarize_roles
from tools.build_helpers.regression_snapshots import compact_quality_snapshot
from tools.build_helpers.restraint import score_restraint
from tools.build_helpers.section_identity import score_section_identity


@dataclass(frozen=True)
class OutputQualityReport:
    """Combined report-only payload for Helix output quality diagnostics."""

    version: str
    report_only: bool
    quality_preset: str
    style_preset: str
    enabled_modules: tuple[str, ...]
    reports: dict[str, object] = field(default_factory=dict)
    summary: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "report_only": self.report_only,
            "quality_preset": self.quality_preset,
            "style_preset": self.style_preset,
            "enabled_modules": list(self.enabled_modules),
            "reports": self.reports,
            "summary": self.summary,
            "warnings": list(self.warnings),
        }


def build_output_quality_report(
    *,
    options: Mapping[str, object] | GuiQualityOptions | None = None,
    model_names: Iterable[str] | None = None,
    cues: Iterable[Mapping[str, object]] | None = None,
    sections: Iterable[Mapping[str, object]] | None = None,
    motifs: Iterable[Mapping[str, object]] | None = None,
    manual_locks: Mapping[str, object] | None = None,
    variants: Iterable[Mapping[str, object]] | None = None,
    baseline_candidate: Mapping[str, object] | None = None,
) -> OutputQualityReport:
    """Build a combined advisory report from available generated artifacts.

    Missing inputs are skipped with warnings. This makes the hook safe to call from
    early pipeline stages before every advisory source exists.
    """

    normalized_options = options if isinstance(options, GuiQualityOptions) else normalize_gui_quality_options(options)
    enabled = set(normalized_options.enabled_report_modules())
    reports: dict[str, object] = {}
    warnings: list[str] = []

    if "prop_roles" in enabled:
        if model_names is None:
            warnings.append("prop_roles skipped: no model_names provided")
        else:
            reports["prop_roles"] = summarize_roles(model_names)

    if "density_restraint" in enabled:
        if cues is None:
            warnings.append("density_restraint skipped: no cues provided")
        else:
            reports["density_restraint"] = score_restraint(cues).as_dict()

    if "section_identity" in enabled:
        if sections is None:
            warnings.append("section_identity skipped: no sections provided")
        else:
            reports["section_identity"] = score_section_identity(sections).as_dict()

    if "palette_discipline" in enabled:
        if sections is None:
            warnings.append("palette_discipline skipped: no sections provided")
        else:
            reports["palette_discipline"] = score_palette_discipline(
                sections,
                style=normalized_options.style_preset,
            ).as_dict()

    if "motif_memory" in enabled:
        if motifs is None:
            warnings.append("motif_memory skipped: no motifs provided")
        else:
            reports["motif_memory"] = score_motif_memory(motifs).as_dict()

    if "manual_locks" in enabled:
        if manual_locks is None:
            warnings.append("manual_locks skipped: no manual_locks sidecar provided")
        else:
            try:
                lock_file = parse_manual_lock_file(manual_locks)
                reports["manual_locks"] = {
                    "summary": lock_file.summary(),
                    "locks": [lock.as_dict() for lock in lock_file.locks],
                }
            except ManualLockError as exc:
                warnings.append(f"manual_locks skipped: {exc}")

    if variants is not None:
        shortlist = rank_variants(variants, preset=normalized_options.quality_preset)
        reports["explainable_variants"] = shortlist.as_dict()

    if baseline_candidate is not None:
        reports["compact_quality_snapshot"] = compact_quality_snapshot(baseline_candidate)

    summary = _summarize_reports(reports)
    return OutputQualityReport(
        version="0.1",
        report_only=True,
        quality_preset=normalized_options.quality_preset,
        style_preset=normalized_options.style_preset,
        enabled_modules=normalized_options.enabled_report_modules(),
        reports=reports,
        summary=summary,
        warnings=tuple(warnings),
    )


def _summarize_reports(reports: Mapping[str, object]) -> dict[str, object]:
    summary: dict[str, object] = {
        "report_count": len(reports),
        "available_reports": sorted(reports),
    }

    score_keys = {
        "density_restraint": "score",
        "section_identity": "score",
        "palette_discipline": "score",
        "motif_memory": "score",
    }
    component_scores: dict[str, float] = {}
    for report_name, score_key in score_keys.items():
        report = reports.get(report_name)
        if isinstance(report, Mapping) and score_key in report:
            component_scores[report_name] = float(report[score_key])

    variants = reports.get("explainable_variants")
    if isinstance(variants, Mapping):
        winner = variants.get("winner")
        if winner is not None:
            summary["winner"] = winner

    if component_scores:
        summary["component_scores"] = component_scores
        summary["average_component_score"] = round(
            sum(component_scores.values()) / len(component_scores),
            4,
        )

    return summary
