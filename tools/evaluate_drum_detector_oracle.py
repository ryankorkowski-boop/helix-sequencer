#!/usr/bin/env python3
"""Evaluate Helix drum detection against a timestamped labeled drum oracle."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from audio.drum_detection import detect_drum_event_streams_from_file
from mapping.drum_mapper import flatten_drum_streams


ORACLE_FAMILY = {
    "kick": "kick",
    "snare": "snare",
    "hat": "hihat",
    "hihat": "hihat",
    "crash": "cymbal",
    "cymbal": "cymbal",
    "tom": "tom",
    "tom_low": "tom",
    "tom_mid": "tom",
    "tom_high": "tom",
}


def _match_times(
    truth_ms: list[int],
    detected_ms: list[int],
    *,
    tolerance_ms: int,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Greedily match each truth event to its nearest unused detection."""
    available = set(range(len(detected_ms)))
    matches: list[tuple[int, int]] = []
    missed_truth: list[int] = []
    for truth in sorted(truth_ms):
        candidates = [
            (abs(detected_ms[idx] - truth), idx)
            for idx in available
            if abs(detected_ms[idx] - truth) <= tolerance_ms
        ]
        if not candidates:
            missed_truth.append(truth)
            continue
        _, idx = min(candidates, key=lambda item: (item[0], detected_ms[item[1]]))
        available.remove(idx)
        matches.append((truth, detected_ms[idx]))
    false_positive = [detected_ms[idx] for idx in sorted(available)]
    return matches, missed_truth, false_positive


def evaluate(
    audio_path: Path,
    events_path: Path,
    *,
    tolerance_ms: int = 70,
) -> dict[str, object]:
    truth_payload = json.loads(events_path.read_text(encoding="utf-8"))
    truth_by_family: dict[str, list[int]] = defaultdict(list)
    for item in truth_payload:
        if not isinstance(item, dict):
            continue
        family = ORACLE_FAMILY.get(str(item.get("event", "")).strip().lower())
        if not family:
            continue
        truth_by_family[family].append(int(round(float(item.get("time", 0.0)) * 1000.0)))

    streams = detect_drum_event_streams_from_file(audio_path, source_label="oracle:mix")
    detected = flatten_drum_streams(streams)
    detected_by_family: dict[str, list[int]] = defaultdict(list)
    for event in detected:
        if event.drum_type in {"kick", "snare", "tom", "hihat", "cymbal"}:
            detected_by_family[event.drum_type].append(event.timestamp_ms)

    families = ("kick", "snare", "tom", "hihat", "cymbal")
    metrics: dict[str, dict[str, object]] = {}
    total_tp = total_fp = total_fn = 0
    all_offsets: list[int] = []

    for family in families:
        truth = sorted(truth_by_family.get(family, []))
        found = sorted(detected_by_family.get(family, []))
        matches, missed, false_positive = _match_times(
            truth,
            found,
            tolerance_ms=max(0, int(tolerance_ms)),
        )
        tp = len(matches)
        fp = len(false_positive)
        fn = len(missed)
        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        offsets = [detected_ms - truth_ms for truth_ms, detected_ms in matches]
        all_offsets.extend(offsets)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        metrics[family] = {
            "truth": len(truth),
            "detected": len(found),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "mean_offset_ms": round(sum(offsets) / len(offsets), 2) if offsets else 0.0,
            "max_abs_offset_ms": max((abs(value) for value in offsets), default=0),
            "missed_truth_ms": missed,
            "false_positive_ms": false_positive,
        }

    micro_precision = total_tp / max(1, total_tp + total_fp)
    micro_recall = total_tp / max(1, total_tp + total_fn)
    micro_f1 = (
        2.0 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall)
        else 0.0
    )
    return {
        "audio": str(audio_path),
        "events": str(events_path),
        "tolerance_ms": int(tolerance_ms),
        "detected_stream_counts": {key: len(value) for key, value in sorted(streams.items())},
        "families": metrics,
        "micro": {
            "true_positive": total_tp,
            "false_positive": total_fp,
            "false_negative": total_fn,
            "precision": round(micro_precision, 4),
            "recall": round(micro_recall, 4),
            "f1": round(micro_f1, 4),
            "mean_offset_ms": round(sum(all_offsets) / len(all_offsets), 2) if all_offsets else 0.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("events", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance-ms", type=int, default=70)
    args = parser.parse_args()

    report = evaluate(
        args.audio,
        args.events,
        tolerance_ms=args.tolerance_ms,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
