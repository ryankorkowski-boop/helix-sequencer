"""Regression checks for workspace-learned effects on incompatible targets."""

from types import SimpleNamespace

from core.effect_engine import (RuntimeTuning, pick_runtime_effect,
                                requested_effect_supported_for_target)
from core.model_parser import Model


CATALOG = {"effect_names": ["On", "Bars", "Spirals", "Pinwheel", "Twinkle", "Strobe", "Shimmer", "Ramp"]}


def _model(string_type):
    return Model(name="Mixed Layout Spinner", display_as="Spinner", type="spinner",
                 strings=1, nodes_per_string=16, total_pixels=16, start_channel=1,
                 coordinates=None, end_coordinates=None, orientation=None, wiring=None,
                 string_type=string_type, color_family=None)


def test_mixed_layout_single_color_target_rejects_explicit_and_learned_pixels():
    model = _model("Single Color White")
    tuning = RuntimeTuning(ac_lights_only=False, motion_effect="Pinwheel")
    history = SimpleNamespace(family_effects={"spinner": ["Pinwheel", "Bars"]})
    assert not requested_effect_supported_for_target(
        requested="Pinwheel", layer="motion", family="spinner", model=model,
        tuning=tuning, catalog=CATALOG)
    for requested in ("On", "Pinwheel", "Bars"):
        result = pick_runtime_effect(
            requested=requested, layer="motion", family="spinner", parsed_model=model,
            tuning=tuning, catalog=CATALOG, workspace_history=history, fallback="Pinwheel")
        assert result.lower() in {"on", "ramp", "strobe", "twinkle", "shimmer"}


def test_mixed_layout_rgb_neighbor_retains_spatial_effect():
    result = pick_runtime_effect(
        requested="Pinwheel", layer="motion", family="spinner",
        parsed_model=_model("RGB Nodes"), tuning=RuntimeTuning(ac_lights_only=False),
        catalog=CATALOG, workspace_history=None, fallback="On")
    assert result == "Pinwheel"


def test_unrecognized_color_capability_fails_closed_for_spatial_effects():
    result = pick_runtime_effect(
        requested="Pinwheel", layer="motion", family="spinner",
        parsed_model=_model("Unknown"), tuning=RuntimeTuning(ac_lights_only=False),
        catalog=CATALOG, workspace_history=None, fallback="Pinwheel")
    assert result.lower() in {"on", "ramp", "strobe", "twinkle", "shimmer"}


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

