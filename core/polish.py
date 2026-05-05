from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from tools.build_helpers import expand_neighbor_targets


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


def _flatten_entries(timelines: dict[str, Any]) -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    for model_name, timeline in timelines.items():
        for layer_name, entries in getattr(timeline, "layers", {}).items():
            for entry in list(entries):
                rows.append((model_name, layer_name, entry))
    return rows


def _nearest_anchor(value: int, anchors: list[int], tolerance_ms: int) -> int | None:
    best: int | None = None
    best_delta = tolerance_ms + 1
    for anchor in anchors:
        delta = abs(anchor - value)
        if delta > tolerance_ms:
            continue
        if delta < best_delta:
            best = anchor
            best_delta = delta
    return best


def _section_density(entries: list[tuple[str, str, Any]], start_ms: int, end_ms: int) -> float:
    duration_ms = max(1, end_ms - start_ms)
    hits = 0
    for _model_name, _layer_name, entry in entries:
        overlap = max(
            0,
            min(end_ms, int(getattr(entry, "end", 0))) - max(start_ms, int(getattr(entry, "start", 0))),
        )
        if overlap > 0:
            hits += 1
    return (hits * 1000.0) / float(duration_ms)


def _apply_transition_palette(
    *,
    entry: Any,
    palette: str,
) -> bool:
    if not palette:
        return False
    try:
        current = entry.xml_effect.attrib.get("palette", "")
        if current == palette:
            return False
        entry.xml_effect.attrib["palette"] = palette
        return True
    except Exception:
        return False


def section_transition_windows(parts: list[Any], padding_ms: int = 180) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    pad = max(40, int(padding_ms))
    for idx in range(1, len(parts)):
        boundary = int(getattr(parts[idx], "start_ms", 0))
        windows.append((max(0, boundary - pad), boundary + pad))
    return windows


@dataclass
class PolishResult:
    score: float
    overlap_repairs: int = 0
    section_rebalances: int = 0
    breathing_fades: int = 0
    hook_enhancements: int = 0
    retimed_entries: int = 0
    palette_swaps: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "overlap_repairs": int(self.overlap_repairs),
            "section_rebalances": int(self.section_rebalances),
            "breathing_fades": int(self.breathing_fades),
            "hook_enhancements": int(self.hook_enhancements),
            "retimed_entries": int(self.retimed_entries),
            "palette_swaps": int(self.palette_swaps),
            "notes": self.notes[:64],
        }


def apply_polish_pass(
    *,
    timelines: dict[str, Any],
    parts: list[Any],
    quiet_windows: list[tuple[int, int]],
    add_model,
    min_effect_ms: int = 50,
    used_root_models: set[str] | None = None,
    neighbor_graph: Any | None = None,
    template_palette_pool: list[str] | None = None,
    vocal_peaks: list[int] | None = None,
    bass_peaks: list[int] | None = None,
    drum_peaks: list[int] | None = None,
) -> PolishResult:
    min_effect_ms = max(1, int(min_effect_ms))
    notes: list[str] = []
    overlap_repairs = 0
    section_rebalances = 0
    breathing_fades = 0
    hook_enhancements = 0
    retimed_entries = 0
    palette_swaps = 0

    for _model_name, timeline in timelines.items():
        flattened: list[tuple[str, Any]] = []
        for layer_name, entries in getattr(timeline, "layers", {}).items():
            entries.sort(key=lambda item: (item.start, item.end))
            for entry in list(entries):
                flattened.append((layer_name, entry))
        flattened.sort(key=lambda item: (int(getattr(item[1], "start", 0)), -int(getattr(item[1], "priority", 0))))
        for idx in range(1, len(flattened)):
            prev_layer, prev = flattened[idx - 1]
            curr_layer, curr = flattened[idx]
            if int(getattr(curr, "start", 0)) >= int(getattr(prev, "end", 0)):
                continue
            prev_priority = int(getattr(prev, "priority", 0))
            curr_priority = int(getattr(curr, "priority", 0))
            if curr_priority > prev_priority or (curr_priority == prev_priority and curr_layer == "accent"):
                trim_entry = prev
                keep_entry = curr
            else:
                trim_entry = curr
                keep_entry = prev
            trim_start = int(getattr(trim_entry, "start", 0))
            trim_end = int(getattr(trim_entry, "end", 0))
            keep_start = int(getattr(keep_entry, "start", 0))
            keep_end = int(getattr(keep_entry, "end", 0))
            left_len = max(0, keep_start - trim_start)
            right_len = max(0, trim_end - keep_end)
            if right_len >= left_len and right_len >= min_effect_ms:
                _set_entry_window(trim_entry, keep_end, trim_end)
                overlap_repairs += 1
            elif left_len >= min_effect_ms:
                _set_entry_window(trim_entry, trim_start, keep_start)
                overlap_repairs += 1

    anchors = sorted(set((vocal_peaks or []) + (bass_peaks or []) + (drum_peaks or [])))
    if anchors:
        for _model_name, timeline in timelines.items():
            for _layer_name, entries in getattr(timeline, "layers", {}).items():
                entries.sort(key=lambda item: (item.start, item.end))
                for idx, entry in enumerate(entries):
                    start_ms = int(getattr(entry, "start", 0))
                    end_ms = int(getattr(entry, "end", 0))
                    duration_ms = end_ms - start_ms
                    if duration_ms < min_effect_ms:
                        continue
                    anchor = _nearest_anchor(start_ms, anchors, tolerance_ms=70)
                    if anchor is None:
                        continue
                    delta = anchor - start_ms
                    if abs(delta) < 16:
                        continue
                    new_start = start_ms + delta
                    new_end = end_ms + delta
                    prev_end = int(getattr(entries[idx - 1], "end", -10**9)) if idx > 0 else -10**9
                    next_start = int(getattr(entries[idx + 1], "start", 10**9)) if idx + 1 < len(entries) else 10**9
                    if new_start < prev_end or new_end > next_start or (new_end - new_start) < min_effect_ms:
                        continue
                    _set_entry_window(entry, new_start, new_end)
                    retimed_entries += 1

    flattened_entries = _flatten_entries(timelines)
    if parts:
        densities = [
            _section_density(flattened_entries, int(getattr(part, "start_ms", 0)), int(getattr(part, "end_ms", 0)))
            for part in parts
        ]
        avg_density = mean(densities) if densities else 0.0
        for idx, part in enumerate(parts):
            label = str(getattr(part, "label", "") or "").upper()
            start_ms = int(getattr(part, "start_ms", 0))
            end_ms = int(getattr(part, "end_ms", 0))
            energy = float(getattr(part, "energy", 0.0) or 0.0)
            density = densities[idx] if idx < len(densities) else 0.0
            if label in {"INTRO", "VERSE", "OUTRO"} and density > max(avg_density * 1.15, 1.0):
                for _model_name, layer_name, entry in list(flattened_entries):
                    if layer_name == "base":
                        continue
                    if int(getattr(entry, "start", 0)) < start_ms or int(getattr(entry, "start", 0)) >= end_ms:
                        continue
                    duration_ms = _entry_len(entry)
                    if duration_ms <= (min_effect_ms + 30):
                        continue
                    shrink_ms = min(80, max(24, duration_ms // 10))
                    _set_entry_window(entry, int(getattr(entry, "start", 0)), int(getattr(entry, "end", 0)) - shrink_ms)
                    section_rebalances += 1
                    if section_rebalances >= 18:
                        break
            if label in {"CHORUS", "DROP", "HOOK"} or energy >= 0.72:
                if density >= max(avg_density * 0.95, 0.9):
                    continue
                hook_time = start_ms + 40
                seed_models = list(sorted(used_root_models or set(timelines.keys())))[:4]
                if neighbor_graph is not None and seed_models:
                    seed_models = expand_neighbor_targets(neighbor_graph, seed_models[:2], depth=1, limit=6)
                for offset, model_name in enumerate(seed_models[:6]):
                    add_model(
                        model_name,
                        hook_time + (offset * 24),
                        min(end_ms, hook_time + 220 + (offset * 24)),
                        "polish_hook_enhancement",
                        eff="Ramp" if offset % 2 else "On",
                        stem="vocals" if offset % 2 == 0 else "bass",
                    )
                    hook_enhancements += 1

    quiet_plus_transitions = list(quiet_windows or []) + section_transition_windows(parts)
    breathing_targets = list(sorted(used_root_models or set(timelines.keys())))[:4]
    if neighbor_graph is not None and breathing_targets:
        breathing_targets = expand_neighbor_targets(neighbor_graph, breathing_targets[:2], depth=1, limit=6)
    for start_ms, end_ms in quiet_plus_transitions[:10]:
        if (end_ms - start_ms) < max(140, min_effect_ms):
            continue
        for idx, model_name in enumerate(breathing_targets[:4]):
            add_model(
                model_name,
                start_ms + (idx * 12),
                max(start_ms + min_effect_ms, end_ms - (idx * 8)),
                "polish_breathing_fade",
                eff="Ramp",
                stem="vocals",
            )
            breathing_fades += 1

    palettes = [palette for palette in (template_palette_pool or []) if palette]
    if palettes:
        transitions = section_transition_windows(parts, padding_ms=240)
        boundary_index = 0
        for _model_name, _layer_name, entry in flattened_entries:
            start_ms = int(getattr(entry, "start", 0))
            while boundary_index + 1 < len(transitions) and start_ms > transitions[boundary_index][1]:
                boundary_index += 1
            if not transitions:
                break
            transition_start, transition_end = transitions[min(boundary_index, len(transitions) - 1)]
            if transition_start <= start_ms <= transition_end:
                palette = palettes[boundary_index % len(palettes)]
                if _apply_transition_palette(entry=entry, palette=palette):
                    palette_swaps += 1

    if overlap_repairs:
        notes.append(f"Resolved {overlap_repairs} melody-priority overlaps.")
    if section_rebalances:
        notes.append(f"Rebalanced {section_rebalances} crowded low-energy windows.")
    if hook_enhancements:
        notes.append(f"Lifted hooks and drops with {hook_enhancements} polish accents.")
    if breathing_fades:
        notes.append(f"Added {breathing_fades} breathing fades around quiet or transition windows.")
    if retimed_entries:
        notes.append(f"Micro-timed {retimed_entries} entries onto stem anchors.")
    if palette_swaps:
        notes.append(f"Applied {palette_swaps} color-flow transitions near section boundaries.")

    score = 76.0
    score += min(8.0, overlap_repairs * 0.35)
    score += min(5.0, section_rebalances * 0.20)
    score += min(5.0, hook_enhancements * 0.10)
    score += min(4.0, breathing_fades * 0.08)
    score += min(4.0, retimed_entries * 0.08)
    score += min(3.0, palette_swaps * 0.05)

    return PolishResult(
        score=_clamp(score, 0.0, 100.0),
        overlap_repairs=overlap_repairs,
        section_rebalances=section_rebalances,
        breathing_fades=breathing_fades,
        hook_enhancements=hook_enhancements,
        retimed_entries=retimed_entries,
        palette_swaps=palette_swaps,
        notes=notes,
    )
