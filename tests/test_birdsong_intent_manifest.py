from __future__ import annotations

import json
from pathlib import Path

from core.birdsong_behavior_planner import plan_effect_intent
from core.birdsong_feature_state import FeatureState
from core.birdsong_intent_manifest import SCHEMA, build_intent_manifest, write_intent_manifest
from core.birdsong_phrase_engine import Phrase


def _state(energy: float = 0.8) -> FeatureState:
    state = FeatureState(smoothing_alpha=1.0)
    state.update({"energy": energy, "onset": 0.7, "bands": (0.2, 0.6, 0.2)})
    return state


def _phrase(start: float = 0.0) -> Phrase:
    return Phrase(start_time=start, duration=4.0, motif="wave_sweep", direction="left_to_right", energy_anchor=0.8)


def _intent(time: float):
    intent = plan_effect_intent(state=_state(), phrase=_phrase(time), time=time)
    assert intent is not None
    return intent


def test_build_intent_manifest_has_schema_and_count() -> None:
    manifest = build_intent_manifest([_intent(1.0), _intent(0.0)], title="Demo")

    assert manifest["schema"] == SCHEMA
    assert manifest["title"] == "Demo"
    assert manifest["intent_count"] == 2
    assert len(manifest["intents"]) == 2


def test_build_intent_manifest_sorts_deterministically() -> None:
    first = build_intent_manifest([_intent(2.0), _intent(0.5), _intent(1.0)])
    second = build_intent_manifest([_intent(1.0), _intent(2.0), _intent(0.5)])

    assert first == second
    assert [item["start_time"] for item in first["intents"]] == [0.5, 1.0, 2.0]


def test_intent_manifest_contains_score_detail() -> None:
    manifest = build_intent_manifest([_intent(0.0)])
    record = manifest["intents"][0]

    assert record["effect_name"]
    assert record["motif"] == "wave_sweep"
    assert record["direction"] == "left_to_right"
    assert record["end_time"] == round(record["start_time"] + record["duration"], 6)
    assert 0.0 <= record["strength"] <= 1.0
    assert 0.0 <= record["score"] <= 1.0
    assert set(record["score_detail"]) == {"energy_match", "spatial_fit", "novelty", "continuity"}


def test_write_intent_manifest_outputs_json(tmp_path: Path) -> None:
    output = write_intent_manifest(tmp_path / "birdsong_intents.json", [_intent(0.0)], title="Written")

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA
    assert data["title"] == "Written"
    assert data["intent_count"] == 1
