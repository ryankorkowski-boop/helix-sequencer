#!/usr/bin/env python3
"""Run Helix drum detection and emit measurable classification diagnostics."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from audio.drum_detection import detect_drum_event_streams_from_file
from audio.drum_classification import classify_drum_hit


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("audio", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    streams = detect_drum_event_streams_from_file(args.audio)
    counts = Counter()
    confidence = {}
    events = []
    for stream, items in streams.items():
        for event in items:
            features = dict(getattr(event, "features", {}) or {})
            drum_type, score = classify_drum_hit(features)
            counts[drum_type] += 1
            confidence.setdefault(drum_type, []).append(score)
            events.append({
                "timestamp": round(float(getattr(event, "timestamp", 0.0)), 6),
                "source_stream": stream,
                "classified_type": drum_type,
                "confidence": score,
            })
    events.sort(key=lambda x: x["timestamp"])
    summary = {
        "audio": str(args.audio),
        "candidate_events": len(events),
        "class_counts": dict(sorted(counts.items())),
        "confidence": {
            key: {"count": len(values), "min": min(values), "max": max(values), "mean": round(sum(values)/len(values), 4)}
            for key, values in sorted(confidence.items()) if values
        },
        "events": events,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("audio", "candidate_events", "class_counts", "confidence")}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
