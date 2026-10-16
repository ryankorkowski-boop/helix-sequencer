from __future__ import annotations

import copy
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from tools.quality import score_sequence
from tools.quality.__main__ import score_run


FIXTURE = Path(__file__).parent / "fixtures" / "quality"


def features():
    return json.loads((FIXTURE / "audio_features.json").read_text())


@pytest.fixture
def run_dir(tmp_path):
    for name in ("benchmark.xsq", "layout.xml", "audio_features.json"):
        shutil.copyfile(FIXTURE / name, tmp_path / name)
    (tmp_path / "run_manifest.json").write_text(json.dumps({
        "status": "success", "success": True, "layout_path": "layout.xml",
        "artifacts": [{"kind": "xsq", "path": "benchmark.xsq"}],
        "preserve_me": {"nested": [1, 2, 3]},
    }))
    return tmp_path


def test_golden_benchmark_is_pure_deterministic_and_serializable():
    inputs = features()
    original = copy.deepcopy(inputs)
    before = {p: p.read_bytes() for p in FIXTURE.iterdir() if p.is_file()}
    rng_state = random.getstate()
    result = score_sequence(FIXTURE / "benchmark.xsq",
                            FIXTURE / "layout.xml", inputs)
    assert result == score_sequence(FIXTURE / "benchmark.xsq",
                                    FIXTURE / "layout.xml", inputs)
    golden = json.loads((FIXTURE / "expected_quality.json").read_text())
    assert result == golden
    assert inputs == original
    assert random.getstate() == rng_state
    assert all(p.read_bytes() == data for p, data in before.items())
    json.dumps(result, allow_nan=False)


def test_metric_arithmetic_and_partial_intentional_restraint():
    result = score_sequence(FIXTURE / "benchmark.xsq",
                            FIXTURE / "layout.xml", features())
    overall = result["overall"]
    assert overall["effect_count"] == 4
    assert overall["onset_latency"]["median_ms"] == 30
    assert overall["onset_latency"]["p95_ms"] == 390
    assert overall["energy_tracking"]["correlation"] == 1
    assert overall["energy_tracking"]["mean_lit_fraction_estimate"] == .4375
    assert overall["peak_simultaneous_effects"] == 2
    assert overall["focal_points_estimate"]["peak"] == 2
    assert overall["repetition"]["adjacent_identical"] == 1
    assert overall["dead_air"] == [
        {"start_ms": 2000, "end_ms": 2500, "intentional": False},
        {"start_ms": 3000, "end_ms": 3500, "intentional": True},
        {"start_ms": 3500, "end_ms": 4000, "intentional": False},
    ]
    assert overall["palette_consistency"] == .75
    assert result["native_render_verified"] is False
    assert [s["id"] for s in result["sections"]] == ["intro", "outro"]


def test_missing_measurements_and_no_effects_are_not_passes(run_dir):
    data = features()
    data["onsets_ms"] = [3100]
    data["energy"] = []
    root = ET.parse(run_dir / "benchmark.xsq")
    for layer in root.findall(".//EffectLayer"):
        layer.clear()
    root.write(run_dir / "benchmark.xsq")
    result = score_sequence(run_dir / "benchmark.xsq",
                            run_dir / "layout.xml", data)["overall"]
    assert result["onset_latency"]["matched_count"] == 0
    assert result["onset_latency"]["median_ms"] is None
    assert result["energy_tracking"]["correlation"] is None
    assert "unintentional_dead_air" in result["warnings"]
    assert "onset_alignment_outside_threshold" in result["warnings"]


@pytest.mark.parametrize("mutation", [
    {"duration_ms": 0}, {"duration_ms": 5000},
    {"onsets_ms": [float("nan")]}, {"onsets_ms": [4000]},
    {"energy": [{"time_ms": 0, "value": 1.1}]},
    {"energy": [{"time_ms": 0, "value": .1},
                {"time_ms": 0, "value": .2}]},
    {"sections": [{"id": "a", "start_ms": 0, "end_ms": 3000},
                  {"id": "b", "start_ms": 2000, "end_ms": 4000}]},
])
def test_invalid_features_are_rejected(mutation):
    with pytest.raises(ValueError):
        score_sequence(FIXTURE / "benchmark.xsq", FIXTURE / "layout.xml",
                       dict(features(), **mutation))


@pytest.mark.parametrize("attribute,value", [
    ("ref", "99"), ("ref", "-1"), ("palette", "99"),
    ("startTime", "-1"), ("endTime", "0"),
])
def test_invalid_xsq_is_rejected_without_manifest_damage(
    run_dir, attribute, value,
):
    tree = ET.parse(run_dir / "benchmark.xsq")
    tree.find("./ElementEffects/Element[@name='Arch']/EffectLayer/Effect").set(
        attribute, value)
    tree.write(run_dir / "benchmark.xsq")
    original = (run_dir / "run_manifest.json").read_bytes()
    with pytest.raises(ValueError):
        score_run(run_dir)
    assert (run_dir / "run_manifest.json").read_bytes() == original


def test_cyclic_groups_and_unknown_targets_fail(run_dir):
    path = run_dir / "layout.xml"
    path.write_text(path.read_text().replace('models="Arch"', 'models="All"'))
    with pytest.raises(ValueError, match="Cyclic"):
        score_run(run_dir)
    shutil.copyfile(FIXTURE / "layout.xml", path)
    xsq = run_dir / "benchmark.xsq"
    xsq.write_text(xsq.read_text().replace('name="Star"', 'name="Missing"'))
    with pytest.raises(ValueError, match="Unknown sequence target"):
        score_run(run_dir)


def test_cli_preserves_manifest_and_repeated_scoring_is_identical(run_dir):
    original = json.loads((run_dir / "run_manifest.json").read_text())
    command = [sys.executable, "-m", "tools.quality", "score", str(run_dir)]
    result = subprocess.run(command, check=True, capture_output=True,
                            text=True)
    first = (run_dir / "run_manifest.json").read_bytes()
    second = subprocess.run(command, check=True, capture_output=True,
                            text=True)
    saved = json.loads(first)
    assert {k: v for k, v in saved.items() if k != "quality"} == original
    assert saved["quality"] == json.loads(result.stdout)
    assert second.stdout == result.stdout
    assert (run_dir / "run_manifest.json").read_bytes() == first
    assert not list(run_dir.glob(".quality-*"))


def test_multiple_xsq_requires_explicit_choice(run_dir):
    path = run_dir / "run_manifest.json"
    data = json.loads(path.read_text())
    data["artifacts"].append({"kind": "xsq", "path": "second.xsq"})
    shutil.copyfile(run_dir / "benchmark.xsq", run_dir / "second.xsq")
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="exactly one"):
        score_run(run_dir)
    score_run(run_dir, xsq=run_dir / "benchmark.xsq")


def test_existing_birdsong_export_with_inline_settings_is_scored(run_dir):
    from core.birdsong_xsq_export import write_birdsong_xsq
    from tools.export_birdsong_demo_manifest import build_birdsong_demo_intents

    intents = build_birdsong_demo_intents(duration_seconds=4)
    xsq = write_birdsong_xsq(
        run_dir / "birdsong.xsq", intents, model_pool=("Arch", "Star"))
    result = score_sequence(xsq, run_dir / "layout.xml", {})
    assert result["overall"]["effect_count"] > 0
    assert "value_curves_not_evaluated" in result["warnings"]
    assert "non_on_effect_occupancy_is_an_upper_bound" in result["warnings"]


def test_fractional_short_section_samples_stay_inside_the_section(run_dir):
    data = features()
    data["sections"] = [{"id": "tiny", "start_ms": 999.9, "end_ms": 1000.1}]
    result = score_sequence(run_dir / "benchmark.xsq",
                            run_dir / "layout.xml", data)
    assert result["sections"][0]["energy_tracking"][
        "mean_lit_fraction_estimate"] == 1.0


def test_group_and_direct_effects_do_not_double_count_occupied_models(run_dir):
    tree = ET.parse(run_dir / "benchmark.xsq")
    layer = tree.find("./ElementEffects/Element[@name='All']/EffectLayer")
    layer[0].set("startTime", "1000")
    layer[0].set("endTime", "2000")
    tree.write(run_dir / "benchmark.xsq")
    result = score_run(run_dir)["overall"]
    assert result["peak_simultaneous_effects"] == 3
    assert result["energy_tracking"]["mean_lit_fraction_estimate"] == .3125
    assert result["focal_points_estimate"]["peak"] <= 2


def test_diversity_counts_families_and_warns_on_pixel_estimates(run_dir):
    tree = ET.parse(run_dir / "benchmark.xsq")
    layer = tree.find("./ElementEffects/Element[@name='Arch']/EffectLayer")
    layer[1].set("name", "Twinkle")
    tree.write(run_dir / "benchmark.xsq")
    report = score_run(run_dir)
    assert report["overall"]["diversity_by_model_class"][
        "Arches"]["entropy_bits"] == .918296
    assert "non_on_effect_occupancy_is_an_upper_bound" in report["warnings"]


def test_missing_channel_counts_warn_instead_of_inventing_channels(run_dir):
    tree = ET.parse(run_dir / "layout.xml")
    for node in tree.findall("./models/model"):
        del node.attrib["ChannelCount"]
    tree.write(run_dir / "layout.xml")
    report = score_run(run_dir)
    assert report["coverage_weighting"] == "models"
    assert report["overall"]["energy_tracking"][
        "mean_lit_fraction_estimate"] == .5
    assert "channel_counts_unavailable_using_equal_model_weights" in (
        report["warnings"])


def test_black_palette_is_dark_even_with_active_effects(run_dir):
    tree = ET.parse(run_dir / "benchmark.xsq")
    for palette in tree.findall("./ColorPalettes/ColorPalette"):
        palette.text = "C_BUTTON_Palette1=#000000,C_CHECKBOX_Palette1=1"
    tree.write(run_dir / "benchmark.xsq")
    report = score_run(run_dir)["overall"]
    assert report["effect_count"] == 0
    assert report["peak_simultaneous_effects"] == 0
    assert "unintentional_dead_air" in report["warnings"]


def test_cli_failure_is_actionable_and_keeps_manifest(run_dir):
    (run_dir / "audio_features.json").unlink()
    original = (run_dir / "run_manifest.json").read_bytes()
    result = subprocess.run(
        [sys.executable, "-m", "tools.quality", "score", str(run_dir)],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "quality score:" in result.stderr
    assert "Traceback" not in result.stderr
    assert (run_dir / "run_manifest.json").read_bytes() == original
