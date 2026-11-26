import json
from pathlib import Path

from core.cooperative_intelligence import (
    CooperativeShowBrief,
    CooperativeShowDirector,
    SectionDirective,
    is_pure_white_palette,
    parse_xlights_settings,
)
from core import orchestration_balance as ob


def test_brief_json_roundtrip(tmp_path: Path) -> None:
    brief = CooperativeShowBrief(
        song_duration_ms=12000,
        bpm=120.0,
        beat_grid_ms=[0, 500, 1000, 1500, 2000],
        sections=[
            SectionDirective(name="INTRO", start_ms=0, end_ms=4000, spatial_pattern="center_out"),
            SectionDirective(name="CHORUS", start_ms=4000, end_ms=12000, spatial_pattern="full_yard_burst"),
        ],
        model_zones={"MegaTree": "center", "MiniTree_L1": "left"},
        chorus_motif_family="Spirals",
        masterpiece_score=91.5,
    )
    out = brief.save_json(tmp_path / "brief.json")
    loaded = CooperativeShowBrief.load_json(out)
    assert loaded.song_duration_ms == 12000
    assert loaded.bpm == 120.0
    assert loaded.beat_grid_ms == [0, 500, 1000, 1500, 2000]
    assert len(loaded.sections) == 2
    assert loaded.sections[1].name == "CHORUS"
    assert loaded.model_zones["MegaTree"] == "center"
    assert loaded.chorus_motif_family == "Spirals"
    assert loaded.masterpiece_score == 91.5


def test_beat_snapping() -> None:
    brief = CooperativeShowBrief(song_duration_ms=5000, beat_grid_ms=[0, 500, 1000, 1500])
    assert brief.snap_to_beat_ms(1030, tolerance_ms=65) == 1000
    assert brief.snap_to_beat_ms(1470, tolerance_ms=65) == 1500
    assert brief.snap_to_beat_ms(1250, tolerance_ms=65) == 1250


def test_layer_conflict_promotion_to_blend_layers() -> None:
    director = CooperativeShowDirector.from_orchestration_and_audio(
        song_duration_ms=10000,
        bpm=120.0,
        audio_sections=[{"name": "CHORUS", "start_ms": 0, "end_ms": 10000}],
    )
    unmask_dir = director.plan_cooperative_placement(
        model_name="MegaTree",
        start_ms=1000,
        end_ms=2500,
        effect_name="Spirals",
        label="CHORUS_MOTION",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1", "L2"],
        layer_has_conflict=True,
        lane="overlay",
    )
    assert unmask_dir.promoted_from_conflict is True
    assert unmask_dir.target_layer_key == "L1"
    assert unmask_dir.layer_method == "1 is Unmask"
    parsed_unmask = parse_xlights_settings(unmask_dir.adjusted_settings)
    assert parsed_unmask["T_CHOICE_LayerMethod"] == "1 is Unmask"

    additive_dir = director.plan_cooperative_placement(
        model_name="MegaTree",
        start_ms=1500,
        end_ms=2500,
        effect_name="Twinkle",
        label="CHORUS_SPARKLE",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1", "L2"],
        layer_has_conflict=True,
        lane="flash",
    )
    assert additive_dir.promoted_from_conflict is True
    assert additive_dir.layer_method == "Additive"


def test_soft_brightness_layering() -> None:
    director = CooperativeShowDirector.from_orchestration_and_audio(
        song_duration_ms=10000,
        bpm=120.0,
        audio_sections=[
            {"name": "INTRO", "start_ms": 0, "end_ms": 5000},
            {"name": "CHORUS", "start_ms": 5000, "end_ms": 10000},
        ],
    )
    base_dir = director.plan_cooperative_placement(
        model_name="Roofline",
        start_ms=500,
        end_ms=2500,
        effect_name="Color Wash",
        label="BASE",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1"],
        layer_has_conflict=False,
        lane="primary",
    )
    assert base_dir.brightness >= 70
    assert base_dir.brightness < 100

    focus_dir = director.plan_cooperative_placement(
        model_name="Singer",
        start_ms=5500,
        end_ms=7500,
        effect_name="Faces",
        label="VOCAL",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1"],
        layer_has_conflict=False,
        lane="vocal",
    )
    assert focus_dir.brightness == 100


def test_anti_white_wash_diversification() -> None:
    director = CooperativeShowDirector.from_orchestration_and_audio(
        song_duration_ms=5000,
        bpm=120.0,
        audio_sections=[{"name": "VERSE", "start_ms": 0, "end_ms": 5000}],
    )
    white_palette = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1,C_BUTTON_Palette2=#FEFEFE,C_CHECKBOX_Palette2=1"
    assert is_pure_white_palette(white_palette)

    directives = [
        director.plan_cooperative_placement(
            model_name=f"Prop_{i}",
            start_ms=100,
            end_ms=1000,
            effect_name="On",
            label="FLASH",
            requested_layer_key="L0",
            available_layer_keys=["L0"],
            layer_has_conflict=False,
            palette_str=white_palette,
            lane="flash",
        )
        for i in range(12)
    ]
    assert any(d.anti_white_wash_applied for d in directives)
    diversified = next(d for d in directives if d.anti_white_wash_applied)
    assert diversified.adjusted_palette is not None
    assert not is_pure_white_palette(diversified.adjusted_palette)


def test_spatial_call_and_response_staggering() -> None:
    director = CooperativeShowDirector.from_orchestration_and_audio(
        song_duration_ms=10000,
        bpm=120.0,
        audio_sections=[{"name": "PRECHORUS", "start_ms": 0, "end_ms": 10000}],
        layout_coords={"LeftTree": (0.0, 0.5), "CenterTree": (0.5, 0.5), "RightTree": (1.0, 0.5)},
    )
    left_d = director.plan_cooperative_placement(
        model_name="LeftTree",
        start_ms=1000,
        end_ms=2000,
        effect_name="Bars",
        label="MOTION",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1"],
        layer_has_conflict=False,
        lane="overlay",
    )
    right_d = director.plan_cooperative_placement(
        model_name="RightTree",
        start_ms=1000,
        end_ms=2000,
        effect_name="Bars",
        label="MOTION",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1"],
        layer_has_conflict=False,
        lane="overlay",
    )
    assert left_d.spatial_phase_offset_ms == 0
    assert right_d.spatial_phase_offset_ms > left_d.spatial_phase_offset_ms


def test_chorus_motif_continuity() -> None:
    director = CooperativeShowDirector.from_orchestration_and_audio(
        song_duration_ms=10000,
        bpm=120.0,
        audio_sections=[{"name": "CHORUS", "start_ms": 0, "end_ms": 10000}],
    )
    first = director.plan_cooperative_placement(
        model_name="MegaTree",
        start_ms=1000,
        end_ms=2000,
        effect_name="Pinwheel",
        label="CHORUS",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1"],
        layer_has_conflict=False,
        lane="overlay",
    )
    second = director.plan_cooperative_placement(
        model_name="Roofline",
        start_ms=3000,
        end_ms=4000,
        effect_name="Pinwheel",
        label="CHORUS",
        requested_layer_key="L0",
        available_layer_keys=["L0", "L1"],
        layer_has_conflict=False,
        lane="overlay",
    )
    assert first.motif_reinforced is False
    assert director.brief.chorus_motif_family == "Pinwheel"
    assert second.motif_reinforced is True
    assert director.telemetry.motif_callbacks_applied == 1


def test_orchestration_balance_backward_compatibility() -> None:
    assert ob.priority_for_lane("vocal", is_climax=True) > ob.priority_for_lane("primary")
    assert ob.cooperative_layer_blend("Twinkle", "CHORUS_FLASH", 1) == "Additive"
    assert ob.cooperative_brightness_scale("VOCAL_LEAD", "CHORUS") == 100
    assert ob.cooperative_brightness_scale("BASE_WASH", "INTRO") >= 70
    assert ob.spatial_zone_for_model("Left_MiniTree_1") == "left"
