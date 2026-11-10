from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from core.helix_flow_spatial_graph import build_spatial_graph


HELIXVILLE3_MANIFEST = Path("helixville3/helixville3_manifest.json")
DEFAULT_LAYOUT = Path("xlights_rgbeffects.xml")

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
    ordered_path: tuple[str, ...] = ()
    spread_path: tuple[str, ...] = ()


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


def _ordered_path(intent: Mapping[str, object], model_pool: tuple[str, ...]) -> tuple[str, ...]:
    direction = str(intent.get("direction", ""))
    graph = build_spatial_graph(layout_path=DEFAULT_LAYOUT, model_names=model_pool)
    return tuple(node.name for node in graph.ordered_for_direction(direction)) or model_pool


def choose_target_model(intent: Mapping[str, object], model_pool: tuple[str, ...]) -> str:
    if not model_pool:
        raise ValueError("model_pool must not be empty")
    ordered = _ordered_path(intent, model_pool)
    start_time = float(intent.get("start_time", 0.0) or 0.0)
    index = int(round(start_time * 1000.0)) % len(ordered)
    return ordered[index]


def build_spread_path(intent: Mapping[str, object], model_pool: tuple[str, ...], *, max_models: int = 4) -> tuple[str, ...]:
    if not model_pool:
        raise ValueError("model_pool must not be empty")
    if max_models <= 0:
        raise ValueError("max_models must be > 0")
    ordered = _ordered_path(intent, model_pool)
    start = choose_target_model(intent, model_pool)
    start_index = ordered.index(start)
    path = []
    for offset in range(min(max_models, len(ordered))):
        path.append(ordered[(start_index + offset) % len(ordered)])
    return tuple(path)


def build_target_plan(intent: Mapping[str, object], model_pool: tuple[str, ...] | None = None) -> BirdsongTargetPlan:
    pool = model_pool or load_helixville3_target_pool()
    ordered = _ordered_path(intent, pool)
    spread = build_spread_path(intent, pool)
    return BirdsongTargetPlan(
        model_name=spread[0],
        model_pool=pool,
        ordered_path=ordered,
        spread_path=spread,
    )
