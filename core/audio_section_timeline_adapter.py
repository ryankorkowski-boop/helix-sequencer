"""Convert Helix audio_analysis.json to the strict orchestration section schema.

Reject the current energy-curve thirds fallback: its labels are heuristics,
not verified musical structure, and should not silently drive production.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def timeline_from_audio_analysis(analysis_path: str | Path, audio_path: str | Path) -> dict:
    """Adapt verified section events for the nine-pass director.

    Requires a caller-supplied audio file and rejects low-confidence or
    fallback section guesses. This does not claim to independently recognize
    musical form.
    """
    payload = json.loads(Path(analysis_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("audio analysis must be a JSON object")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("analysis_schema") != "helix.audio_analysis.v1":
        raise ValueError("unrecognized audio analysis schema")
    duration_ms = metadata.get("duration_ms")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)) or not math.isfinite(duration_ms) or duration_ms <= 0:
        raise ValueError("audio analysis must provide positive duration_ms")
    source = Path(audio_path)
    if not source.is_file():
        raise ValueError("matching source audio is required")
    # A path name alone is not proof of source identity. If the analysis
    # provides a hash, it must match. Otherwise require explicit review.
    expected_hash = metadata.get("audio_sha256")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ValueError("analysis lacks source audio SHA-256; regenerate or verify provenance")
    actual_hash = _sha256(source)
    if actual_hash.lower() != expected_hash.lower():
        raise ValueError("analysis audio SHA-256 does not match source audio")
    events = payload.get("section_events")
    if not isinstance(events, list) or not events:
        raise ValueError("audio analysis contains no section events")
    sections = []
    previous_end = 0
    for item in events:
        if not isinstance(item, dict):
            raise ValueError("invalid section event")
        start, end = item.get("start_ms"), item.get("end_ms")
        strength, confidence = item.get("strength"), item.get("confidence")
        label, reason = item.get("section_type"), item.get("reason")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, end, strength, confidence)):
            raise ValueError("invalid section values")
        if not isinstance(label, str) or not label.strip() or not isinstance(reason, str):
            raise ValueError("section requires label and provenance")
        if "fallback" in reason or reason == "tail_fill" or confidence < 0.7:
            raise ValueError("fallback or low-confidence sections require review, not automatic promotion")
        if start != previous_end or end <= start or end > duration_ms or not 0 <= strength <= 1 or not 0 <= confidence <= 1:
            raise ValueError("sections must cover audio continuously and have valid bounds")
        sections.append({
            "label": label,
            "start_seconds": start / 1000,
            "end_seconds": end / 1000,
            "energy": strength,
        })
        previous_end = end
    if abs(previous_end - duration_ms) > 25:
        raise ValueError("sections do not cover complete audio duration")
    return {
        "source": "audio_analysis",
        "duration_seconds": duration_ms / 1000,
        "audio_sha256": actual_hash,
        "sections": sections,
    }


def write_timeline_from_audio_analysis(analysis_path: str | Path, audio_path: str | Path, destination: str | Path) -> Path:
    payload = timeline_from_audio_analysis(analysis_path, audio_path)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
