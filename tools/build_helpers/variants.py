from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeVariantCandidate:
    label: str
    description: str
    style: Any
    tuning: Any


@dataclass(frozen=True)
class QualityGatePreset:
    name: str
    min_quality_score: float
    min_audit_score: float
    max_rejected_effects: int


DEFAULT_MIN_AUDIT_SCORE = 80.0
DEFAULT_MAX_REJECTED_EFFECTS = 28000
DEFAULT_MIN_QUALITY_SCORE = 90.0
DEFAULT_SHOWCASE_MIN_AUDIT_SCORE = 86.0
DEFAULT_SHOWCASE_MAX_REJECTED_EFFECTS = 18000
DEFAULT_SHOWCASE_MIN_QUALITY_SCORE = 93.0
DEFAULT_PRO_MIN_AUDIT_SCORE = 90.0
DEFAULT_PRO_MAX_REJECTED_EFFECTS = 12000
DEFAULT_PRO_MIN_QUALITY_SCORE = 96.0

# Backward-compatible constant aliases. Existing engine flags still use the
# historical names, but user-facing calibration language should prefer "pro".
DEFAULT_VENDOR_MIN_AUDIT_SCORE = DEFAULT_PRO_MIN_AUDIT_SCORE
DEFAULT_VENDOR_MAX_REJECTED_EFFECTS = DEFAULT_PRO_MAX_REJECTED_EFFECTS
DEFAULT_VENDOR_MIN_QUALITY_SCORE = DEFAULT_PRO_MIN_QUALITY_SCORE

QUALITY_GATE_PRESETS: dict[str, QualityGatePreset] = {
    "general": QualityGatePreset(
        name="general",
        min_quality_score=DEFAULT_MIN_QUALITY_SCORE,
        min_audit_score=DEFAULT_MIN_AUDIT_SCORE,
        max_rejected_effects=DEFAULT_MAX_REJECTED_EFFECTS,
    ),
    "showcase": QualityGatePreset(
        name="showcase",
        min_quality_score=DEFAULT_SHOWCASE_MIN_QUALITY_SCORE,
        min_audit_score=DEFAULT_SHOWCASE_MIN_AUDIT_SCORE,
        max_rejected_effects=DEFAULT_SHOWCASE_MAX_REJECTED_EFFECTS,
    ),
    "pro": QualityGatePreset(
        name="pro",
        min_quality_score=DEFAULT_PRO_MIN_QUALITY_SCORE,
        min_audit_score=DEFAULT_PRO_MIN_AUDIT_SCORE,
        max_rejected_effects=DEFAULT_PRO_MAX_REJECTED_EFFECTS,
    ),
    # Backward-compatible alias for older prompts/scripts. New docs/tests should use "pro".
    "vendor": QualityGatePreset(
        name="pro",
        min_quality_score=DEFAULT_PRO_MIN_QUALITY_SCORE,
        min_audit_score=DEFAULT_PRO_MIN_AUDIT_SCORE,
        max_rejected_effects=DEFAULT_PRO_MAX_REJECTED_EFFECTS,
    ),
}


def quality_gate_preset(name: str | None) -> QualityGatePreset:
    key = (name or "general").strip().lower().replace("-", "_")
    return QUALITY_GATE_PRESETS.get(key, QUALITY_GATE_PRESETS["general"])


def build_runtime_candidates(base_style: Any, base_tuning: Any, count: int) -> list[RuntimeVariantCandidate]:
    requested = max(1, int(count))
    candidates: list[RuntimeVariantCandidate] = [
        RuntimeVariantCandidate(
            label="signature",
            description="Base v27.3/master render with audit and polish enabled.",
            style=base_style,
            tuning=base_tuning,
        )
    ]
    if requested == 1:
        return candidates

    presets = [
        (
            "hook_focus",
            "Boost hooks, melodic carry, and chorus memorability.",
            {
                "version": f"{base_style.version}.alt1",
                "title": f"{base_style.title} / Hook Focus",
                "density_scale": base_style.density_scale * 1.06,
                "melody_scale": base_style.melody_scale * 1.18,
                "bass_scale": base_style.bass_scale * 0.96,
                "randomness_scale": base_style.randomness_scale * 0.88,
                "section_emphasis": True,
                "call_response": True,
            },
            {
                "keyboard_mix": min(2.0, float(getattr(base_tuning, "keyboard_mix", 1.0)) * 0.96),
                "palette_mode": "workspace_match" if getattr(base_tuning, "palette_mode", "template") == "template" else base_tuning.palette_mode,
            },
        ),
        (
            "wide_stage",
            "Push spatial flow, neighbor reactions, and larger yard movement.",
            {
                "version": f"{base_style.version}.alt2",
                "title": f"{base_style.title} / Wide Stage",
                "density_scale": base_style.density_scale * 1.02,
                "speed_scale": base_style.speed_scale * 1.04,
                "bass_scale": base_style.bass_scale * 1.08,
                "randomness_scale": base_style.randomness_scale * 0.94,
                "pool_mode": "sectional",
                "placement_mode": "showcase_signature",
            },
            {
                "spatial_awareness": max(0.36, float(getattr(base_tuning, "spatial_awareness", 0.0))),
                "chase_style": "wave" if getattr(base_tuning, "chase_style", "none") == "none" else base_tuning.chase_style,
                "layering_mode": "smart_layer",
            },
        ),
        (
            "stem_story",
            "Lean harder into stem-aware layering and controlled breathing.",
            {
                "version": f"{base_style.version}.alt3",
                "title": f"{base_style.title} / Stem Story",
                "density_scale": base_style.density_scale * 0.98,
                "speed_scale": base_style.speed_scale * 0.99,
                "bass_scale": base_style.bass_scale * 1.10,
                "melody_scale": base_style.melody_scale * 1.10,
                "darkness_scale": base_style.darkness_scale * 1.04,
            },
            {
                "keyboard_mix": min(2.0, float(getattr(base_tuning, "keyboard_mix", 1.0)) * 0.92),
                "flash_guard": min(1.0, float(getattr(base_tuning, "flash_guard", 0.80)) * 1.06),
                "layer_priority_vocals": max(5, int(getattr(base_tuning, "layer_priority_vocals", 4))),
            },
        ),
        (
            "cinematic_arc",
            "Stretch section contrast, skyline reveals, and hero-chorus storytelling.",
            {
                "version": f"{base_style.version}.alt4",
                "title": f"{base_style.title} / Cinematic Arc",
                "density_scale": base_style.density_scale * 0.97,
                "speed_scale": base_style.speed_scale * 0.98,
                "bass_scale": base_style.bass_scale * 1.04,
                "melody_scale": base_style.melody_scale * 1.16,
                "darkness_scale": base_style.darkness_scale * 1.08,
                "pool_mode": "sectional",
                "placement_mode": "showcase_signature",
                "section_emphasis": True,
                "call_response": True,
            },
            {
                "flash_guard": min(1.0, float(getattr(base_tuning, "flash_guard", 0.80)) * 1.08),
                "spatial_awareness": max(0.30, float(getattr(base_tuning, "spatial_awareness", 0.0))),
                "palette_mode": "workspace_match" if getattr(base_tuning, "palette_mode", "template") == "template" else base_tuning.palette_mode,
                "layering_mode": "smart_layer",
            },
        ),
    ]
    for label, description, style_overrides, tuning_overrides in presets[: max(0, requested - 1)]:
        candidates.append(
            RuntimeVariantCandidate(
                label=label,
                description=description,
                style=replace(base_style, **style_overrides),
                tuning=replace(base_tuning, **tuning_overrides),
            )
        )
    return candidates[:requested]


def _score_maximum(value: float, target: float, ceiling: float) -> float:
    if target <= 0:
        return 100.0
    if value <= target:
        return min(100.0, max(0.0, (value / target) * 100.0))
    if ceiling <= target:
        return 100.0
    overshoot = min(1.0, (value - target) / max(ceiling - target, 1e-6))
    return max(0.0, 100.0 - (overshoot * 100.0))


def _audit_payload(entry: dict[str, Any]) -> dict[str, Any]:
    payload = (entry.get("audit") or {}) or {}
    if isinstance(payload.get("final"), dict):
        return (payload.get("final") or {}) or {}
    return payload


def _audit_score(entry: dict[str, Any]) -> float:
    payload = _audit_payload(entry)
    return float(payload.get("score", 0.0) or 0.0)


def evaluate_quality_gates(
    entry: dict[str, Any],
    *,
    min_audit_score: float = DEFAULT_MIN_AUDIT_SCORE,
    max_rejected_effects: int = DEFAULT_MAX_REJECTED_EFFECTS,
    min_quality_score: float | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    quality_payload = (entry.get("quality") or {}) or {}
    quality_score = float(quality_payload.get("score", 0.0) or 0.0)
    if min_quality_score is not None and quality_score < float(min_quality_score):
        reasons.append(f"quality_below_threshold<{float(min_quality_score):.1f}")

    audit_score = _audit_score(entry)
    if audit_score <= 0.0:
        reasons.append("missing_final_audit")
    elif audit_score < float(min_audit_score):
        reasons.append(f"audit_below_threshold<{float(min_audit_score):.1f}")

    validation_payload = (entry.get("validation") or {}) or {}
    rejected_effects = int(validation_payload.get("rejected_effects_count", 0) or 0)
    if rejected_effects > int(max_rejected_effects):
        reasons.append(f"rejected_effects_above_threshold>{int(max_rejected_effects)}")

    return {
        "passed": not reasons,
        "reasons": reasons,
        "quality_score": round(quality_score, 2),
        "audit_score": round(audit_score, 2),
        "rejected_effects": rejected_effects,
    }


def evaluate_quality_gate_preset(entry: dict[str, Any], preset_name: str | None) -> dict[str, Any]:
    preset = quality_gate_preset(preset_name)
    result = evaluate_quality_gates(
        entry,
        min_quality_score=preset.min_quality_score,
        min_audit_score=preset.min_audit_score,
        max_rejected_effects=preset.max_rejected_effects,
    )
    return result | {"preset": preset.name}


def _score_entry(entry: dict[str, Any]) -> float:
    quality_payload = (entry.get("quality") or {}) or {}
    audit_payload = _audit_payload(entry)
    self_scoring = (entry.get("self_improving_scoring") or {}) or {}
    quality = float(quality_payload.get("score", 0.0) or 0.0)
    audit = float(audit_payload.get("score", 0.0) or 0.0)
    self_score = float(self_scoring.get("total_score", 0.0) or 0.0) * 100.0
    polish = entry.get("polish") or {}
    polish_score = float(polish.get("score", 0.0) or 0.0)
    component_scores = (quality_payload.get("component_scores") or {}) or {}
    structure = float(component_scores.get("structure", 0.0) or 0.0)
    coverage = float(component_scores.get("coverage", 0.0) or 0.0)
    detail = float(component_scores.get("detail", 0.0) or 0.0)
    family_diversity = float(component_scores.get("family_diversity", 0.0) or 0.0)
    dominance = float(component_scores.get("dominance", 0.0) or 0.0)
    musical_coherence = float(audit_payload.get("musical_coherence", 0.0) or 0.0)
    section_coverage = float(audit_payload.get("section_coverage", 0.0) or 0.0)
    overlap_ratio = float(audit_payload.get("overlap_ratio", 0.0) or 0.0)
    clutter_ratio = float(audit_payload.get("clutter_ratio", 0.0) or 0.0)
    rejected_effects = int(((entry.get("validation") or {}) or {}).get("rejected_effects_count", 0) or 0)
    polish_bonus = (
        min(4.0, float(polish.get("hook_enhancements", 0)) * 0.4)
        + min(3.0, float(polish.get("breathing_fades", 0)) * 0.25)
        + min(3.0, float(polish.get("palette_swaps", 0)) * 0.20)
    )
    craft_bonus = (
        min(3.0, max(0.0, (structure - 78.0) * 0.16))
        + min(2.5, max(0.0, (coverage - 74.0) * 0.12))
        + min(2.0, max(0.0, (detail - 72.0) * 0.08))
        + min(2.0, max(0.0, (family_diversity - 72.0) * 0.08))
        + min(1.5, max(0.0, (dominance - 76.0) * 0.06))
        + min(3.0, max(0.0, (musical_coherence - 84.0) * 0.18))
        + min(2.0, max(0.0, ((section_coverage * 100.0) - 72.0) * 0.12))
    )
    cleanup_penalty = (
        (100.0 - _score_maximum(overlap_ratio, target=0.03, ceiling=0.22)) * 0.05
        + (100.0 - _score_maximum(clutter_ratio, target=0.08, ceiling=0.42)) * 0.03
    )
    rejected_penalty = min(10.0, max(0.0, rejected_effects - 6000) / 2400.0)
    shortlist_score = (
        (quality * 0.40)
        + (audit * 0.20)
        + (self_score * 0.18)
        + (polish_score * 0.08)
        + craft_bonus
        + polish_bonus
        - cleanup_penalty
        - rejected_penalty
    )
    return round(shortlist_score, 2)


def choose_best_candidate(
    entries: list[dict[str, Any]],
    *,
    min_audit_score: float = DEFAULT_MIN_AUDIT_SCORE,
    max_rejected_effects: int = DEFAULT_MAX_REJECTED_EFFECTS,
    min_quality_score: float | None = None,
) -> dict[str, Any] | None:
    if not entries:
        return None
    scored = []
    for entry in entries:
        copy = dict(entry)
        copy["shortlist_score"] = _score_entry(copy)
        quality_gate = evaluate_quality_gates(
            copy,
            min_audit_score=min_audit_score,
            max_rejected_effects=max_rejected_effects,
            min_quality_score=min_quality_score,
        )
        copy["quality_gate_passed"] = bool(quality_gate["passed"])
        copy["quality_gate_reasons"] = list(quality_gate["reasons"])
        copy["quality_gate_quality_score"] = float(quality_gate["quality_score"])
        copy["quality_gate_audit_score"] = float(quality_gate["audit_score"])
        copy["quality_gate_rejected_effects"] = int(quality_gate["rejected_effects"])
        scored.append(copy)
    scored.sort(
        key=lambda item: (
            int(bool(item.get("quality_gate_passed", False))),
            float(item.get("shortlist_score", 0.0)),
            _audit_score(item),
            float(((item.get("quality") or {}) or {}).get("score", 0.0) or 0.0),
        ),
        reverse=True,
    )
    return scored[0]


def choose_best_candidate_with_preset(entries: list[dict[str, Any]], preset_name: str | None) -> dict[str, Any] | None:
    preset = quality_gate_preset(preset_name)
    best = choose_best_candidate(
        entries,
        min_audit_score=preset.min_audit_score,
        max_rejected_effects=preset.max_rejected_effects,
        min_quality_score=preset.min_quality_score,
    )
    if best is not None:
        best = dict(best)
        best["quality_gate_preset"] = preset.name
    return best


def promote_shortlisted_candidate(best_entry: dict[str, Any], canonical_output: Path) -> dict[str, Any]:
    if best_entry.get("quality_gate_passed") is False:
        reasons = ", ".join(str(item) for item in (best_entry.get("quality_gate_reasons") or [])) or "failed_quality_gates"
        raise ValueError(f"Refusing shortlist promotion: {reasons}")

    source_output = Path(best_entry["output_path"])
    source_report = Path(best_entry["report_path"])
    source_notes = Path(best_entry["notes_path"])
    shortlist_score = float(best_entry.get("shortlist_score", 0.0) or 0.0)

    if source_output.resolve() != canonical_output.resolve():
        shutil.copy2(source_output, canonical_output)

    payload = json.loads(source_report.read_text(encoding="utf-8"))
    shortlist_meta = payload.get("shortlist", {}) or {}
    shortlist_meta.update(
        {
            "selected": True,
            "winner": source_output.name,
            "promoted_output": canonical_output.name,
            "score": shortlist_score,
            "label": best_entry.get("label", ""),
            "description": best_entry.get("description", ""),
        }
    )
    payload["shortlist"] = shortlist_meta
    payload["output"] = canonical_output.name
    canonical_report = canonical_output.with_name(f"{canonical_output.stem}.report.json")
    canonical_report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    notes_text = source_notes.read_text(encoding="utf-8")
    notes_suffix = (
        "\n\nAuto Shortlist\n"
        f"- Selected candidate: {source_output.name}\n"
        f"- Promoted output: {canonical_output.name}\n"
        f"- Shortlist score: {shortlist_score:.2f}\n"
    )
    canonical_notes = canonical_output.with_name(f"{canonical_output.stem}.sequence_notes.txt")
    canonical_notes.write_text(notes_text.rstrip() + notes_suffix, encoding="utf-8")

    return {
        "output_path": str(canonical_output),
        "report_path": str(canonical_report),
        "notes_path": str(canonical_notes),
        "shortlist_score": shortlist_score,
    }
