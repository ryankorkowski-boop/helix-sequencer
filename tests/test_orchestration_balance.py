from core.orchestration_balance import (
    allows_piano_overlay,
    allows_vocal,
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


def test_accent_gate_preserves_snowman_performers_without_stopping_spatial_yard():
    from core.orchestration_balance import accent_target_allowed

    assert not accent_target_allowed("HX_SNOWMAN_DRUMMER", "pixel_kick", layout_has_piano=True, layout_has_singer=True)
    assert not accent_target_allowed("HX_FLOOR_PIANO_C_LOW", "spatial_chase", layout_has_piano=True, layout_has_singer=True)
    assert not accent_target_allowed("HX_SNOWMAN_SINGER_MOUTH", "drop_flash", layout_has_piano=True, layout_has_singer=True)
    assert accent_target_allowed("HX_ARCH_01", "spatial_chase", layout_has_piano=True, layout_has_singer=True)
    assert accent_target_allowed("HX_CENTRAL_MATRIX", "lyric_text_pixel", layout_has_piano=True, layout_has_singer=True)
    assert accent_target_allowed("HX_ARCH_01", "polyphonic_keyboard", layout_has_piano=False, layout_has_singer=False)
    assert not accent_target_allowed("HX_ARCH_01", "polyphonic_keyboard", layout_has_piano=True, layout_has_singer=True)


def test_quiet_sections_forbid_flash_regardless_of_density():
    from core.orchestration_balance import restrained_accent_budget

    assert restrained_accent_budget("CHORUS", quiet=True, density=2.0) == (1, 0)
    assert restrained_accent_budget("VERSE", quiet=False, density=0.2) == (3, 1)
    assert restrained_accent_budget("CHORUS", quiet=False, density=1.0) == (14, 2)


def test_show_direction_budget_limits_whole_yard_wash_without_suppressing_focal_group():
    from core.orchestration_balance import ShowDirectionBudget, family_cap_for_layout, vu_cap_for_section

    assert family_cap_for_layout(30, 9) == 5
    assert family_cap_for_layout(384, 9) == 9
    assert family_cap_for_layout(10240, 16) == 12
    assert vu_cap_for_section(384) == 64
    gate = ShowDirectionBudget(30, 9)
    for family in ("mega", "arch", "matrix", "roof", "spiral"):
        assert gate.allow(section="VERSE", family=family, label="primary_phrase")
    assert not gate.allow(section="VERSE", family="snowflake", label="primary_phrase")
    assert gate.held["family"] == 1
    assert gate.allow(section="VERSE", family="mega", label="primary_phrase")
    assert not gate.allow(section="VERSE", family="arch", label="piano_support")
    assert gate.held["support"] == 1


def test_vu_meter_has_bounded_activity():
    from core.orchestration_balance import ShowDirectionBudget

    gate = ShowDirectionBudget(16, 3)
    for _ in range(24):
        assert gate.allow(section="CHORUS", family="mega", label="green_vu")
    assert not gate.allow(section="CHORUS", family="mega", label="green_vu")
    assert gate.held["vu"] == 1


def test_family_budget_does_not_consume_failed_proposals():
    from core.orchestration_balance import ShowDirectionBudget

    gate = ShowDirectionBudget(30, 9)
    assert gate.can_allow(section="VERSE", family="mega", label="primary_phrase")
    assert gate.can_allow(section="VERSE", family="mega", label="primary_phrase")
    assert gate._families == {}
    gate.record(section="VERSE", family="mega", label="primary_phrase")
    assert gate._families["VERSE"] == ["mega"]
    for family in ("arch", "matrix", "roof", "spiral"):
        assert gate.can_allow(section="VERSE", family=family, label="primary_phrase")
        gate.record(section="VERSE", family=family, label="primary_phrase")
    assert not gate.can_allow(section="VERSE", family="snowflake", label="primary_phrase")
    gate.reject(section="VERSE", family="snowflake", label="primary_phrase")
    assert gate.held["family"] == 1
    assert len(gate._families["VERSE"]) == 5
    assert gate.can_allow(section="CHORUS", family="snowflake", label="primary_phrase")


def test_vu_meter_does_not_consume_failed_placements():
    from core.orchestration_balance import ShowDirectionBudget

    gate = ShowDirectionBudget(16, 3)
    for _ in range(25):
        assert gate.can_allow(section="CHORUS", family="mega", label="green_vu")
    assert gate._vu == {}
    for _ in range(24):
        gate.record(section="CHORUS", family="mega", label="green_vu")
    assert not gate.can_allow(section="CHORUS", family="mega", label="green_vu")


def test_repeated_verse_and_chorus_sections_have_distinct_budgets():
    from types import SimpleNamespace
    from core.orchestration_balance import section_instance_key, ShowDirectionBudget

    parts = [
        SimpleNamespace(label="VERSE", start_ms=0, end_ms=1000),
        SimpleNamespace(label="CHORUS", start_ms=1000, end_ms=2000),
        SimpleNamespace(label="VERSE", start_ms=2000, end_ms=3000),
    ]
    key_a = section_instance_key(parts, 50)
    key_b = section_instance_key(parts, 2050)
    assert key_a == "0:VERSE"
    assert key_b == "2:VERSE"
    gate = ShowDirectionBudget(8, 3)
    for key in (key_a, key_b):
        assert gate.can_allow(section=key, family="mega", label="primary_phrase")
        gate.record(section=key, family="mega", label="primary_phrase")
    assert len(gate._families) == 2


def test_flash_quiet_guard_rejects_effect_overlap_without_suppressing_adjacent_note():
    from core.orchestration_balance import intersects_quiet_window

    quiet = [(200, 400)]
    assert intersects_quiet_window(100, 220, quiet)
    assert intersects_quiet_window(300, 460, quiet)
    assert not intersects_quiet_window(100, 200, quiet)
    assert not intersects_quiet_window(400, 600, quiet)
