from core.effect_engine import SequentialPool, build_keyboard_lane_with_routes, section_planned_family
from core.orchestration_balance import (
    ShowDirectionBudget,
    allows_piano_overlay,
    allows_vocal,
    family_cap_for_layout,
    flash_cap_per_window,
    label_lane,
    model_role,
    overlay_cap_per_second,
)


def test_roles_match_showcase_names():
    assert model_role("HX_FLOOR_PIANO_C_LOW") == "piano"
    assert model_role("HX_SNOWMAN_DRUMMER") == "percussion"
    assert model_role("HX_SNOWMAN_SINGER_MOUTH") == "singer"
    assert model_role("HELIXIA_GIANT_DOUBLE_HELIX_A") == "hero"
    assert model_role("HX_ARCH_01") == "arch"
    assert model_role("HX_lot_01_roofline") == "house"


def test_piano_overlay_stays_on_piano_when_a_piano_exists():
    assert label_lane("polyphonic_keyboard") == "piano_overlay"
    assert label_lane("player_piano_mega") == "piano_overlay"
    assert allows_piano_overlay("HX_FLOOR_PIANO_C_LOW", layout_has_piano=True)
    assert not allows_piano_overlay("HX_ARCH_01", layout_has_piano=True)
    assert allows_piano_overlay("HX_ARCH_01", layout_has_piano=False)


def test_vocal_faces_stay_on_singers():
    assert allows_vocal("HX_SNOWMAN_SINGER", "lyric_mouth_sync", layout_has_singer=True)
    assert allows_vocal("talking head 2", "lyric_mouth_sync", layout_has_singer=True)
    assert not allows_vocal("HX_ARCH_01", "lyric_mouth_sync", layout_has_singer=True)
    assert allows_vocal("HX_CENTRAL_MATRIX", "lyric_text_pixel", layout_has_singer=True)
    assert allows_vocal("HX_ARCH_01", "lyric_mouth_sync", layout_has_singer=False)


def test_quiet_sections_hold_fewer_overlays_than_chorus():
    assert overlay_cap_per_second("VERSE") < overlay_cap_per_second("CHORUS")
    assert overlay_cap_per_second("BRIDGE") == overlay_cap_per_second("VERSE")
    assert flash_cap_per_window("VERSE") < flash_cap_per_window("CHORUS")
    assert label_lane("multiband_bass") == "overlay"
    assert label_lane("pixel_scene_matrix") == "overlay"
    assert label_lane("drop_flash") == "flash"
    assert label_lane("digital_piano") == "primary"


def test_keyboard_lane_collapses_to_piano_models():
    pools = [
        SequentialPool("notes", "notes", ["HX_FLOOR_PIANO_C_LOW", "HX_FLOOR_PIANO_D_LOW"]),
        SequentialPool("line_white", "line", ["HX_lot_01_roofline", "HX_lot_02_roofline"]),
        SequentialPool("arches", "arch", ["HX_ARCH_01", "HX_ARCH_02"]),
        SequentialPool("mega", "mega", ["HX_FIB_MEGA_TREE_CENTER"]),
    ]
    lane = build_keyboard_lane_with_routes(pools)
    assert lane == ["HX_FLOOR_PIANO_C_LOW", "HX_FLOOR_PIANO_D_LOW"]


def test_keyboard_lane_unchanged_without_a_piano():
    pools = [
        SequentialPool("line_white", "line", ["north roofline", "south roofline"]),
        SequentialPool("arches", "arch", ["arch 1"]),
    ]
    lane = build_keyboard_lane_with_routes(pools)
    assert "north roofline" in lane
    assert "arch 1" in lane


def test_large_layouts_may_use_more_than_five_families():
    assert family_cap_for_layout(30, 9) == 5
    assert family_cap_for_layout(384, 9) == 9
    assert family_cap_for_layout(384, 0) > 5
    assert section_planned_family("v27")
    assert not section_planned_family("v23")


def test_show_budget_keeps_families_on_a_large_yard_but_not_a_support_wash():
    budget = ShowDirectionBudget(384, 9)
    admitted = []
    for family in ("mega", "line", "arch", "matrix", "stars", "spinner", "sphere", "canes_combo", "gt"):
        assert budget.allow(section="CHORUS", family=family, label="bass_focus")
        admitted.append(family)
    assert budget.allow(section="CHORUS", family="mega", label="spatial_keyboard_mega_support")
    assert not budget.allow(section="CHORUS", family="spinner", label="spatial_keyboard_spinner_support")
    assert len(admitted) == 9

