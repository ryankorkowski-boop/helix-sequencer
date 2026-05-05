from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from core import model_parser as xmp


def _family_key(model: xmp.Model, fallback: str | None = None) -> str:
    semantic = (model.type or "").strip().lower()
    if semantic in {"tree"}:
        name = xmp.normalize_name(model.name)
        if "garage" in name:
            return "gt"
        return "mega"
    if semantic in {"arch", "matrix", "spinner", "sphere", "line", "flood", "star", "image"}:
        return {
            "arch": "arch",
            "matrix": "matrix",
            "spinner": "spinner",
            "sphere": "sphere",
            "line": "line",
            "flood": "flood",
            "star": "stars",
            "image": "matrix",
        }[semantic]
    if semantic in {"cane"}:
        return "canes_combo"
    if semantic in {"circle", "wreath"}:
        return "sphere"
    if semantic in {"icicle", "window", "channelblock", "multipoint"}:
        return "line"
    if semantic in {"custom", "cube"}:
        return "matrix"
    return (fallback or "").strip().lower()


@dataclass
class CoveragePlan:
    family_counts: dict[str, int] = field(default_factory=dict)
    uncovered_models: list[str] = field(default_factory=list)
    recommended_targets: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "family_counts": self.family_counts,
            "uncovered_models": self.uncovered_models,
            "recommended_targets": self.recommended_targets,
        }


def summarize_family_counts(parsed_layout: xmp.ParsedLayout | None) -> dict[str, int]:
    if parsed_layout is None:
        return {}
    counts: Counter[str] = Counter()
    for model in parsed_layout.models.values():
        if model.is_submodel:
            continue
        family = _family_key(model)
        if family:
            counts[family] += 1
    return {key: counts[key] for key in sorted(counts)}


def collect_coverage_targets(
    *,
    parsed_layout: xmp.ParsedLayout | None,
    available_layer_names: Iterable[str],
    used_root_models: set[str],
    model_category_map: Mapping[str, str],
    limit: int = 48,
) -> CoveragePlan:
    if parsed_layout is None:
        return CoveragePlan()

    available = {name for name in available_layer_names}
    family_counts = summarize_family_counts(parsed_layout)
    family_models: dict[str, list[tuple[float, str]]] = defaultdict(list)
    uncovered: list[str] = []

    for model in parsed_layout.models.values():
        if model.is_submodel or model.name not in available:
            continue
        family = _family_key(model, model_category_map.get(model.name, ""))
        if not family:
            continue
        center = model.center()
        family_models[family].append((center[0], model.name))
        if model.name not in used_root_models:
            uncovered.append(model.name)

    if not uncovered:
        return CoveragePlan(family_counts=family_counts)

    ordered_targets: list[str] = []
    family_use = Counter(
        _family_key(parsed_layout.model_for(name), model_category_map.get(name, ""))
        for name in used_root_models
        if parsed_layout.model_for(name) is not None
    )
    for family, points in sorted(
        family_models.items(),
        key=lambda item: (
            family_use.get(item[0], 0),
            -len(item[1]),
            item[0],
        ),
    ):
        points.sort(key=lambda item: item[0])
        for _x, name in points:
            if name in used_root_models or name in ordered_targets:
                continue
            ordered_targets.append(name)
            if len(ordered_targets) >= max(1, int(limit)):
                break
        if len(ordered_targets) >= max(1, int(limit)):
            break

    if len(ordered_targets) < max(1, int(limit)):
        remaining = [name for name in uncovered if name not in ordered_targets]
        ordered_targets.extend(remaining[: max(0, int(limit) - len(ordered_targets))])

    return CoveragePlan(
        family_counts=family_counts,
        uncovered_models=sorted(uncovered),
        recommended_targets=ordered_targets[: max(1, int(limit))],
    )
