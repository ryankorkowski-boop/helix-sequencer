from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from core.birdsong_behavior_planner import EffectIntent


SCHEMA = "helix.birdsong.intent_manifest.v1"


def intent_to_record(intent: EffectIntent) -> dict[str, object]:
    return {
        "effect_name": intent.effect_name,
        "motif": intent.motif,
        "direction": intent.direction,
        "start_time": round(intent.start_time, 6),
        "end_time": intent.end_time,
        "duration": round(intent.duration, 6),
        "strength": round(intent.strength, 6),
        "score": round(intent.score, 6),
        "score_detail": {
            "energy_match": round(intent.score_detail.energy_match, 6),
            "spatial_fit": round(intent.score_detail.spatial_fit, 6),
            "novelty": round(intent.score_detail.novelty, 6),
            "continuity": round(intent.score_detail.continuity, 6),
        },
    }


def build_intent_manifest(intents: Iterable[EffectIntent], *, title: str = "BirdsongIntentDemo") -> dict[str, object]:
    records = [intent_to_record(intent) for intent in intents]
    records.sort(key=lambda item: (item["start_time"], item["effect_name"], item["score"]))
    return {
        "schema": SCHEMA,
        "title": title,
        "intent_count": len(records),
        "intents": records,
    }


def write_intent_manifest(path: Path, intents: Iterable[EffectIntent], *, title: str = "BirdsongIntentDemo") -> Path:
    manifest = build_intent_manifest(intents, title=title)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
