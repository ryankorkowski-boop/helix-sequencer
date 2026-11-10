from core.plan.sequence_plan import (
    PlanCue,
    PlanSection,
    SequencePlan,
    SequencePlanBuilder,
)


def test_sequence_plan_contract_round_trip(tmp_path):
    plan = SequencePlan(
        source_audio="LightsOutTheme.mp3",
        fps=40,
        duration_seconds=10.0,
        style="rock",
        sections=[
            PlanSection(
                name="intro",
                kind="intro",
                start=0.0,
                end=5.0,
                target_intensity=0.35,
            ),
            PlanSection(
                name="chorus",
                kind="chorus",
                start=5.0,
                end=10.0,
                target_intensity=0.9,
            ),
        ],
        cues=[PlanCue(time=5.0, kind="section_start", confidence=0.9)],
    )
    assert plan.validate() == []
    path = plan.write_json(tmp_path / "sequence_plan.json")
    restored = SequencePlan.from_dict(__import__("json").loads(path.read_text()))
    assert restored.to_dict() == plan.to_dict()


def test_builder_does_not_require_renderer():
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
    assert plan.version == "0.2"
    assert len(plan.sections) == 1
    assert len(plan.cues) == 2
    assert plan.validate() == []
