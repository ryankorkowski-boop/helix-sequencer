from core.canonical_timeline_orchestrator import (
    CanonicalTimelineOrchestrator,
    MusicalContext,
    MusicalSection,
)
from core.multi_pass_orchestration_director import MultiPassOrchestrationDirector


def test_context_preserves_variable_beat_spacing_and_section_boundaries():
    music = MusicalContext(
        duration_ms=1850,
        sections=(MusicalSection("VERSE", 0, 1000, 0.2), MusicalSection("CHORUS", 1000, 1850, 0.8)),
        beat_ms=(0, 400, 1000, 1600),
    )
    assert music.tempo_map == ((0, 150.0), (400, 100.0), (1000, 100.0))
    assert music.subdivisions_ms[4:8] == [400, 550, 700, 850]
    assert music.section_at(999).label == "VERSE"
    assert music.section_at(1000).label == "CHORUS"
    assert music.section_at(1850) is None
    graph = CanonicalTimelineOrchestrator().from_music(music)
    assert [(intent.start, intent.end) for intent in graph] == [(0, 1), (1, 1.85)]
    assert [intent.section for intent in MultiPassOrchestrationDirector().direct_music(music).final_graph] == [
        "VERSE", "CHORUS",
    ]


def test_missing_beats_and_sections_do_not_invent_cues():
    music = MusicalContext(duration_ms=900, sections=())
    assert music.section_at(0) is None
    assert music.subdivisions_ms == []
    assert not CanonicalTimelineOrchestrator().from_music(music).intents


def test_live_intent_correction_is_bounded_and_preserves_original():
    from dataclasses import replace
    from core.intent_graph import IntentGraph

    music = MusicalContext(duration_ms=2000, sections=(MusicalSection("CHORUS", 0, 2000, 1),))
    seed = CanonicalTimelineOrchestrator().from_music(music).intents[0]
    original = IntentGraph([replace(seed, density_budget=0.95)])
    corrected, report = MultiPassOrchestrationDirector()._validate_live_plan(original)
    assert report["iterations"] == 1
    assert report["correction_accepted"]
    assert corrected.intents[0].density_budget == 0.75
    assert corrected.intents[0].start == original.intents[0].start
    assert original.intents[0].density_budget == 0.95


def test_xsq_validator_checks_serialized_palette_and_timing(tmp_path):
    from core.autonomous_render_validation_engine import AutonomousRenderValidationEngine

    path = tmp_path / "export.xsq"
    xml = """<xsequence><ColorPalettes><ColorPalette/></ColorPalettes><ElementEffects>
    <Element name="Arch"><EffectLayer name="AUTO_base">
    <Effect name="On" startTime="0" endTime="70" palette="{palette}" />
    </EffectLayer></Element></ElementEffects></xsequence>"""
    validator = AutonomousRenderValidationEngine()
    path.write_text(xml.format(palette=0), encoding="utf-8")
    assert validator.validate_export(path, "AUTO", 100)["passed"]
    path.write_text(xml.format(palette=2), encoding="utf-8")
    assert not validator.validate_export(path, "AUTO", 100)["passed"]
    assert not validator.validate_export(path, "AUTO", 50)["passed"]
