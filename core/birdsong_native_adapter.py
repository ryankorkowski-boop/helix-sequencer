"""Pre-export Birdsong adapter for authenticated source-audio features.

Invoke from the native XSQ effect-placement stage, not after export.
This module deliberately does not synthesize features or claim rendered proof.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Mapping, Sequence

from core.birdsong_issue2_runtime import (
    BirdsongRuntimeConfig, emit_birdsong_rows, plan_birdsong_runtime,
)
from core.feature_state import build_feature_state_sequence


def place_source_birdsong(
    audio_path: Path,
    features: Mapping[str, object],
    *,
    source_audio_sha256: str,
    features_audio_sha256: str,
    fps: float,
    models: Sequence[str],
    add_model: Callable,
) -> dict[str, object]:
    """Place real-audio Birdsong rows through a native engine callback.

    The caller must provide the SHA of the audio used for feature extraction.
    A successful callback is not by itself proof of serialized XSQ/FSEQ output;
    downstream artifact inspection is still mandatory.
    """
    if not audio_path.is_file():
        raise ValueError("Birdsong source audio is missing")
    actual = hashlib.sha256(audio_path.read_bytes()).hexdigest()
    if actual != source_audio_sha256 or actual != features_audio_sha256:
        raise ValueError("Birdsong features do not match verified source audio")
    if not 1 <= fps <= 240:
        raise ValueError("Birdsong feature fps out of range")
    if "energy" not in features or "centroid" not in features:
        raise ValueError("Birdsong source features missing energy or centroid")
    if not models:
        raise ValueError("Birdsong has no native target models")
    frames = build_feature_state_sequence(features, fps=fps)
    if not frames:
        raise ValueError("Birdsong source features produced no frames")
    plan = plan_birdsong_runtime(
        frames, models, config=BirdsongRuntimeConfig(enabled=True),
    )
    if not plan.rows:
        raise ValueError("Birdsong generated no native placement rows")
    placed = emit_birdsong_rows(plan.rows, add_model, strict=True)
    if placed != len(plan.rows):
        raise RuntimeError("Birdsong native callback did not confirm every row")
    return {
        "audio_sha256": actual,
        "features_source": "source_audio",
        "planned_rows": len(plan.rows),
        "callback_confirmed_rows": placed,
        "native_artifact_verified": False,
    }
