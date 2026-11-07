from __future__ import annotations

import json
import shutil
import wave
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from tools.drummer_ground_truth_oracle import TARGETS as LOGICAL_TARGETS, fixture_events
from tools.export_drummer_ground_truth_xsq import export_drummer_ground_truth_xsq
from tools.generate_drummer_ground_truth import generate
from tools.render_drummer_v3_preview import (
    TARGETS,
    _preview_body_keepalive_mask,
    compose_lighting,
    load_component_masks,
)
from tools.drummer_v3_visual_masks import (
    target_surface_key,
    build_geometry_masks,
    exact_geometry,
    load_spec,
)

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


def test_instrument_surfaces_remain_independent_with_complete_front_strikes() -> None:
    submodels = _submodels()
    all_surfaces = {target: submodels[f"{target}_SURFACE"] for target in TARGETS}
    for target in TARGETS:
        surface = all_surfaces[target]
        public = submodels[target]
        assert surface <= public
        for other, other_surface in all_surfaces.items():
            if other != target:
                assert not (surface & other_surface), (target, other)
        # Public lanes are hidden logic. Visible arm submodels may cross a
        # surface; deleting those nodes caused the reported disappearing arms.


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


def test_background_remains_dim_and_active_component_restores_exact_source_pixels() -> None:
    source, masks = load_component_masks()
    idle = compose_lighting(source, masks, [])
    target = TARGETS[1]
    active = compose_lighting(source, masks, [target])

    mask = np.asarray(masks[target]) > 0
    idle_arr = np.asarray(idle)[..., :3].astype(float)
    active_arr = np.asarray(active)[..., :3].astype(float)
    source_arr = np.asarray(source)[..., :3].astype(float)

    assert masks[target].size == source.size
    assert source_arr.mean() * 0.22 < idle_arr.mean() < source_arr.mean() * 0.42
    assert active_arr[mask].mean() > idle_arr[mask].mean() * 2.8

    # Far-away pixels remain the fixed dim drummerbg; a hit never brightens the
    # whole snowman.
    far = np.ones(mask.shape, dtype=bool)
    ys, xs = np.where(mask)
    pad = 28
    far[max(0, ys.min() - pad):min(mask.shape[0], ys.max() + pad + 1),
        max(0, xs.min() - pad):min(mask.shape[1], xs.max() + pad + 1)] = False
    assert np.abs(active_arr[far] - idle_arr[far]).max() <= 2.0


def test_preview_body_stays_dimly_lit_during_idle_and_hits() -> None:
    source, masks = load_component_masks()
    body = np.asarray(_preview_body_keepalive_mask(source, masks)) > 0
    assert body.any()

    source_arr = np.asarray(source)[..., :3].astype(float)
    idle = np.asarray(compose_lighting(source, masks, []))[..., :3].astype(float)
    active = np.asarray(compose_lighting(source, masks, [TARGETS[0]]))[..., :3].astype(float)

    ratio = idle[body].mean() / max(source_arr[body].mean(), 1e-9)
    assert 0.38 <= ratio <= 0.48
    assert np.all(active[body] >= idle[body] - 2.0)


def test_preview_strike_poses_are_not_clipped_by_foreign_surfaces() -> None:
    source, preview_masks = load_component_masks()
    safe_masks = exact_geometry(source, load_spec(), preview_front_overlap=False)["masks"]
    arm_targets = [TARGETS[1], *TARGETS[3:]]
    gained = {
        target: int((np.asarray(preview_masks[target]) > 0).sum())
        - int((np.asarray(safe_masks[target]) > 0).sum())
        for target in arm_targets
    }
    assert any(value > 0 for value in gained.values()), gained


def test_kick_is_actual_red_ring_with_blue_snowflake_source_art() -> None:
    source, masks = load_component_masks()
    surface = np.asarray(masks[target_surface_key(TARGETS[0])]) > 0
    rgb = np.asarray(source)[..., :3]
    pixels = rgb[surface].astype(float)
    red = (pixels[:, 0] > pixels[:, 1] * 1.20) & (pixels[:, 0] > pixels[:, 2] * 1.10)
    blue = (pixels[:, 2] > pixels[:, 0] * 1.15) & (pixels[:, 2] > pixels[:, 1] * 1.05)
    assert red.sum() >= 20
    assert blue.sum() >= 10


def test_each_tom_mask_is_the_green_source_art_not_a_polygon_outline() -> None:
    source, masks = load_component_masks()
    rgb = np.asarray(source)[..., :3]
    for tom in TARGETS[3:6]:
        surface = np.asarray(masks[target_surface_key(tom)]) > 0
        pixels = rgb[surface].astype(float)
        green = (pixels[:, 1] > pixels[:, 0] * 1.20) & (pixels[:, 1] > pixels[:, 2] * 1.08)
        assert green.mean() > 0.45, (tom, green.mean())
        # Compare to the authored search shape, not its bounding rectangle:
        # tightening a window around the real artwork legitimately increases
        # rectangle occupancy. A filled replacement polygon must still fail.
        authored = np.asarray(build_geometry_masks(source.size, load_spec())["surfaces"][tom.removeprefix("HX_SNOWMAN_DRUMMER_V3_")+"_SURFACE"]) > 0
        assert surface.sum() < authored.sum() * 0.95
        assert not np.any(surface & (rgb.max(axis=2) < 24))


def test_tom_windows_do_not_pick_up_neighboring_green_drums():
    _, masks = load_component_masks()
    mid = np.asarray(masks[target_surface_key(TARGETS[4])])
    high = np.asarray(masks[target_surface_key(TARGETS[3])])
    assert not mid[255:275, 145:180].any()  # floor-tom upper left body
    assert not high[260:280, 407:422].any()  # unused lower-right drum



def test_actuator_brightens_in_its_original_source_colors() -> None:
    source, masks = load_component_masks()
    snare = TARGETS[1]
    target_mask = np.asarray(masks[snare]) > 0
    surface_mask = np.asarray(masks[target_surface_key(snare)]) > 0
    actuator_only = target_mask & ~surface_mask
    idle = np.asarray(compose_lighting(source, masks, []))[..., :3].astype(float)
    active = np.asarray(compose_lighting(source, masks, [snare]))[..., :3].astype(float)
    source_arr = np.asarray(source)[..., :3].astype(float)

    assert actuator_only.any()
    assert active[actuator_only].mean() > idle[actuator_only].mean() * 2.8

    # Active actuator pixels are a brightness/saturation transform of the real
    # source art, not a flat instrument-color paint.
    source_spread = source_arr[actuator_only].std(axis=0).mean()
    active_spread = active[actuator_only].std(axis=0).mean()
    assert source_spread > 5.0
    assert active_spread > 5.0


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
