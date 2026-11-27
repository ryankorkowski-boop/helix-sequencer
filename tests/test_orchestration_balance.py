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
