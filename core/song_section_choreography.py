"""Validated source-timed section adapter for the existing nine-pass director.

This module does not infer structure from audio. It consumes an existing,
verified analysis artifact and refuses fabricated or out-of-range boundaries.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from core.choreography_intent import (
    ContrastStrategy, DominanceStrategy, MotionVocabulary,
)
from core.intent_graph import IntentGraph


def load_song_section_graph(path: str | Path, seed: IntentGraph, *, audio_path: str | Path | None = None) -> IntentGraph:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sections"), list):
        raise ValueError("source timeline requires a sections array")
    if payload.get("source") not in {"audio_analysis", "verified_manual"}:
        raise ValueError("source timeline must declare audio_analysis or verified_manual provenance")
    if audio_path is not None:
        expected = payload.get("audio_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("source timeline requires audio_sha256 when source audio is supplied")
        source_audio = Path(audio_path)
        if not source_audio.is_file():
            raise ValueError("source audio file does not exist")
        digest = hashlib.sha256()
        with source_audio.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected.lower():
            raise ValueError("source timeline audio_sha256 does not match source audio")
    duration = payload.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("source timeline requires a finite positive duration_seconds")
    if not payload["sections"]:
        raise ValueError("source timeline must contain at least one section")
    templates = tuple(seed.intents)
    if not templates:
        raise ValueError("orchestrator seed has no intent templates")
    graph = IntentGraph()
    previous_end = 0.0
    for index, section in enumerate(payload["sections"]):
        if not isinstance(section, dict):
            raise ValueError("each section must be an object")
        label = section.get("label")
        start, end = section.get("start_seconds"), section.get("end_seconds")
        energy = section.get("energy")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("section label must be nonempty")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, end, energy)):
            raise ValueError("section times and energy must be finite numbers")
        if start < 0 or end <= start or end > duration + 1e-6 or not 0 <= energy <= 1:
            raise ValueError("section bounds or energy are invalid")
        if abs(start - previous_end) > 0.025:
            raise ValueError("source sections must cover the audio continuously without gaps or overlaps")
        previous_end = end
        normalized = label.strip().lower()
        if "chorus" in normalized or "drop" in normalized:
            motion = (MotionVocabulary.BLOOM, MotionVocabulary.CHASE, MotionVocabulary.CASCADE)
            contrast = ContrastStrategy.ESCALATING_CHORUS
        elif "build" in normalized or "pre-chorus" in normalized:
            motion = (MotionVocabulary.CHASE, MotionVocabulary.SWEEP)
            contrast = ContrastStrategy.ESCALATING_CHORUS
        elif "break" in normalized or "quiet" in normalized:
            motion = (MotionVocabulary.TEXTURE, MotionVocabulary.SHIMMER)
            contrast = ContrastStrategy.SPARSE_VERSE
        else:
            motion = (MotionVocabulary.TEXTURE, MotionVocabulary.SWEEP)
            contrast = ContrastStrategy.NONE
        template = templates[index % len(templates)]
        graph.add_intent(replace(
            template,
            start=round(float(start), 6),
            duration=round(float(end - start), 6),
            section=normalized,
            emotional_energy=float(energy),
            intensity=float(energy),
            density_budget=max(0.1, min(1.0, float(energy))),
            motion_vocabulary=motion,
            contrast_strategy=contrast,
            dominance_strategy=DominanceStrategy.DISTRIBUTED,
            dominant_prop=None,
            source="verified_song_section_timeline",
            metadata={"section_index": index, "timeline_source": payload["source"], "original_label": label},
        ))
    if abs(previous_end - duration) > 0.025:
        raise ValueError("source sections must reach the end of the audio")
    return graph
