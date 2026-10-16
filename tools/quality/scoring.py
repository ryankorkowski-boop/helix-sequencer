"""Original structural metrics, separate from native or hardware validation."""

from __future__ import annotations

import math
from bisect import bisect_left
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from statistics import median
from typing import Any

from tools.quality.inputs import (
    Effect, Model, finite, read_layout, read_sequence,
)


THRESHOLDS = {
    "onset_p95_ms": 100,
    "minimum_onset_match_fraction": 0.8,
    "minimum_energy_correlation": 0.5,
    "maximum_repetition_rate": 0.5,
    "dead_air_ms": 1000,
    "maximum_focal_points": 2,
    "minimum_palette_consistency": 0.5,
}


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def _correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2:
        return None
    a, b = sum(left) / len(left), sum(right) / len(right)
    av, bv = [x - a for x in left], [x - b for x in right]
    denominator = math.sqrt(sum(x*x for x in av) * sum(x*x for x in bv))
    if not denominator:
        return None
    return sum(x*y for x, y in zip(av, bv)) / denominator


def _windows(raw: Any, duration: float) -> list[tuple[float, float]]:
    if not isinstance(raw, list):
        raise ValueError("Windows must be a list")
    result = []
    for window in raw:
        start, end = finite(window["start_ms"]), finite(window["end_ms"])
        if not 0 <= start < end <= duration:
            raise ValueError("Windows must lie inside the sequence duration")
        result.append((start, end))
    return result


def _metrics(
    effects: list[Effect], models: dict[str, Model],
    features: Mapping[str, Any], start: float, end: float,
    weights: dict[str, float],
) -> dict[str, Any]:
    overlapping = [e for e in effects if e.start < end and e.end > start]
    visible = [e for e in overlapping if max(e.start_level, e.end_level) > 0]
    starting = [e for e in visible if start <= e.start < end]
    warnings: set[str] = set()
    planned = features.get("sections", [])
    for index, earlier in enumerate(planned):
        for later in planned[index + 1:]:
            if all("energy" in s and "energy_budget" in s
                   for s in (earlier, later)):
                if (finite(later["energy"]) > finite(earlier["energy"]) + 1e-6
                        and finite(later["energy_budget"])
                        <= finite(earlier["energy_budget"])):
                    warnings.add("section_energy_budget_not_increasing")
    # Match a detected onset only to a causal start within 500 ms.
    onsets = [finite(t) for t in features.get("onsets_ms", [])
              if start <= finite(t) < end]
    starts = sorted({e.start for e in starting})
    latencies = []
    for onset in onsets:
        index = bisect_left(starts, onset)
        if index < len(starts) and starts[index] - onset <= 500:
            latencies.append(starts[index] - onset)
    matched = len(latencies) / len(onsets) if onsets else None
    p95 = _percentile(latencies, 0.95)
    if not onsets:
        warnings.add("onset_latency_unavailable")
    if ((p95 is not None and p95 > THRESHOLDS["onset_p95_ms"])
            or (matched is not None and matched < 0.8)):
        warnings.add("onset_alignment_outside_threshold")

    by_class: dict[str, Counter[str]] = defaultdict(Counter)
    for effect in starting:
        for name in effect.models:
            by_class[models[name].model_class][effect.name] += 1
    diversity = {}
    for name, counts in sorted(by_class.items()):
        total = sum(counts.values())
        entropy = -sum((n / total) * math.log2(n / total)
                       for n in counts.values())
        diversity[name] = {"effect_counts": dict(sorted(counts.items())),
                           "entropy_bits": round(entropy, 6)}

    by_lane: dict[tuple[str, str], list[Effect]] = defaultdict(list)
    for effect in starting:
        by_lane[effect.target, effect.layer].append(effect)
    adjacent = recent = comparisons = 0
    for lane in by_lane.values():
        last: dict[tuple[str, ...], float] = {}
        for index, effect in enumerate(lane):
            if index:
                comparisons += 1
                adjacent += effect.signature == lane[index - 1].signature
                previous = last.get(effect.signature, -math.inf)
                recent += effect.start - previous <= 5000
            last[effect.signature] = effect.start
    repetition = max(adjacent, recent) / comparisons if comparisons else 0.0
    if repetition > THRESHOLDS["maximum_repetition_rate"]:
        warnings.add("repetition_outside_threshold")

    # Exact effect-presence sweep, with ends before starts at a shared time.
    events: dict[float, int] = defaultdict(int)
    for effect in visible:
        events[max(start, effect.start)] += 1
        events[min(end, effect.end)] -= 1
    count = peak = 0
    cursor = start
    gaps = []
    for time, delta in sorted(events.items()):
        if count == 0 and time > cursor:
            gaps.append((cursor, time))
        count += delta
        peak = max(peak, count)
        cursor = time
    if cursor < end:
        gaps.append((cursor, end))
    restraint = _windows(features.get("intentional_restraint", []),
                         finite(features["duration_ms"]))
    dead_air = []
    for left, right in gaps:
        cuts = sorted({left, right} | {
            max(left, min(right, t)) for span in restraint for t in span
        })
        for a, b in zip(cuts, cuts[1:]):
            intentional = any(x <= a and b <= y for x, y in restraint)
            dead_air.append({"start_ms": a, "end_ms": b,
                             "intentional": intentional})
            if not intentional and b - a >= THRESHOLDS["dead_air_ms"]:
                warnings.add("unintentional_dead_air")

    # Fixed 100 ms midpoint samples. Union expanded group targets per model.
    coverage, focal = [], []
    times = [start + min(t + 50, (t + end - start) / 2)
             for t in range(0, math.ceil(end - start), 100)]
    sample_events = sorted(
        (time, delta, index)
        for index, effect in enumerate(visible)
        for time, delta in ((effect.start, 1), (effect.end, -1))
    )
    active: set[int] = set()
    event_index = 0
    total_weight = sum(weights.values())
    for time in times:
        while (event_index < len(sample_events)
               and sample_events[event_index][0] <= time):
            _, delta, index = sample_events[event_index]
            if delta < 0:
                active.discard(index)
            else:
                active.add(index)
            event_index += 1
        levels: dict[str, float] = {}
        for index in sorted(active):
            effect = visible[index]
            for name in effect.models:
                levels[name] = max(levels.get(name, 0),
                                   effect.intensity(time))
        coverage.append(sum(weights[n] for n, level in levels.items()
                            if level > 0) / total_weight)
        maximum = max(levels.values(), default=0)
        focal.append(sum(v >= max(0.8, maximum * 0.9)
                         for v in levels.values()))
    energy_raw = features.get("energy", [])
    energy = [(finite(p["time_ms"]), finite(p["value"])) for p in energy_raw]
    curve_times = [t for t, _ in energy]
    paired_coverage, paired_energy = [], []
    for time, value in zip(times, coverage):
        if not energy or time < curve_times[0] or time > curve_times[-1]:
            continue
        index = bisect_left(curve_times, time)
        if curve_times[index] == time or index == 0:
            level = energy[index][1]
        else:
            t0, v0 = energy[index - 1]
            t1, v1 = energy[index]
            level = v0 + (v1 - v0) * (time - t0) / (t1 - t0)
        paired_coverage.append(value)
        paired_energy.append(level)
    correlation = _correlation(paired_energy, paired_coverage)
    if correlation is None:
        warnings.add("energy_correlation_unavailable_or_constant")
    elif correlation < THRESHOLDS["minimum_energy_correlation"]:
        warnings.add("energy_tracking_outside_threshold")
    if max(focal, default=0) > THRESHOLDS["maximum_focal_points"]:
        warnings.add("focal_count_outside_threshold")

    palettes = Counter(e.palette for e in starting if e.palette)
    consistency = (max(palettes.values()) / sum(palettes.values())
                   if palettes else None)
    if consistency is None:
        warnings.add("palette_consistency_unavailable")
    elif consistency < THRESHOLDS["minimum_palette_consistency"]:
        warnings.add("palette_consistency_outside_threshold")
    return {
        "start_ms": start, "end_ms": end, "effect_count": len(starting),
        "onset_latency": {
            "median_ms": _rounded(
                median(latencies) if latencies else None),
            "p95_ms": _rounded(p95), "onset_count": len(onsets),
            "matched_count": len(latencies),
            "match_fraction": _rounded(matched),
        },
        "diversity_by_model_class": diversity,
        "energy_tracking": {
            "correlation": _rounded(correlation),
            "paired_samples": len(paired_energy),
            "mean_lit_fraction_estimate": _rounded(
                sum(coverage) / len(coverage) if coverage else None),
        },
        "repetition": {"adjacent_identical": adjacent,
                       "within_5s_identical": recent,
                       "comparisons": comparisons,
                       "rate": _rounded(repetition)},
        "dead_air": dead_air, "peak_simultaneous_effects": peak,
        "focal_points_estimate": {"peak": max(focal, default=0),
                                  "p95": _rounded(_percentile(focal, 0.95))},
        "palette_consistency": _rounded(consistency),
        "warnings": sorted(warnings),
    }


def score_sequence(
    xsq_path: str | Path, layout_path: str | Path,
    audio_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Return JSON diagnostics, with no writes or global RNG use."""
    models, targets = read_layout(layout_path)
    override = audio_features.get("legacy_millisecond_times", False)
    if not isinstance(override, bool):
        raise ValueError("legacy_millisecond_times must be a boolean")
    effects, sequence_duration, warnings = read_sequence(
        xsq_path, targets, legacy_millisecond_times=override)
    duration = finite(audio_features.get("duration_ms", sequence_duration))
    if duration <= 0:
        raise ValueError("A positive sequence duration is required")
    if sequence_duration and abs(duration - sequence_duration) > 1:
        raise ValueError("Feature duration does not match XSQ duration")
    if any(e.end > duration + 1 for e in effects):
        raise ValueError("Effect extends past sequence duration")
    onsets = [finite(t) for t in audio_features.get("onsets_ms", [])]
    if any(t < 0 or t >= duration for t in onsets):
        raise ValueError("Onsets must lie inside the sequence")
    energy = audio_features.get("energy", [])
    times = [finite(p["time_ms"]) for p in energy]
    if (any(a >= b for a, b in zip(times, times[1:]))
            or any(t < 0 or t > duration for t in times)
            or any(not 0 <= finite(p["value"]) <= 1 for p in energy)):
        raise ValueError(
            "Energy requires increasing times and values in [0, 1]")
    sections = audio_features.get("sections", [])
    if not sections:
        warnings.append("section_metrics_unavailable")
    windows = _windows(sections, duration)
    if any(a[1] > b[0] for a, b in zip(windows, windows[1:])):
        raise ValueError("Sections must be ordered and nonoverlapping")
    ids = [str(s["id"]) for s in sections]
    if len(set(ids)) != len(ids) or any(not s for s in ids):
        raise ValueError("Section ids must be unique and nonempty")
    features = dict(audio_features, duration_ms=duration)
    channel_weights = all(m.channels is not None for m in models.values())
    weights = {n: (m.channels or 1.0) if channel_weights else 1.0
               for n, m in models.items()}
    if not channel_weights:
        warnings.append("channel_counts_unavailable_using_equal_model_weights")
    return {
        "schema": "helix.quality.v1",
        "basis": "structural_estimate_not_native_render",
        "coverage_weighting": (
            "declared_channels" if channel_weights else "models"),
        "native_render_verified": False,
        "thresholds": dict(THRESHOLDS),
        "warnings": sorted(set(warnings)),
        "overall": _metrics(effects, models, features, 0.0, duration, weights),
        "sections": [dict(id=name, **_metrics(
            effects, models, features, start, end, weights
        )) for name, (start, end) in zip(ids, windows)],
    }
