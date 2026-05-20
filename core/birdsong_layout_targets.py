from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


HELIXVILLE3_MANIFEST = Path("helixville3/helixville3_manifest.json")

FALLBACK_TARGETS: tuple[str, ...] = (
    "NBH_RIGHT_SINGING_FACE_01_PANEL",
    "NBH_RIGHT_SINGING_FACE_02_PANEL",
    "NBH_RIGHT_SINGING_FACE_03_PANEL",
    "HV3_IMPORT_Matrix",
    "NBH_LEFT_MATRIX_01",
)


@dataclass(frozen=True)
class BirdsongTargetPlan:
    model_name: str
    model_pool: tuple[str, ...]


def load_helixville3_target_pool(manifest_path: Path = HELIXVILLE3_MANIFEST) -> tuple[str, ...]:
    if not manifest_path.exists():
        return FALLBACK_TARGETS
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    models: list[str] = []
    for key in ("singing_face_models", "lyric_marquee_models"):
        raw = data.get(key, [])
        if isinstance(raw, list):
            models.extend(str(item) for item in raw if item)
    unique = tuple(dict.fromkeys(models))
    return unique or FALLBACK_TARGETS


def choose_target_model(intent: Mapping[str, object], model_pool: tuple[str, ...]) -> str:
    if not model_pool:
        raise ValueError("model_pool must not be empty")
    motif = str(intent.get("motif", ""))
    direction = str(intent.get("direction", ""))
    effect_name = str(intent.get("effect_name", ""))
    start_time = float(intent.get("start_time", 0.0) or 0.0)
    seed = sum(ord(ch) for ch in f"{motif}:{direction}:{effect_name}") + int(round(start_time * 1000.0))
    return model_pool[seed % len(model_pool)]


def build_target_plan(intent: Mapping[str, object], model_pool: tuple[str, ...] | None = None) -> BirdsongTargetPlan:
    pool = model_pool or load_helixville3_target_pool()
    return BirdsongTargetPlan(model_name=choose_target_model(intent, pool), model_pool=pool)
