from __future__ import annotations

import json
import shutil
import wave
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
from PIL import ImageFilter

from tools.drummer_ground_truth_oracle import TARGETS as LOGICAL_TARGETS, fixture_events
from tools.export_drummer_ground_truth_xsq import export_drummer_ground_truth_xsq
from tools.generate_drummer_ground_truth import generate
from tools.render_drummer_v3_preview import TARGETS, compose_lighting, load_component_masks\nfrom tools.drummer_v3_visual_masks import target_surface_key

ROOT = Path(__file__).resolve().parents[1]
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"


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
    return {sm.get("name", ""): _expand(sm.get("line0", "")) for sm in root.findall("./subModels/subModel")}


def test_exact_eight_public_targets_exist_and_are_nonempty() -> None:
    submodels = _submodels()
    assert len(TARGETS) == 8
    assert set(TARGETS) == {f"HX_SNOWMAN_DRUMMER_V3_{name}" for name in LOGICAL_TARGETS}
    for target in TARGETS:
        assert submodels[target]


def test_each_public_target_is_spatially_isolated_from_other_instrument_surfaces() -> None:
    submodels = _submodels()
    all_surfaces = {target: submodels[f"{target}_SURFACE"] for target in TARGETS}
    union_of_surfaces = set().union(*all_surfaces.values())
    for target in TARGETS:
        surface = all_surfaces[target]
        public = submodels[target]
        assert surface <= public
        for other, other_surface in all_surfaces.items():
            if other != target:
                assert not (public & other_surface), (target, other)
        actuator_contribution = public - surface
        assert not (actuator_contribution & union_of_surfaces), target


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


def test_background_remains_dimly_visible_and_active_component_has_local_outline() -> None:
    source, masks = load_component_masks()
    idle = compose_lighting(source, masks, [])
    target = TARGETS[1]
    active = compose_lighting(source, masks, [target])
    mask_image = masks[target]
    mask = np.asarray(mask_image) > 0
    dilated = np.asarray(mask_image.filter(ImageFilter.MaxFilter(11))) > 0
    ring = dilated & ~mask
    far = ~(np.asarray(mask_image.filter(ImageFilter.MaxFilter(41))) > 0)

    idle_arr = np.asarray(idle)[..., :3].astype(float)
    active_arr = np.asarray(active)[..., :3].astype(float)
    source_arr = np.asarray(source)[..., :3].astype(float)

    assert masks[target].size == source.size
    assert idle_arr.mean() > source_arr.mean() * 0.36
    assert idle_arr.mean() < source_arr.mean() * 0.56
    assert active_arr[mask].mean() > idle_arr[mask].mean() * 2.0
    assert (active_arr[ring] - idle_arr[ring]).mean() > 8.0
    assert np.abs(active_arr[far] - idle_arr[far]).max() <= 2.0


def _surface_edge(mask_image):
    radius = 2
    kernel = radius * 2 + 1
    dilated = np.asarray(mask_image.filter(ImageFilter.MaxFilter(kernel))) > 0
    eroded = np.asarray(mask_image.filter(ImageFilter.MinFilter(kernel))) > 0
    surface = np.asarray(mask_image) > 0
    return (dilated & ~surface) | (surface & ~eroded)


def test_kick_outline_is_red_and_tom_outlines_are_green() -> None:
    source, masks = load_component_masks()

    kick = TARGETS[0]
    kick_frame = np.asarray(compose_lighting(source, masks, [kick]))[..., :3].astype(float)
    kick_edge = _surface_edge(masks[target_surface_key(kick)])
    kick_rgb = kick_frame[kick_edge].mean(axis=0)
    assert kick_rgb[0] > kick_rgb[1] * 1.45
    assert kick_rgb[0] > kick_rgb[2] * 1.35

    for tom in TARGETS[3:6]:
        frame = np.asarray(compose_lighting(source, masks, [tom]))[..., :3].astype(float)
        edge = _surface_edge(masks[target_surface_key(tom)])
        rgb = frame[edge].mean(axis=0)
        assert rgb[1] > rgb[0] * 1.35, (tom, rgb)
        assert rgb[1] > rgb[2] * 1.15, (tom, rgb)


def test_actuator_is_brightened_but_not_wrapped_in_instrument_color() -> None:
    source, masks = load_component_masks()
    snare = TARGETS[1]
    target_mask = np.asarray(masks[snare]) > 0
    surface_mask = np.asarray(masks[target_surface_key(snare)]) > 0
    actuator_only = target_mask & ~surface_mask
    idle = np.asarray(compose_lighting(source, masks, []))[..., :3].astype(float)
    active = np.asarray(compose_lighting(source, masks, [snare]))[..., :3].astype(float)
    assert actuator_only.any()
    assert active[actuator_only].mean() > idle[actuator_only].mean() * 1.8
    # It should remain source-colored instead of becoming a flat magenta trace.
    actuator_rgb = active[actuator_only].mean(axis=0)
    assert max(actuator_rgb) - min(actuator_rgb) < 95.0


def test_simultaneous_hits_use_one_union_pass_so_shared_actuators_do_not_compound() -> None:
    source, masks = load_component_masks()
    snare = TARGETS[1]
    mid = TARGETS[4]
    snare_only = np.asarray(compose_lighting(source, masks, [snare])).astype(int)
    mid_only = np.asarray(compose_lighting(source, masks, [mid])).astype(int)
    combo = np.asarray(compose_lighting(source, masks, [snare, mid])).astype(int)
    shared = (np.asarray(masks[snare]) > 0) & (np.asarray(masks[mid]) > 0)
    assert shared.any()
    separate_max = np.maximum(snare_only, mid_only)
    assert np.all(combo[shared] <= separate_max[shared] + 2)

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


def test_wav_manifest_and_xsq_share_exact_event_oracle_and_duration(tmp_path: Path) -> None:
    wav = tmp_path / "truth.wav"
    manifest_path = tmp_path / "events.json"
    xsq = tmp_path / "truth.xsq"
    generate(wav, manifest_path, 20.0)
    export_drummer_ground_truth_xsq(xsq, 20.0)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = ET.parse(xsq).getroot()
    timing = [
        {"time": round(float(node.get("start", "0")), 4), "duration": round(float(node.get("duration", "0")), 4), "event": node.get("channel")}
        for node in root.findall("./timingtrack/phoneme")
    ]
    assert timing == manifest
    with wave.open(str(wav), "rb") as handle:
        assert handle.getnframes() / handle.getframerate() == pytest.approx(20.0, abs=1 / 44100)
