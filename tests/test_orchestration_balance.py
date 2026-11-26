from core.effect_engine import SequentialPool, build_keyboard_lane_with_routes
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


def test_governor_charges_accepted_final_candidates_only():
    from core.canonical_timeline_orchestrator import MusicalContext, MusicalSection
    from core.composition_governor import CompositionGovernor
    from core.orchestration_balance import PlacementProposal

    music = MusicalContext(
        duration_ms=2000,
        sections=(MusicalSection("VERSE", 0, 1020, 0.2), MusicalSection("CHORUS", 1020, 2000, 0.8)),
        quiet_windows=((0, 900),),
    )
    session = CompositionGovernor().begin_placement(music, ["Arch 1"])
    accent = PlacementProposal("Arch 1", "pixel_vocal", 950, 1110, "On")
    quiet_window = session.budget_window(accent, 100)
    verse_window = session.budget_window(accent, 1000)
    chorus_window = session.budget_window(accent, 1040)
    assert {session.limits[key] for key in (quiet_window, verse_window, chorus_window)} == {1, 5, 14}
    assert session.budget_rejection(accent, quiet_window, ()) is None
    session.reject(accent, "same-layer conflict")
    assert session.budget_rejection(accent, quiet_window, ()) is None
    session.accept(accent, 100, quiet_window)
    assert session.budget_rejection(accent, quiet_window, ()) == "overlay over section budget"
    assert session.budget_rejection(accent, quiet_window, (quiet_window,)) is None
    session.displace(accent, quiet_window)
    session.accept(accent, 1040, chorus_window)
    summary = session.summary([(accent, 1040)])
    assert summary["contributions"]["pixel_reactive"] == {
        "proposed": 3, "accepted": 2, "rejected": 1, "displaced": 1, "retained": 1,
    }
    assert summary["resolved_conflicts"] == {"higher_priority_same_layer": 1}


def test_owned_specialists_rank_above_accents_and_keep_layout_fallback():
    from core.canonical_timeline_orchestrator import MusicalContext
    from core.composition_governor import CompositionGovernor
    from core.orchestration_balance import PlacementProposal

    music = MusicalContext(duration_ms=2000, sections=())
    governor = CompositionGovernor()
    session = governor.begin_placement(music, ["Floor Piano", "Singer", "Drummer", "Arch 1"])
    piano = PlacementProposal("Floor Piano", "polyphonic_keyboard", 0, 100, "On")
    accent = PlacementProposal("Floor Piano", "pixel_kick", 0, 100, "On")
    yard_piano = PlacementProposal("Arch 1", "polyphonic_keyboard", 0, 100, "On")
    assert session.ownership_rejection(piano) is None
    assert session.priority(piano, "other") > session.priority(accent, "drums")
    assert session.ownership_rejection(accent) == "accent kept off dedicated performer"
    assert session.ownership_rejection(yard_piano) == "piano overlay kept off non-piano models"
    assert governor.begin_placement(music, ["Arch 1"]).ownership_rejection(yard_piano) is None


def test_late_audio_reactive_cue_gets_a_slot_without_raising_the_cap():
    from core.canonical_timeline_orchestrator import MusicalContext
    from core.composition_governor import CompositionGovernor
    from core.orchestration_balance import PlacementProposal

    session = CompositionGovernor().begin_placement(MusicalContext(duration_ms=1000, sections=()), ["Arch"])
    pixel = PlacementProposal("Arch", "pixel_vocal", 30, 110, "On")
    reactive = PlacementProposal("Arch", "audio_reactive_bass_pulse", 30, 110, "On")
    session.reserve_audio_reactive_windows([30])
    window = session.budget_window(pixel, 30)
    for _ in range(4):
        assert session.budget_rejection(pixel, window, ()) is None
        session.accept(pixel, 30, window)
    assert session.budget_rejection(pixel, window, ()) == "remaining overlay slot reserved for audio-reactive cues"
    assert session.budget_rejection(reactive, window, ()) is None
    session.finish_audio_reactive()
    assert session.budget_rejection(pixel, window, ()) is None
    session.accept(reactive, 30, window)
    assert session.budget_rejection(pixel, window, ()) == "overlay over section budget"
