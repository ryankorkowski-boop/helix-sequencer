"""Keyboard-arm proportion and note-contact safety tests for the production rig."""
import numpy as np

from models.refined_band_scene import RefinedBandScene
from models.keyboard_motion_plan import plan_keyboard_hands
from models.band_motion_refinement import elbow_3d


def _keyboard_fixture():
    scene = RefinedBandScene("prismatic_orrery")
    rigs = {r["side"]: r for r in scene.rigs if r["role"] == "piano"}
    centers = {int(o["name"].removeprefix("piano_key_")): o["matrix"][:3, 3].copy()
               for o in scene.instances if o["name"].startswith("piano_key_")}
    return scene, rigs, centers


def test_authored_arm_links_are_short_and_fixed():
    scene, rigs, centers = _keyboard_fixture()
    assert set(rigs) == {"left", "right"}
    for side in rigs:
        upper, lower = rigs[side]["link_lengths"]
        assert (upper, lower) == (.52, .50)
        shoulder = rigs[side]["shoulder"]
        rest = rigs[side]["hand"]
        distance = np.linalg.norm(rest - shoulder)
        assert abs(upper - lower) < distance < upper + lower


def test_keyboard_contact_motion_is_bounded_and_ik_links_stay_constant():
    _, rigs, centers = _keyboard_fixture()
    mid = (rigs["left"]["shoulder"][0] + rigs["right"]["shoulder"][0]) / 2
    # Select actually reachable white/black keys, not a synthetic, unreachable pose.
    chosen = {}
    for side in ("left", "right"):
        rig = rigs[side]
        upper, lower = rig["link_lengths"]
        options = []
        for pitch, center in centers.items():
            if (center[0] <= mid) != (side == "left"):
                continue
            target = center + (0, .110, .065)
            distance = np.linalg.norm(target - rig["shoulder"])
            if abs(upper - lower) + .1 < distance < upper + lower - .1:
                options.append((abs(pitch-66), pitch))
        assert options, "Short arms have no reachable keys"
        chosen[side] = min(options)[1]
    held = np.full((130, 2), -1, dtype=int)
    levels = np.zeros((130, 2), dtype=float)
    held[:110] = [chosen["left"], chosen["right"]]
    levels[:110] = 1
    lanes, contacts, report = plan_keyboard_hands(held, levels, centers, rigs)
    for side in ("left", "right"):
        lane = lanes[side]
        upper, lower = rigs[side]["link_lengths"]
        shoulder = rigs[side]["shoulder"]
        assert np.linalg.norm(np.diff(lane, axis=0), axis=1).max() <= .030001
        assert np.linalg.norm(np.diff(lane, n=2, axis=0), axis=1).max() <= .010001
        assert all(c is None or c == chosen[side] for c in contacts[side])
        assert all(c is None for c in contacts[side][110:])
        assert any(c == chosen[side] for c in contacts[side][:110])
        for wrist in lane:
            elbow = elbow_3d(shoulder, wrist, upper, lower,
                            (-.8 if side=="left" else .8, -.2, .8))
            np.testing.assert_allclose(np.linalg.norm(elbow-shoulder), upper, atol=1e-5)
            np.testing.assert_allclose(np.linalg.norm(elbow-wrist), lower, atol=1e-5)
        assert report[side]["contact_frames"] > 0


def test_unreachable_notes_do_not_create_fake_strikes():
    _, rigs, centers = _keyboard_fixture()
    held = np.full((60, 2), [21, 108], dtype=int)
    levels = np.ones_like(held, dtype=float)
    lanes, contacts, report = plan_keyboard_hands(held, levels, centers, rigs)
    assert all(x is None for values in contacts.values() for x in values)
    assert all(report[side]["contact_frames"] == 0 for side in ("left", "right"))
    assert all(np.isfinite(v).all() for v in lanes.values())
