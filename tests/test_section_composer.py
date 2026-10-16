from __future__ import annotations

import json
import os
import random
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from core import effect_engine
from core.section_composer import Section, SectionPlan, compose_sections
from core.section_placement import (
    SectionPlacementBudget, cap_palette, expand_targets, section_palette,
)
from tools.quality import score_sequence
from tools.section_composer_benchmark import (
    prepare_benchmark, verify_native_benchmark,
)


@pytest.fixture(scope="module")
def tones():
    sr = 22050
    audio = np.concatenate([
        np.sin(2 * np.pi * f * np.arange(sr * 6) / sr) * amplitude
        for f, amplitude in ((220, .15), (330, .65), (196, .25), (440, .85))])
    return audio, sr


def test_audio_derived_sections_minimum_coverage_energy_and_stable_ids(tones):
    audio, sr = tones
    state = random.getstate()
    actual = compose_sections(audio, sr)
    assert random.getstate() == state
    assert actual == compose_sections(audio, sr)
    assert [s.start_ms for s in actual.sections] == [0, 6000, 12000, 18000]
    assert actual.sections[-1].end_ms == 24000
    assert all(s.end_ms - s.start_ms >= 4000 for s in actual.sections)
    assert len({s.id for s in actual.sections}) == 4
    assert all(a.end_ms == b.start_ms for a, b in
               zip(actual.sections, actual.sections[1:]))
    assert all(0 <= s.density_cap <= 1 for s in actual.sections)
    assert [s.marker for s in actual.sections] == [
        "steady", "build", "drop", "build"]
    assert actual.to_dict()["warnings"] == []
    for a in actual.sections:
        for b in actual.sections:
            if b.energy > a.energy:
                assert b.energy_budget > a.energy_budget


def test_silence_is_restraint_and_quiet_audio_is_not():
    silent = compose_sections(np.zeros(22050 * 5), 22050)
    assert silent.intentional_restraint == ((0, 5000),)
    assert silent.sections[0].energy_budget == 0
    assert "silent_audio" in silent.warnings
    short = compose_sections(np.ones(22050) * .01, 22050)
    assert len(short.sections) == 1
    assert not short.intentional_restraint
    assert "short_audio_single_section" in short.warnings


@pytest.mark.parametrize("audio,rate,minimum", [
    ([], 22050, 4000), ([float("nan")], 22050, 4000),
    ([.1, .2], 0, 4000), ([[.1], [.2]], 22050, 4000),
    ([.1, .2], 22050, 10),
])
def test_invalid_analysis_inputs_are_rejected(audio, rate, minimum):
    with pytest.raises(ValueError):
        compose_sections(audio, rate, minimum_ms=minimum)


def _plan():
    low = Section("low", 0, 4000, .2, .25, .25, ("#ffffff",),
                  ("base", "motion"), "steady")
    high = Section("high", 4000, 8000, .8, .85, .85, ("#00ffff",),
                   ("base", "motion", "texture"), "build")
    return SectionPlan(8000, (low, high), ((2000, 2500),),
                       ((0, .2), (4000, .8), (8000, .8)))


def test_budget_order_violation_is_visible_in_plan_and_quality(tmp_path):
    plan = _plan()
    broken = replace(plan, sections=(plan.sections[0], replace(
        plan.sections[1], energy_budget=.1)))
    assert broken.to_dict()["warnings"] == ["energy_budget_order:low:high"]
    fixture = Path("tests/fixtures/quality")
    features = json.loads((fixture / "audio_features.json").read_text())
    features["sections"][0].update(energy=.1, energy_budget=.8)
    features["sections"][1].update(energy=.9, energy_budget=.2)
    report = score_sequence(fixture / "benchmark.xsq",
                            fixture / "layout.xml", features)
    assert "section_energy_budget_not_increasing" in (
        report["overall"]["warnings"])


def test_nested_groups_and_submodels_count_root_unions_and_reject_cycles():
    targets = expand_targets({"A": "A", "A/sub": "A", "B": "B"},
                             {"dupe": ["A", "A/sub"],
                              "all": ["dupe", "B"]})
    assert targets["dupe"] == ["A"]
    assert targets["all"] == ["A", "B"]
    with pytest.raises(ValueError, match="Cyclic"):
        expand_targets({}, {"A": ["B"], "B": ["A"]})


def test_density_reserves_only_committed_placements_and_clips_boundaries():
    policy = SectionPlacementBudget(_plan(), {n: [n] for n in "ABCD"})
    first = policy.propose("A", 0, 1000, "On")
    assert first is not None
    assert policy.propose("B", 0, 1000, "On") is not None
    policy.commit(first)
    assert policy.propose("B", 0, 1000, "On") is None
    assert policy.propose("B", 1000, 1500, "On") is not None
    assert policy.propose("B", 2100, 2700, "On") is None
    before_rest = policy.propose("B", 1800, 2300, "On")
    assert before_rest is not None and before_rest.end_ms == 2000
    crossing = policy.propose("B", 3800, 4500, "On")
    assert crossing is not None and crossing.end_ms == 4000
    assert policy.propose("B", 1000, 1500, "Twinkle") is None
    assert policy.propose("B", 4500, 4800, "Twinkle") is not None


def test_performer_group_is_exempt_and_palette_caps_do_not_recolor_ac():
    targets = {"HX_SNOWMAN_DRUMMER_SNARE": ["HX_SNOWMAN_DRUMMER_SNARE"],
               "band": ["HX_SNOWMAN_DRUMMER_SNARE"], "Arch": ["Arch"]}
    policy = SectionPlacementBudget(_plan(), targets)
    assert policy.exempt("band")
    assert policy.exempt("HX_SNOWMAN_DRUMMER_SNARE")
    assert not policy.exempt("Arch")
    original = "C_BUTTON_Palette1=#ff0000,C_SLIDER_Brightness=40"
    assert "C_SLIDER_Brightness=40" in cap_palette(original, .9)
    assert "C_SLIDER_Brightness=25" in cap_palette(original, .25)
    with pytest.raises(ValueError, match="active brightness curve"):
        cap_palette("C_VALUECURVE_Brightness=Active=TRUE|Type=Sine|", .25)
    assert "C_BUTTON_Palette1=#ff0000" in section_palette(
        original, _plan().sections[0], rgb=False)


def test_section_composer_is_explicitly_opt_in():
    style = effect_engine.VARIANTS["v27.3"]
    assert effect_engine.RuntimeTuning().section_composer is False
    assert effect_engine.parse_args(style, []).section_composer is False
    args = effect_engine.parse_args(style, ["--section-composer"])
    assert args.section_composer


def test_existing_energy_wave_native_fixture_improves_without_metric_tuning(
        tmp_path):
    summary = prepare_benchmark(tmp_path / "benchmark")
    results = summary["results"]
    before, after = (results[k]["correlation"]
                     for k in ("baseline", "composed"))
    assert 0 < before < after < .5
    assert after - before > .05
    for label in ("baseline", "composed"):
        manifest = json.loads((tmp_path / "benchmark" / label
                               / "run_manifest.json").read_text())
        assert "energy_tracking_outside_threshold" in (
            manifest["quality"]["overall"]["warnings"])


def test_actual_native_section_artifact_audio_and_channel_tracking():
    raw = os.environ.get("HELIX_SECTION_COMPOSER_BENCHMARK")
    if not raw:
        pytest.skip("Set HELIX_SECTION_COMPOSER_BENCHMARK after native export")
    verify_native_benchmark(Path(raw))
