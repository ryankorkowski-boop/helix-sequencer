from __future__ import annotations

from types import SimpleNamespace

from core.color_system import Color, ColorEngine


def test_color_scaled_clamps_channels() -> None:
    color = Color(200, 100, 50)

    assert color.scaled(2.0).as_tuple() == (200, 100, 50)
    assert color.scaled(0.5).as_tuple() == (100, 50, 25)


def test_color_engine_maps_motifs_to_deterministic_palettes() -> None:
    engine = ColorEngine()
    engine.update(SimpleNamespace(motif="sparkle_field"), intensity=1.0)

    first = engine.pick_color("roof_star", energy=0.8)
    second = engine.pick_color("roof_star", energy=0.8)

    assert engine.palette_name == "sparkle"
    assert first == second


def test_color_engine_scales_with_energy() -> None:
    engine = ColorEngine()
    engine.update(SimpleNamespace(motif="pulse_cascade"), intensity=1.0)

    low = sum(engine.pick_color("kick_drum_ground", energy=0.1))
    high = sum(engine.pick_color("kick_drum_ground", energy=0.9))

    assert high > low


def test_color_engine_uses_cool_fallback_for_unknown_motif() -> None:
    engine = ColorEngine()

    engine.update(SimpleNamespace(motif="unknown"), intensity=1.0)

    assert engine.palette_name == "cool"
