from tools.style_engine import (
    AudioSegment,
    HelixStyleEngine,
    LayoutProfile,
    LayoutProp,
    StylePreset,
)


def sample_layout() -> LayoutProfile:
    return LayoutProfile(
        props=(
            LayoutProp("MegaTree", type="tree", role="centerpiece"),
            LayoutProp("Arch_01", type="arch", role="motion"),
            LayoutProp("HouseOutline", type="outline", role="outline"),
            LayoutProp("Matrix", type="matrix", role="matrix"),
            LayoutProp("HelixStrand_A", type="polyline_3d", role="centerpiece", supports_3d=True),
        )
    )


def test_high_energy_chorus_produces_sweep_or_burst() -> None:
    engine = HelixStyleEngine("CinematicSweep", sample_layout())

    decision = engine.decide(
        AudioSegment(
            start=10.0,
            duration=0.5,
            section="chorus",
            event_type="hit",
            energy=0.92,
        )
    )

    assert decision.intent in {"sweep", "burst"}
    assert decision.effect in {"cinematic_sweep", "trailer_hit_burst"}
    assert decision.targets


def test_low_energy_verse_produces_fade_or_texture() -> None:
    engine = HelixStyleEngine("ClassicChristmas", sample_layout())

    decision = engine.decide(
        AudioSegment(
            start=2.0,
            duration=1.0,
            section="verse",
            event_type="beat",
            energy=0.22,
        )
    )

    assert decision.intent in {"fade", "texture"}
    assert decision.effect in {"warm_color_fade", "gentle_twinkle_texture"}


def test_beatdrive_favors_pulse_or_chase() -> None:
    engine = HelixStyleEngine("BeatDrive", sample_layout())

    strong_beat = engine.decide(
        {
            "time": 4.0,
            "duration": 0.25,
            "section": "verse",
            "event": "kick",
            "energy": 0.7,
            "beat_strength": 0.95,
        }
    )

    assert strong_beat.intent in {"pulse", "chase"}
    assert strong_beat.effect in {"beat_pulse", "tight_chase"}


def test_classic_christmas_uses_red_green_white_gold_palette() -> None:
    engine = HelixStyleEngine("ClassicChristmas", sample_layout())

    decision = engine.decide(
        AudioSegment(
            start=24.0,
            duration=0.5,
            section="chorus",
            event_type="beat",
            energy=0.82,
        )
    )

    assert decision.palette == ("red", "green", "white", "gold")


def test_spatial_helix_selects_3d_motion_and_3d_targets() -> None:
    engine = HelixStyleEngine("SpatialHelix", sample_layout())

    decision = engine.decide(
        AudioSegment(
            start=32.0,
            duration=0.5,
            section="build",
            event_type="beat",
            energy=0.68,
            pitch_direction="up",
        )
    )

    assert decision.motion == "upward_z"
    assert "HelixStrand_A" in decision.targets
    assert decision.effect == "helix_spiral_sweep"


def test_decisions_are_deterministic_for_same_input() -> None:
    engine = HelixStyleEngine(StylePreset("PartyMode"), sample_layout())
    segment = AudioSegment(
        start=12.5,
        duration=0.5,
        section="drop",
        event_type="drop",
        energy=0.95,
        onset_density=0.9,
    )

    assert engine.decide(segment) == engine.decide(segment)


def test_empty_layout_targets_all_sentinel() -> None:
    engine = HelixStyleEngine("BeatDrive", LayoutProfile())

    decision = engine.decide(
        AudioSegment(start=0.0, duration=0.5, event_type="beat", beat_strength=0.9)
    )

    assert decision.targets == ("ALL",)
