"""xLights 2026.19 layer-blend settings.

The keys come from the 2026.19 AppImage, not from guessed attribute names:

- ``usr/share/xLights/effectmetadata/shared/Blending.json`` says Layer Method
  is serialized as ``T_CHOICE_LayerMethod`` and Canvas source layers as
  ``T_LayersSelected``.
- The same binary's BlendingPanel help lists the choice labels below.
- ``T_CHECKBOX_Canvas`` and ``T_SLIDER_EffectLayerMix`` are stored on the
  effect settings string, beside the effect's own ``E_`` keys.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


XLIGHTS_LAYER_METHODS = (
    "Normal",
    "Average",
    "Layered",
    "Additive",
    "Subtractive",
    "Brightness",
    "Highlight",
    "Highlight Vibrant",
    "Max",
    "Min",
    "Bottom-top",
    "Left-Right",
    "1 is Mask",
    "2 is Mask",
    "1 is Unmask",
    "2 is Unmask",
    "1 is True Unmask",
    "2 is True Unmask",
    "Shadow 1 on 2",
    "Shadow 2 on 1",
    "1 reveals 2",
    "2 reveals 1",
)

# Helix layering names that are not xLights labels.
_INTERNAL_TO_XLIGHTS = {
    "normal": "Normal",
    "overlay": "Average",
    "screen": "Highlight",
    "additive": "Additive",
    "layered": "Layered",
    "average": "Average",
    "min": "Min",
    "max": "Max",
}

SPATIAL_EFFECTS = {
    "butterfly",
    "curtain",
    "fan",
    "galaxy",
    "liquid",
    "marquee",
    "morph",
    "pinwheel",
    "plasma",
    "shape",
    "shockwave",
    "singlestrand",
    "spirals",
    "wave",
}

CANVAS_ROLES = {"texture", "motion", "focus"}


def xlights_layer_method(name: str) -> str:
    label = (name or "Normal").strip()
    if label in XLIGHTS_LAYER_METHODS:
        return label
    return _INTERNAL_TO_XLIGHTS.get(label.lower(), "Normal")


def canvas_for(layer_role: str, effect_name: str) -> bool:
    if (layer_role or "").lower() in CANVAS_ROLES:
        return True
    compact = "".join(ch for ch in (effect_name or "").lower() if ch.isalnum())
    return compact in SPATIAL_EFFECTS


def blend_settings(
    base: str,
    method: str,
    *,
    canvas: bool = False,
    mix: int | None = None,
    layers_selected: str | None = None,
) -> str:
    """Append the official blend keys, replacing any previous copies."""
    drop = (
        "T_CHOICE_LayerMethod=",
        "T_CHECKBOX_Canvas=",
        "T_SLIDER_EffectLayerMix=",
        "T_LayersSelected=",
    )
    parts = [part for part in (base or "").split(",") if part and not part.startswith(drop)]
    parts.append(f"T_CHOICE_LayerMethod={xlights_layer_method(method)}")
    parts.append(f"T_CHECKBOX_Canvas={1 if canvas else 0}")
    if mix is not None:
        parts.append(f"T_SLIDER_EffectLayerMix={max(0, min(100, int(mix)))}")
    if canvas and layers_selected:
        parts.append(f"T_LayersSelected={layers_selected}")
    return ",".join(parts)


def stamp_native_blends(root: ET.Element) -> int:
    """Write blend keys onto effects that do not already carry them.

    The musical bed stamps itself. Spatial effects use Canvas so they
    composite against the selected lower layer instead of replacing it
    with an opaque buffer.
    """
    changed = 0
    for effect in root.iter("Effect"):
        settings = effect.attrib.get("settings") or ""
        if "T_CHOICE_LayerMethod=" in settings:
            continue
        if effect.attrib.get("source") == "HelixMusicalBed":
            continue
        name = effect.attrib.get("name") or ""
        canvas = canvas_for("", name)
        method = "Layered" if canvas else "Normal"
        effect.attrib["settings"] = blend_settings(
            settings,
            method,
            canvas=canvas,
            mix=40 if canvas else None,
            layers_selected="1" if canvas else None,
        )
        changed += 1
    return changed
