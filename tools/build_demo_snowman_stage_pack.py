from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from audio.drum_classification import DrumEvent
from models.working_stage_pack import build_reactive_snowman_stage_pack


DEFAULT_OUTPUT_PATH = Path("outputs/demo_snowman_stage_pack.json")


def _drum_event(ms: int, drum_type: str, velocity: float, confidence: float) -> DrumEvent:
    return DrumEvent(
        timestamp=round(ms / 1000.0, 4),
        velocity=velocity,
        confidence=confidence,
        frequency_band_info={"demo_ms": float(ms), "demo_source": 1.0},
        cluster_id=ms,
        drum_type=drum_type,
        source="demo_stage_pack",
    )


def _demo_inputs() -> dict[str, Any]:
    return {
        "lyric_events": [
            SimpleNamespace(start_ms=120, end_ms=720, text="audio in", confidence=0.86),
            SimpleNamespace(start_ms=760, end_ms=1320, text="lights out", confidence=0.88),
        ],
        "female_lyric_events": [
            SimpleNamespace(start_ms=1360, end_ms=1980, text="shine bright", confidence=0.84),
            SimpleNamespace(start_ms=2020, end_ms=2520, text="snow tonight", confidence=0.82),
        ],
        "vocal_peaks": [160, 420, 820, 1120],
        "female_vocal_peaks": [1420, 1720, 2100, 2360],
        "note_events": [
            SimpleNamespace(start_ms=100, end_ms=260, notes=[(60, 0.72), (64, 0.8), (67, 0.68)]),
            SimpleNamespace(start_ms=340, end_ms=980, notes=[(43, 0.84), (55, 0.46)]),
            SimpleNamespace(start_ms=1120, end_ms=1360, notes=[(62, 0.7), (65, 0.76), (69, 0.72)]),
            SimpleNamespace(start_ms=1640, end_ms=2380, notes=[(47, 0.78), (59, 0.48)]),
            SimpleNamespace(start_ms=2180, end_ms=2620, notes=[(72, 0.9)]),
        ],
        "bass_peaks": [360, 760, 1260, 1760, 2260],
        "guitar_onsets": [100, 500, 1120, 1620, 2180],
        "beat_ms": [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750],
        "parts": [
            SimpleNamespace(label="INTRO", start_ms=0, end_ms=500, energy=0.45),
            SimpleNamespace(label="CHORUS", start_ms=500, end_ms=2100, energy=0.92),
            SimpleNamespace(label="OUTRO", start_ms=2100, end_ms=3000, energy=0.66),
        ],
        "drum_event_streams": {
            "kick_events": [_drum_event(250, "kick", 0.9, 0.86), _drum_event(1250, "kick", 0.88, 0.82)],
            "snare_events": [_drum_event(500, "snare", 0.74, 0.78), _drum_event(1500, "snare", 0.76, 0.8)],
            "hihat_events": [_drum_event(750, "hihat", 0.46, 0.62), _drum_event(1750, "hihat", 0.48, 0.64)],
            "cymbal_events": [_drum_event(1000, "cymbal", 0.82, 0.76), _drum_event(2500, "cymbal", 0.86, 0.78)],
            "tom_events": [_drum_event(2000, "tom", 0.7, 0.7)],
            "drum_bus_events": [],
        },
        "phrase_hits": [0, 500, 1360, 2100, 2500],
        "band_sync_payload": {
            "schema": "helix.band_sync.v1",
            "performer_focus": [
                {"start_ms": 0, "end_ms": 900, "primary_focus": "singer"},
                {"start_ms": 900, "end_ms": 1600, "primary_focus": "guitarist"},
                {"start_ms": 1600, "end_ms": 2350, "primary_focus": "female_singer"},
                {"start_ms": 2350, "end_ms": 3000, "primary_focus": "drummer"},
            ],
            "energy_distributions": [
                {"start_ms": 0, "end_ms": 1500, "allocations": {"guitarist": 0.72, "bassist": 0.62}},
                {"start_ms": 1500, "end_ms": 3000, "allocations": {"guitarist": 0.52, "bassist": 0.76}},
            ],
        },
    }


def build_demo_snowman_stage_pack() -> dict[str, Any]:
    """Build a deterministic whole-stage demo payload for inspection/export tests."""
    payload = build_reactive_snowman_stage_pack(**_demo_inputs())
    payload["demo"] = {
        "schema": "helix.demo_snowman_stage_pack.v1",
        "description": "Deterministic demo proving singers, strings, drummer, and floor piano can react together.",
        "expected_members": ["bassist", "guitarist", "singer", "female_singer", "drummer"],
        "expected_stage_props": ["floor_piano"],
        "expected_integrations": ["drummer_feeds_floor_piano"],
    }
    return payload


def write_demo_snowman_stage_pack(path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    payload = build_demo_snowman_stage_pack()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"path": str(path), "pack_id": payload["pack_id"], "status": payload["status"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the deterministic demo snowman stage pack JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    result = write_demo_snowman_stage_pack(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
