"""Strict drummer-oracle comparison, independent of sequence generation.

Only comparable event streams from the approved baseline and candidate may be
evaluated. No guessed oracle counts or synthetic acceptance evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
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
        # Ordered two-pointer matching maximizes match count within tolerance
        # without allowing a candidate hit to satisfy two oracle hits.
        i = j = hits = 0
        while i < len(baseline) and j < len(observed):
            difference = observed[j] - baseline[i]
            if abs(difference) <= tolerance_ms:
                hits += 1
                drift.append(abs(difference))
                i += 1
                j += 1
            elif difference < -tolerance_ms:
                j += 1
            else:
                i += 1
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


def compare_oracle_files(
    oracle_path: str | Path,
    candidate_path: str | Path,
    *,
    tolerance_ms: int = 30,
) -> dict[str, Any]:
    """Compare actual saved JSON event lists; never substitute a synthetic oracle."""
    def read_events(path: str | Path) -> list[dict[str, Any]]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("events")
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError(f"{path}: expected JSON event list or object with events list")
        return data
    return compare_drum_events(
        read_events(oracle_path), read_events(candidate_path),
        tolerance_ms=tolerance_ms,
    )


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Compare real drummer event JSON against the approved oracle")
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--tolerance-ms", type=int, default=30)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = compare_oracle_files(args.oracle, args.candidate, tolerance_ms=args.tolerance_ms)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["exact_within_tolerance"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
