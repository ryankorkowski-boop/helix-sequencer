"""Regression checks for workspace-learned effects on incompatible targets."""

from types import SimpleNamespace

from core.effect_engine import RuntimeTuning, pick_runtime_effect


CATALOG = {"effect_names": ["On", "Bars", "Spirals", "Pinwheel", "Twinkle", "Strobe", "Shimmer", "Ramp"]}


def test_learned_spinner_effect_does_not_override_star_motion():
    tuning = RuntimeTuning()
    history = SimpleNamespace(family_effects={"stars": ["Pinwheel"]})
    result = pick_runtime_effect(
        requested="On", layer="motion", family="stars", parsed_model=None,
        tuning=tuning, catalog=CATALOG, workspace_history=history, fallback="On",
    )
    assert result != "Pinwheel"


def test_ac_only_rejects_learned_pixel_effect():
    tuning = RuntimeTuning(ac_lights_only=True)
    history = SimpleNamespace(family_effects={"spinner": ["Pinwheel"]})
    result = pick_runtime_effect(
        requested="On", layer="motion", family="spinner", parsed_model=None,
        tuning=tuning, catalog=CATALOG, workspace_history=history, fallback="On",
    )
    assert result.lower() in {"on", "ramp", "strobe", "twinkle", "shimmer"}
