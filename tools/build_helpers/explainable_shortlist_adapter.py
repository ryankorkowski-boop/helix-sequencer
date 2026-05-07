"""Report-only explainable shortlist adapter for Phase 2B.

This module adapts existing variant candidate report entries into the explainable
variant scoring format from Slice 8. It is intentionally adjacent to, not a
replacement for, tools.build_helpers.variants.choose_best_candidate().

Behavior boundary:
- Does not promote variants.
- Does not copy files.
- Does not change existing shortlist decisions.
- Does not mutate entries unless callers explicitly merge the returned payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from tools.build_helpers.explainable_variant_scoring import ShortlistReport, rank_variants
from tools.build_helpers.variants import choose_best_candidate_with_preset


@dataclass(frozen=True)
class ExplainableShortlistAdapterReport:
    """Report-only comparison between legacy and explainable shortlist views."""

    preset: str
    legacy_winner: str | None
    explainable_winner: str | None
    agreement: bool
    explainable_shortlist: ShortlistReport
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "preset": self.preset,
            "legacy_winner": self.legacy_winner,
            "explainable_winner": self.explainable_winner,
            "agreement": self.agreement,
            "explainable_shortlist": self.explainable_shortlist.as_dict(),
            "warnings": list(self.warnings),
        }


def adapt_variant_entry(entry: Mapping[str, Any]) -> dict[str, object]:
    """Convert an existing variant report entry into Slice 8 scoring shape."""

    quality_payload = _mapping(entry.get("quality"))
    audit_payload = _audit_payload(entry)
    validation_payload = _mapping(entry.get("validation"))

    adapted: dict[str, object] = {
        "variant_id": str(entry.get("label") or entry.get("variant_id") or entry.get("output") or "unnamed_variant"),
        "quality_score": _float(quality_payload.get("score")),
        "audit_score": _float(audit_payload.get("score")),
        "rejected_effects": int(_float(validation_payload.get("rejected_effects_count"))),
    }

    # Preserve advisory report scores when callers have already attached them to
    # generated entries. Defaults are handled by score_variant().
    advisory = _mapping(entry.get("advisory") or entry.get("quality_advisory") or entry.get("output_quality"))
    key_map = {
        "restraint": ("restraint", "density_restraint"),
        "section_identity": ("section_identity",),
        "palette_discipline": ("palette_discipline",),
        "motif_memory": ("motif_memory",),
        "prop_roles": ("prop_roles",),
        "manual_lock_respect": ("manual_lock_respect", "manual_locks"),
    }
    for target_key, aliases in key_map.items():
        score = _first_score(advisory, aliases)
        if score is not None:
            adapted[target_key] = {"score": score}

    return adapted


def build_explainable_shortlist_report(
    entries: Iterable[Mapping[str, Any]],
    preset: str = "showcase",
) -> ExplainableShortlistAdapterReport:
    """Build a report-only explainable shortlist beside the existing chooser."""

    entry_list = [dict(entry) for entry in entries]
    warnings: list[str] = []
    legacy_best = choose_best_candidate_with_preset(entry_list, preset)
    legacy_winner = _entry_id(legacy_best) if legacy_best is not None else None

    adapted = [adapt_variant_entry(entry) for entry in entry_list]
    explainable = rank_variants(adapted, preset=preset)
    explainable_winner = explainable.winner

    if not entry_list:
        warnings.append("no entries provided")
    elif legacy_winner != explainable_winner:
        warnings.append(
            "legacy and explainable shortlist winners differ; report-only adapter did not change selection"
        )

    return ExplainableShortlistAdapterReport(
        preset=preset,
        legacy_winner=legacy_winner,
        explainable_winner=explainable_winner,
        agreement=legacy_winner == explainable_winner,
        explainable_shortlist=explainable,
        warnings=tuple(warnings),
    )


def attach_explainable_shortlist_report(
    payload: Mapping[str, Any],
    entries: Iterable[Mapping[str, Any]],
    preset: str = "showcase",
) -> dict[str, Any]:
    """Return a copy of a report payload with explainable shortlist metadata.

    This is still report-only. It does not call promote_shortlisted_candidate() or
    alter the canonical winner.
    """

    updated = dict(payload)
    updated["explainable_shortlist"] = build_explainable_shortlist_report(entries, preset).as_dict()
    return updated


def _entry_id(entry: Mapping[str, Any] | None) -> str | None:
    if entry is None:
        return None
    return str(entry.get("label") or entry.get("variant_id") or entry.get("output") or entry.get("output_path") or "unnamed_variant")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _audit_payload(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = _mapping(entry.get("audit"))
    final = payload.get("final")
    return _mapping(final) if isinstance(final, Mapping) else payload


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_score(advisory: Mapping[str, Any], aliases: tuple[str, ...]) -> float | None:
    for alias in aliases:
        value = advisory.get(alias)
        if isinstance(value, Mapping):
            if "score" in value:
                return _float(value.get("score"))
            summary = value.get("summary")
            if isinstance(summary, Mapping) and "score" in summary:
                return _float(summary.get("score"))
        elif value is not None:
            return _float(value)
    return None
