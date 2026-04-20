from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any


def _grade(score: float) -> str:
    if score >= 97:
        return "A+"
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 73:
        return "C"
    if score >= 70:
        return "C-"
    if score >= 67:
        return "D+"
    if score >= 63:
        return "D"
    if score >= 60:
        return "D-"
    return "F"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _entry_len(entry: Any) -> int:
    return max(0, int(getattr(entry, "end", 0)) - int(getattr(entry, "start", 0)))


def _set_entry_window(entry: Any, start_ms: int, end_ms: int) -> None:
    start_ms = int(start_ms)
    end_ms = int(max(start_ms + 1, end_ms))
    entry.start = start_ms
    entry.end = end_ms
    try:
        entry.xml_effect.attrib["startTime"] = str(start_ms)
        entry.xml_effect.attrib["endTime"] = str(end_ms)
    except Exception:
        pass


def _timeline_entries(timelines: dict[str, Any]) -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    for model_name, timeline in timelines.items():
        for layer_name, entries in getattr(timeline, "layers", {}).items():
            for entry in list(entries):
                rows.append((model_name, layer_name, entry))
    return rows


def _pick_keep_entry(first: tuple[str, Any], second: tuple[str, Any]) -> tuple[tuple[str, Any], tuple[str, Any]]:
    first_layer, first_entry = first
    second_layer, second_entry = second
    first_priority = int(getattr(first_entry, "priority", 0))
    second_priority = int(getattr(second_entry, "priority", 0))
    if second_priority > first_priority:
        return second, first
    if second_priority < first_priority:
        return first, second
    layer_weight = {"accent": 3, "motion": 2, "base": 1}
    if layer_weight.get(second_layer, 0) > layer_weight.get(first_layer, 0):
        return second, first
    if layer_weight.get(second_layer, 0) < layer_weight.get(first_layer, 0):
        return first, second
    if _entry_len(second_entry) >= _entry_len(first_entry):
        return second, first
    return first, second


def _resolve_conflict_window(trim_entry: Any, keep_entry: Any, min_effect_ms: int) -> tuple[int, int] | None:
    trim_start = int(getattr(trim_entry, "start", 0))
    trim_end = int(getattr(trim_entry, "end", 0))
    keep_start = int(getattr(keep_entry, "start", 0))
    keep_end = int(getattr(keep_entry, "end", 0))
    left_option = (trim_start, min(trim_end, keep_start))
    right_option = (max(trim_start, keep_end), trim_end)
    options = [
        option
        for option in (left_option, right_option)
        if option[1] - option[0] >= max(1, int(min_effect_ms))
    ]
    if not options:
        return None
    options.sort(key=lambda item: (item[1] - item[0], -item[0]), reverse=True)
    return options[0]


def _overlap_ms(first: Any, second: Any) -> int:
    return max(
        0,
        min(int(getattr(first, "end", 0)), int(getattr(second, "end", 0)))
        - max(int(getattr(first, "start", 0)), int(getattr(second, "start", 0))),
    )


def _max_concurrency(entries: list[Any]) -> int:
    events: list[tuple[int, int]] = []
    for entry in entries:
        start_ms = int(getattr(entry, "start", 0))
        end_ms = int(getattr(entry, "end", 0))
        if end_ms <= start_ms:
            continue
        events.append((start_ms, 1))
        events.append((end_ms, -1))
    if not events:
        return 0
    events.sort(key=lambda item: (item[0], -item[1]))
    active = 0
    peak = 0
    for _time_ms, delta in events:
        active += delta
        peak = max(peak, active)
    return peak


def _section_density(entries: list[tuple[str, str, Any]], start_ms: int, end_ms: int) -> tuple[int, float]:
    duration_ms = max(1, end_ms - start_ms)
    hits = 0
    active_ms = 0
    for _model_name, _layer_name, entry in entries:
        overlap = max(
            0,
            min(end_ms, int(getattr(entry, "end", 0))) - max(start_ms, int(getattr(entry, "start", 0))),
        )
        if overlap <= 0:
            continue
        hits += 1
        active_ms += overlap
    density = (hits * 1000.0) / float(duration_ms)
    coverage = active_ms / float(duration_ms)
    return hits, _clamp(max(density, coverage), 0.0, 25.0)


@dataclass
class AuditSectionScore:
    label: str
    start_ms: int
    end_ms: int
    energy: float
    effect_count: int
    density: float
    target_density: float
    coverage_ratio: float
    score: float

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "label": self.label,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "energy": round(self.energy, 3),
            "effect_count": self.effect_count,
            "density": round(self.density, 3),
            "target_density": round(self.target_density, 3),
            "coverage_ratio": round(self.coverage_ratio, 3),
            "score": round(self.score, 1),
        }


@dataclass
class AuditResult:
    score: float
    grade: str
    overlap_ratio: float
    clutter_ratio: float
    section_coverage: float
    intensity_balance: float
    musical_coherence: float
    auto_fixed: bool = False
    fixes_applied: int = 0
    fixes: list[str] = field(default_factory=list)
    section_scores: list[AuditSectionScore] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "grade": self.grade,
            "overlap_ratio": round(self.overlap_ratio, 3),
            "clutter_ratio": round(self.clutter_ratio, 3),
            "section_coverage": round(self.section_coverage, 3),
            "intensity_balance": round(self.intensity_balance, 1),
            "musical_coherence": round(self.musical_coherence, 1),
            "auto_fixed": self.auto_fixed,
            "fixes_applied": int(self.fixes_applied),
            "fixes": self.fixes[:64],
            "section_scores": [section.as_dict() for section in self.section_scores],
        }


def run_super_audit(
    *,
    timelines: dict[str, Any],
    parts: list[Any],
    placements: dict[str, int] | None = None,
    min_effect_ms: int = 50,
    auto_fix: bool = False,
) -> AuditResult:
    fixes: list[str] = []
    fixes_applied = 0
    min_effect_ms = max(1, int(min_effect_ms))

    if auto_fix:
        for model_name, timeline in timelines.items():
            changed = True
            passes = 0
            while changed and passes < 4:
                changed = False
                passes += 1
                flattened: list[tuple[str, Any]] = []
                for layer_name, entries in getattr(timeline, "layers", {}).items():
                    for entry in list(entries):
                        if _entry_len(entry) >= min_effect_ms:
                            flattened.append((layer_name, entry))
                    entries.sort(key=lambda item: (item.start, item.end))
                flattened.sort(key=lambda item: (int(getattr(item[1], "start", 0)), -int(getattr(item[1], "priority", 0))))
                for idx in range(1, len(flattened)):
                    prev = flattened[idx - 1]
                    curr = flattened[idx]
                    if _overlap_ms(prev[1], curr[1]) <= 0:
                        continue
                    keep_layer_entry, trim_layer_entry = _pick_keep_entry(prev, curr)
                    keep_layer, keep_entry = keep_layer_entry
                    trim_layer, trim_entry = trim_layer_entry
                    replacement = _resolve_conflict_window(trim_entry, keep_entry, min_effect_ms)
                    if replacement is None:
                        timeline.remove_entry(trim_layer, trim_entry)
                        fixes.append(
                            f"{model_name}:{trim_layer} removed lower-priority overlap against {keep_layer}"
                        )
                    else:
                        _set_entry_window(trim_entry, replacement[0], replacement[1])
                        fixes.append(
                            f"{model_name}:{trim_layer} trimmed overlap to {replacement[0]}-{replacement[1]}ms"
                        )
                    fixes_applied += 1
                    changed = True
                    break

    all_entries = _timeline_entries(timelines)
    total_effect_ms = sum(_entry_len(entry) for _model_name, _layer_name, entry in all_entries)
    overlap_ms = 0
    clutter_models = 0
    active_models = 0
    for _model_name, timeline in timelines.items():
        model_entries: list[Any] = []
        for entries in getattr(timeline, "layers", {}).values():
            model_entries.extend(list(entries))
        if not model_entries:
            continue
        active_models += 1
        if _max_concurrency(model_entries) >= 3:
            clutter_models += 1
        ordered = sorted(model_entries, key=lambda entry: (int(getattr(entry, "start", 0)), int(getattr(entry, "end", 0))))
        for idx, first in enumerate(ordered):
            for second in ordered[idx + 1 :]:
                if int(getattr(second, "start", 0)) >= int(getattr(first, "end", 0)):
                    break
                overlap_ms += _overlap_ms(first, second)

    overlap_ratio = overlap_ms / float(max(1, total_effect_ms))
    clutter_ratio = clutter_models / float(max(1, active_models))

    section_scores: list[AuditSectionScore] = []
    populated_sections = 0
    density_pairs: list[tuple[float, float]] = []
    section_entries = all_entries
    for part in parts:
        start_ms = int(getattr(part, "start_ms", 0))
        end_ms = int(getattr(part, "end_ms", 0))
        label = str(getattr(part, "label", "") or "SECTION")
        energy = float(getattr(part, "energy", 0.0) or 0.0)
        hits, density = _section_density(section_entries, start_ms, end_ms)
        coverage_ratio = 1.0 if hits > 0 else 0.0
        populated_sections += 1 if hits > 0 else 0
        target_density = 0.25 + (energy * 1.45)
        delta = abs(density - target_density)
        score = _clamp(100.0 - (delta * 34.0), 0.0, 100.0)
        section_scores.append(
            AuditSectionScore(
                label=label,
                start_ms=start_ms,
                end_ms=end_ms,
                energy=energy,
                effect_count=hits,
                density=density,
                target_density=target_density,
                coverage_ratio=coverage_ratio,
                score=score,
            )
        )
        density_pairs.append((_clamp(energy, 0.0, 1.0), density))

    section_coverage = populated_sections / float(max(1, len(parts)))
    intensity_balance = mean(section.score for section in section_scores) if section_scores else 75.0

    if density_pairs:
        max_density = max(density for _energy, density in density_pairs) or 1.0
        balance_error = mean(abs(energy - (density / max_density)) for energy, density in density_pairs)
        intensity_balance = _clamp(((intensity_balance * 0.55) + ((1.0 - balance_error) * 100.0 * 0.45)), 0.0, 100.0)

    label_counts = {str(key).lower(): int(value) for key, value in (placements or {}).items()}
    build_tokens = sum(value for key, value in label_counts.items() if "build" in key or "lift" in key)
    drop_tokens = sum(value for key, value in label_counts.items() if "drop" in key or "impact" in key)
    hook_tokens = sum(value for key, value in label_counts.items() if "hook" in key or "chorus" in key or "vocal" in key)
    transition_tokens = sum(value for key, value in label_counts.items() if "transition" in key or "call" in key or "response" in key)
    weighted_tokens = (build_tokens * 1.1) + (drop_tokens * 1.3) + hook_tokens + (transition_tokens * 0.9)
    token_score = _clamp(55.0 + min(40.0, weighted_tokens / 24.0), 0.0, 100.0)

    shape_bonus = 0.0
    for idx, section in enumerate(section_scores[:-1]):
        next_section = section_scores[idx + 1]
        if "BUILD" in section.label.upper() and next_section.density >= section.density:
            shape_bonus += 6.0
        if "CHORUS" in next_section.label.upper() and next_section.density >= section.density:
            shape_bonus += 5.0
        if "OUTRO" in next_section.label.upper() and next_section.density <= section.density:
            shape_bonus += 4.0
    musical_coherence = _clamp((token_score * 0.72) + shape_bonus, 0.0, 100.0)

    overlap_score = _clamp(100.0 - (overlap_ratio * 420.0), 0.0, 100.0)
    clutter_score = _clamp(100.0 - (clutter_ratio * 160.0), 0.0, 100.0)
    section_score = _clamp(section_coverage * 100.0, 0.0, 100.0)
    overall = (
        overlap_score * 0.30
        + clutter_score * 0.18
        + section_score * 0.17
        + intensity_balance * 0.19
        + musical_coherence * 0.16
    )

    return AuditResult(
        score=overall,
        grade=_grade(overall),
        overlap_ratio=overlap_ratio,
        clutter_ratio=clutter_ratio,
        section_coverage=section_coverage,
        intensity_balance=intensity_balance,
        musical_coherence=musical_coherence,
        auto_fixed=auto_fix,
        fixes_applied=fixes_applied,
        fixes=fixes,
        section_scores=section_scores,
    )
