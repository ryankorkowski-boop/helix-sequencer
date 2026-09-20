from __future__ import annotations

import json
from pathlib import Path

from core.plan.build_sequence_plan import build_sequence_plan
from core.plan.sequence_plan import PLAN_SCHEMA, PLAN_VERSION, PlanCue, PlanSection, SequencePlan, SequencePlanBuilder


def test_sequence_plan_contract_round_trip(tmp_path: Path) -> None:
    plan = SequencePlan(
        source_audio="LightsOutTheme.mp3",
        fps=40,
        duration_seconds=10.0,
        style="rock",
        sections=[
            PlanSection(name="intro", kind="intro", start=0.0, end=5.0, target_intensity=0.35),
            PlanSection(name="chorus", kind="chorus", start=5.0, end=10.0, target_intensity=0.9),
        ],
        cues=[PlanCue(time=5.0, kind="section_start", confidence=0.9)],
    )

    assert plan.validate() == []
    path = plan.write_json(tmp_path / "sequence_plan.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == PLAN_SCHEMA == "helix.sequence_plan.v1"
    assert payload["version"] == PLAN_VERSION == "0.1"

    restored = SequencePlan.from_dict(payload)
    assert restored.to_dict() == plan.to_dict()


def test_sequence_plan_from_dict_defaults_missing_optional_fields() -> None:
    plan = SequencePlan.from_dict(
        {
            "source_audio": "song.wav",
            "fps": 40,
            "duration_seconds": 12.5,
            "sections": [],
            "prop_groups": [],
            "cues": [],
        }
    )

    assert plan.schema == "helix.sequence_plan.v1"
    assert plan.version == "0.1"
    assert plan.restraint.max_whole_house_hits_per_section == 4
    assert plan.scoring_targets.finale_strength_min == 0.85


def test_builder_does_not_require_renderer() -> None:
    class Event:
        def __init__(self, time_ms, confidence=0.8, strength=0.7):
            self.time_ms = time_ms
            self.confidence = confidence
            self.strength = strength
            self.metadata = {}

    class Section:
        name = "chorus_1"
        start_ms = 0
        end_ms = 10000
        strength = 0.8

    class Analysis:
        metadata = {"duration_ms": 10000, "analysis_schema": "test"}
        section_events = [Section()]
        beat_events = [Event(1000)]
        onset_events = [Event(1500)]

    plan = SequencePlanBuilder(fps=40).from_audio_analysis(
        Analysis(),
        source_audio="test.mp3",
        style="rock",
    )
    assert plan.version == "0.1"
    assert plan.schema == "helix.sequence_plan.v1"
    assert len(plan.sections) == 1
    assert len(plan.cues) == 2
    assert plan.validate() == []


def test_build_sequence_plan_without_audio_is_renderer_neutral(tmp_path: Path) -> None:
    plan = build_sequence_plan(
        audio_path=tmp_path / "missing.wav",
        layout_path=None,
        profile_id="master",
        style_version="v27.3",
        style_title="Master Sequencer",
    )

    assert plan.source_audio == "missing.wav"
    assert plan.style == "v27.3"
    assert plan.duration_seconds == 0.0
    assert plan.metadata["profile_id"] == "master"
    assert plan.metadata["style_title"] == "Master Sequencer"
