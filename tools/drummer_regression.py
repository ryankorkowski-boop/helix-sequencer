"""Deterministic Drummer V3 regression harness.

This intentionally tests the detector/classifier, reactive drummer logic, motion
bridge, and authored preview renderer without depending on a microphone or an
uncontrolled audio model. The synthetic WAV is a reproducible fixture; the
feature vectors model the detector output that the classifier consumes.
"""

from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

from audio.drum_classification import DrumEvent, classify_drum_hit
from helix.preview.drummer_v3 import build_render_event, validate_asset_contract
from helix.preview.pillow_renderer import PillowRenderer
from models.working_drummer import build_reactive_drummer_member


SAMPLE_RATE = 16_000
DURATION_MS = 2_000
EXPECTED = [
    (150, "kick"),
    (350, "hihat"),
    (550, "snare"),
    (750, "hihat"),
    (950, "kick"),
    (950, "hihat"),
    (1_150, "tom"),
    (1_350, "tom"),
    (1_550, "cymbal"),
    (1_750, "kick"),
    (1_750, "snare"),
]

FEATURES = {
    "kick": {"low_ratio": 0.86, "mid_low_ratio": 0.12, "mid_ratio": 0.10, "high_ratio": 0.08, "centroid_hz": 500, "spectral_spread01": 0.18, "transient_sharpness": 0.72, "decay_profile": 0.20},
    "hihat": {"low_ratio": 0.04, "mid_low_ratio": 0.08, "mid_ratio": 0.10, "high_ratio": 0.82, "centroid_hz": 6500, "spectral_spread01": 0.55, "transient_sharpness": 0.72, "decay_profile": 0.18},
    "snare": {"low_ratio": 0.10, "mid_low_ratio": 0.18, "mid_ratio": 0.62, "high_ratio": 0.30, "centroid_hz": 1800, "spectral_spread01": 0.62, "transient_sharpness": 0.68, "decay_profile": 0.28},
    "tom": {"low_ratio": 0.16, "mid_low_ratio": 0.72, "mid_ratio": 0.38, "high_ratio": 0.20, "centroid_hz": 900, "spectral_spread01": 0.30, "transient_sharpness": 0.55, "decay_profile": 0.48},
    "cymbal": {"low_ratio": 0.05, "mid_low_ratio": 0.12, "mid_ratio": 0.20, "high_ratio": 0.72, "centroid_hz": 5200, "spectral_spread01": 0.76, "transient_sharpness": 0.42, "decay_profile": 0.82},
}


def write_synthetic_wav(path: Path) -> None:
    """Write a tiny, deterministic drum-like impulse fixture."""
    frames = bytearray()
    for sample_index in range(SAMPLE_RATE * DURATION_MS // 1000):
        ms = sample_index * 1000 / SAMPLE_RATE
        value = 0.0
        for hit_ms, drum_type in EXPECTED:
            age = ms - hit_ms
            if 0 <= age < 90:
                freq = {"kick": 90, "hihat": 7_000, "snare": 1_900, "tom": 150, "cymbal": 4_800}[drum_type]
                decay = math.exp(-age / {"kick": 35, "hihat": 12, "snare": 24, "tom": 45, "cymbal": 180}[drum_type])
                value += 0.24 * decay * math.sin(2 * math.pi * freq * age / 1000)
        value = max(-1.0, min(1.0, value))
        frames += int(value * 32767).to_bytes(2, "little", signed=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(frames)


def run(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "synthetic_2s.wav"
    write_synthetic_wav(wav_path)

    classifications: list[dict[str, object]] = []
    events: list[DrumEvent] = []
    mismatches: list[dict[str, object]] = []
    for index, (timestamp_ms, expected) in enumerate(EXPECTED):
        actual, confidence = classify_drum_hit(FEATURES[expected])
        classifications.append({"timestamp_ms": timestamp_ms, "expected": expected, "actual": actual, "confidence": confidence})
        if actual != expected:
            mismatches.append(classifications[-1])
        events.append(DrumEvent(timestamp_ms / 1000.0, 0.8, confidence, FEATURES[expected], index, actual, "synthetic_regression"))

    typed = {key: [] for key in ("kick_events", "snare_events", "tom_events", "hihat_events", "cymbal_events", "drum_bus_events")}
    for event in events:
        typed[{"kick": "kick_events", "snare": "snare_events", "hihat": "hihat_events", "tom": "tom_events", "cymbal": "cymbal_events"}.get(event.drum_type, "drum_bus_events")].append(event)

    payload = build_reactive_drummer_member(drum_event_streams=typed)
    reactive_path = output_dir / "reactive_drummer.json"
    reactive_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    contract_missing = validate_asset_contract(Path.cwd())
    render_events = [
        build_render_event(timestamp_ms=event.timestamp_ms, drum_type=event.drum_type, velocity=event.velocity, index=index)
        for index, event in enumerate(events)
    ]

    renderer = PillowRenderer(width=640, height=480)
    render_error = None
    try:
        # Prefer the dedicated preview backdrop when present; the authored source
        # image is a safe deterministic fallback for CI branches that don't carry
        # the generated preview backdrop yet.
        from helix.preview.drummer_v3 import DRUMMER_V3_BACKDROP, DRUMMER_V3_SOURCE
        backdrop = Path.cwd() / DRUMMER_V3_BACKDROP
        if not backdrop.is_file():
            import helix.preview.drummer_v3 as drummer_v3
            drummer_v3.DRUMMER_V3_BACKDROP = DRUMMER_V3_SOURCE
        import imageio.v2 as imageio
        mp4_path = output_dir / "drummer_debug.mp4"
        with imageio.get_writer(mp4_path, fps=24, codec="libx264", quality=7) as writer:
            for frame_index in range(48):
                timestamp_ms = int(round(frame_index * 1000 / 24))
                frame = renderer.render_drummer_v3(Path.cwd(), render_events, timestamp_ms)
                writer.append_data(__import__("numpy").asarray(frame.convert("RGB")))
    except Exception as exc:  # pragma: no cover - surfaced in the report
        render_error = f"{type(exc).__name__}: {exc}"

    report = {
        "duration_ms": DURATION_MS,
        "expected_events": [{"timestamp_ms": ms, "drum_type": kind} for ms, kind in EXPECTED],
        "classifications": classifications,
        "classification_pass": not mismatches,
        "mismatches": mismatches,
        "reactive_cue_count": len(payload["reactive_cues"]),
        "reactive_targets": sorted({cue["submodel"] for cue in payload["reactive_cues"]}),
        "v3_pose_targets": sorted({cue["pose"] for cue in payload["reactive_cues"]}),
        "asset_contract_missing": contract_missing,
        "render_error": render_error,
        "render_pass": render_error is None,
        "wav": str(wav_path),
    }
    (output_dir / "detection_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["classification_pass"] or not report["render_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
