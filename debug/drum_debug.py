from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio.drum_detection import detect_drum_event_streams_from_file
from mapping.drum_mapper import flatten_drum_streams


def drum_debug_summary(streams: dict[str, list[object]]) -> dict[str, object]:
    events = flatten_drum_streams(streams)  # type: ignore[arg-type]
    confidences = [event.confidence for event in events]
    if events:
        end_ms = max(event.timestamp_ms for event in events)
        bins = max(1, min(80, end_ms // 250 + 1))
        density = [0 for _ in range(bins)]
        for event in events:
            density[min(bins - 1, event.timestamp_ms // 250)] += 1
    else:
        density = []
    return {
        "counts": {key: len(value) for key, value in streams.items()},
        "confidence": {
            "min": round(min(confidences), 3) if confidences else 0.0,
            "max": round(max(confidences), 3) if confidences else 0.0,
            "avg": round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
        },
        "density_graph": "".join(chr(9601 + min(7, value)) for value in density),
        "timeline": [
            f"{event.timestamp_ms:06d}ms {event.drum_type:<8} v={event.velocity:.2f} c={event.confidence:.2f} cluster={event.cluster_id}"
            for event in events[:400]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug Helix drum intelligence event streams.")
    parser.add_argument("audio", help="Audio file to analyze")
    parser.add_argument("--json", dest="json_out", default="", help="Optional JSON output path")
    args = parser.parse_args()
    streams = detect_drum_event_streams_from_file(Path(args.audio))
    summary = drum_debug_summary(streams)
    print(json.dumps(summary, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
