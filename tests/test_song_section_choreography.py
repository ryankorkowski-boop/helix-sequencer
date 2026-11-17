from __future__ import annotations

import json

import pytest

from core.effects_orchestrator_bridge import build_seed_graph, run_effects_orchestration
from core.sequence_builder import _clean_engine_args
from core.song_section_choreography import load_song_section_graph


def _write(tmp_path, sections, *, duration=42.0, source="audio_analysis"):
    path = tmp_path / "sections.json"
    path.write_text(json.dumps({
        "source": source, "duration_seconds": duration, "sections": sections,
    }), encoding="utf-8")
    return path


def test_real_timed_sections_replace_fixed_seed(tmp_path):
    path = _write(tmp_path, [
        {"label": "Intro", "start_seconds": 0, "end_seconds": 7, "energy": 0.2},
        {"label": "Build", "start_seconds": 7, "end_seconds": 17, "energy": 0.55},
        {"label": "Chorus", "start_seconds": 17, "end_seconds": 42, "energy": 0.95},
    ])
    graph = load_song_section_graph(path, build_seed_graph())
    assert graph.ordered_sections() == ("intro", "build", "chorus")
    assert len(graph.intents) == 3
    assert [(i.start, i.end) for i in graph] == [(0.0, 7.0), (7.0, 17.0), (17.0, 42.0)]
    assert all(i.source == "verified_song_section_timeline" for i in graph)
    assert graph.intents[2].intensity == 0.95


@pytest.mark.parametrize("sections", [
    [],
    [{"label": "Intro", "start_seconds": 1, "end_seconds": 42, "energy": 0.4}],
    [{"label": "Intro", "start_seconds": 0, "end_seconds": 40, "energy": 0.4}],
    [{"label": "Intro", "start_seconds": 0, "end_seconds": 43, "energy": 0.4}],
    [{"label": "Intro", "start_seconds": 0, "end_seconds": 42, "energy": 1.5}],
    [
        {"label": "Intro", "start_seconds": 0, "end_seconds": 20, "energy": 0.2},
        {"label": "Chorus", "start_seconds": 19, "end_seconds": 42, "energy": 0.8},
    ],
])
def test_invalid_sections_fail_closed(tmp_path, sections):
    path = _write(tmp_path, sections)
    with pytest.raises(ValueError):
        load_song_section_graph(path, build_seed_graph())


def test_unverified_source_rejected(tmp_path):
    path = _write(tmp_path, [{"label": "verse", "start_seconds": 0, "end_seconds": 42, "energy": 0.5}], source="synthetic")
    with pytest.raises(ValueError, match="provenance"):
        load_song_section_graph(path, build_seed_graph())


def test_nine_pass_bridge_uses_source_sections(tmp_path):
    path = _write(tmp_path, [
        {"label": "Intro", "start_seconds": 0, "end_seconds": 7, "energy": 0.2},
        {"label": "Chorus", "start_seconds": 7, "end_seconds": 42, "energy": 0.8},
    ])
    report = run_effects_orchestration([
        "--audio", "song.wav", "--orchestration-sections-json", str(path),
    ], write_report=False)
    assert report.invoked is True, report.error
    assert report.input_intents == 2
    assert len(report.passes) == 9


def test_source_flag_is_not_forwarded_to_effect_engine():
    args = ["--audio", "song.wav", "--orchestration-sections-json", "sections.json", "--polish"]
    assert _clean_engine_args(args) == ["--audio", "song.wav", "--polish"]
