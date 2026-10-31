"""Strict drummer-oracle comparison, independent of sequence generation.

Only comparable event streams from the approved baseline and candidate may be
evaluated. No guessed oracle counts or synthetic acceptance evidence.
"""
from __future__ import annotations

from collections import Counter
from typing import Any


def compare_drum_events(
    oracle: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
    *,
    tolerance_ms: int = 30,
) -> dict[str, Any]:
    """Match each event once, within the same drum class and timing tolerance."""
    if tolerance_ms < 0:
        raise ValueError("tolerance_ms must be nonnegative")
    def normalize(rows: list[dict[str, Any]]) -> list[tuple[str, int]]:
        result = []
        for row in rows:
            drum_class = str(row.get("drum_type") or row.get("class") or "").strip()
            if not drum_class:
                raise ValueError("every drum event requires a drum class")
            time = row.get("timestamp_ms", row.get("time_ms"))
            if isinstance(time, bool) or time is None:
                raise ValueError("every drum event requires a valid timestamp")
            import math
            try:
                value = float(time)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid drum timestamp") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError("invalid drum timestamp")
            result.append((drum_class, int(round(value))))
        return sorted(result)
    expected, actual = normalize(oracle), normalize(candidate)
    by_class_expected: dict[str, list[int]] = {}
    by_class_actual: dict[str, list[int]] = {}
    for drum_class, timestamp in expected:
        by_class_expected.setdefault(drum_class, []).append(timestamp)
    for drum_class, timestamp in actual:
        by_class_actual.setdefault(drum_class, []).append(timestamp)
    matched = 0
    drift: list[int] = []
    counts: dict[str, dict[str, int]] = {}
    for drum_class in sorted(set(by_class_expected) | set(by_class_actual)):
        baseline = by_class_expected.get(drum_class, [])
        observed = by_class_actual.get(drum_class, [])
        # Ordered one-to-one matching avoids reusing one candidate hit twice.
        # Greedy earliest admissible match is deterministic.
        used: set[int] = set()
        hits = 0
        for timestamp in baseline:
            options = [(abs(other - timestamp), j) for j, other in enumerate(observed)
                       if j not in used and abs(other - timestamp) <= tolerance_ms]
            if options:
                distance, j = min(options)
                used.add(j)
                hits += 1
                drift.append(distance)
        matched += hits
        counts[drum_class] = {
            "oracle": len(baseline), "candidate": len(observed),
            "matched": hits, "false_negative": len(baseline) - hits,
            "false_positive": len(observed) - hits,
        }
    false_negative = len(expected) - matched
    false_positive = len(actual) - matched
    return {
        "schema": "helix.drummer_oracle_comparison.v1",
        "tolerance_ms": tolerance_ms,
        "oracle_events": len(expected),
        "candidate_events": len(actual),
        "matched": matched,
        "false_negative": false_negative,
        "false_positive": false_positive,
        "mean_absolute_drift_ms": round(sum(drift) / len(drift), 3) if drift else None,
        "max_absolute_drift_ms": max(drift) if drift else None,
        "counts_by_class": counts,
        "exact_within_tolerance": false_negative == 0 and false_positive == 0,
    }
