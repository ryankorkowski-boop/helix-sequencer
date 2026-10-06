from __future__ import annotations

import json
import shutil
import wave
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tools.drummer_ground_truth_oracle import TARGETS as LOGICAL_TARGETS, fixture_events
from tools.export_drummer_ground_truth_xsq import export_drummer_ground_truth_xsq
from tools.generate_drummer_ground_truth import generate
from tools.render_drummer_v3_preview import TARGETS, compose_lighting, load_component_masks

ROOT = Path(__file__).resolve().parents[1]
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
SOURCE = ROOT / "fixtures/band_geometry/source/drummerbg.png"


def _expand(text: str) -> set[int]:
    out: set[int] = set()
    for token in text.split(","):
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(token))
    return out


def _submodels(path: Path = XMODEL) -> dict[str, set[int]]:
    root = ET.parse(path).getroot()
    return {
        sm.get("name", ""): _expand(sm.get("line0", ""))
        for sm in root.findall("./subModels/subModel")
    }


def test_exact_eight_public_targets_exist_and_are_nonempty() -> None:
    submodels = _submodels()
    assert len(TARGETS) == 8
    assert set(TARGETS) == {f"HX_SNOWMAN_DRUMMER_V3_{name}" for name in LOGICAL_TARGETS}
    for target in TARGETS:
        assert submodels[target]


def test_each_public_target_contains_its_surface_but_no_other_instrument_surface() -> None:
    submodels = _submodels()
    for target in TARGETS:
        suffix = target.removeprefix("HX_SNOWMAN_DRUMMER_V3_")
        surface = submodels[f"{target}_SURFACE"]
        assert surface <= submodels[target]
        for other in TARGETS:
            if other == target:
                continue
            assert not (submodels[target] & submodels[f"{other}_SURFACE"]), (target, other)


def test_hi_hat_uses_foot_and_no_arm_while_kick_has_no_actuator() -> None:
    submodels = _submodels()
    hat = submodels["HX_SNOWMAN_DRUMMER_V3_HI_HAT"]
    kick = submodels["HX_SNOWMAN_DRUMMER_V3_KICK"]
    foot = submodels["HX_SNOWMAN_DRUMMER_V3_HI_HAT_FOOT"]
    left = submodels["HX_SNOWMAN_DRUMMER_V3_LEFT_ARM_STICK"]
    right = submodels["HX_SNOWMAN_DRUMMER_V3_RIGHT_ARM_STICK"]
    assert hat & foot
    assert not (hat & left)
    assert not (hat & right)
    assert not (kick & foot)
    assert not (kick & left)
    assert not (kick & right)


def test_inactive_pixels_are_identical_to_idle_and_active_pixels_preserve_source_color() -> None:
    source, masks = load_component_masks()
    idle = compose_lighting(source, masks, [])
    target = TARGETS[1]
    active = compose_lighting(source, masks, [target])
    mask = np.asarray(masks[target]) > 0
    idle_arr = np.asarray(idle)
    active_arr = np.asarray(active)
    source_arr = np.asarray(source)
    assert np.array_equal(active_arr[~mask], idle_arr[~mask])
    assert np.array_equal(active_arr[mask], source_arr[mask])


def test_simultaneous_hits_use_max_union_so_shared_arm_does_not_compound() -> None:
    source, masks = load_component_masks()
    snare = TARGETS[1]
    mid = TARGETS[4]
    one = np.asarray(compose_lighting(source, masks, [snare]))
    combo = np.asarray(compose_lighting(source, masks, [snare, mid]))
    shared = (np.asarray(masks[snare]) > 0) & (np.asarray(masks[mid]) > 0)
    assert shared.any()
    assert np.array_equal(one[shared], combo[shared])


def test_xmodel_node_mutation_changes_renderer_mask(tmp_path: Path) -> None:
    mutated = tmp_path / "mutated.xmodel"
    shutil.copyfile(XMODEL, mutated)
    tree = ET.parse(mutated)
    root = tree.getroot()
    kick = next(sm for sm in root.findall("./subModels/subModel") if sm.get("name") == TARGETS[0])
    kick.set("line0", "1")
    tree.write(mutated, encoding="UTF-8", xml_declaration=True)
    _, original = load_component_masks()
    _, changed = load_component_masks(xmodel_path=mutated)
    assert original[TARGETS[0]].tobytes() != changed[TARGETS[0]].tobytes()


def test_renderer_rejects_empty_public_target_nodes(tmp_path: Path) -> None:
    mutated = tmp_path / "empty.xmodel"
    shutil.copyfile(XMODEL, mutated)
    tree = ET.parse(mutated)
    root = tree.getroot()
    kick = next(sm for sm in root.findall("./subModels/subModel") if sm.get("name") == TARGETS[0])
    kick.set("line0", "")
    tree.write(mutated, encoding="UTF-8", xml_declaration=True)
    with pytest.raises(ValueError, match="no nodes"):
        load_component_masks(xmodel_path=mutated)


def test_fixture_has_isolated_eight_then_combinations_and_68_events() -> None:
    events = fixture_events(20.0)
    assert len(events) == 68
    assert [event.target for event in events[:8]] == list(LOGICAL_TARGETS)
    assert [round(event.time, 3) for event in events[:8]] == [0.25, 1.25, 2.25, 3.25, 4.25, 5.25, 6.25, 7.25]
    assert any(event.time == 11.0 and event.target == "TOM_HIGH" for event in events)
    assert any(event.time == 11.25 and event.target == "TOM_FLOOR" for event in events)


def test_wav_manifest_and_xsq_share_exact_event_oracle_and_duration(tmp_path: Path) -> None:
    wav = tmp_path / "truth.wav"
    manifest_path = tmp_path / "events.json"
    xsq = tmp_path / "truth.xsq"
    generate(wav, manifest_path, 20.0)
    export_drummer_ground_truth_xsq(xsq, 20.0)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = ET.parse(xsq).getroot()
    timing = [
        {
            "time": round(float(node.get("start", "0")), 4),
            "duration": round(float(node.get("duration", "0")), 4),
            "event": node.get("channel"),
        }
        for node in root.findall("./timingtrack/phoneme")
    ]
    assert timing == manifest
    with wave.open(str(wav), "rb") as handle:
        assert handle.getnframes() / handle.getframerate() == pytest.approx(20.0, abs=1 / 44100)
    assert float(root.get("duration", "0")) == pytest.approx(20.0)
