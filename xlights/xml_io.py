from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    from xlights.xsq_writer import EffectTemplate, XsqIndex


def _legacy():
    from xlights import xsq_writer as legacy

    return legacy


def load_xsq(path: Path) -> "XsqIndex":
    legacy = _legacy()
    try:
        tree = ET.parse(path)
    except Exception as exc:
        legacy.die(f"Failed to parse XSQ XML: {path.name}\n{exc}")
    root = tree.getroot()

    elements: dict[str, ET.Element] = {}
    for el in legacy._find_any(root, "Element"):
        name = legacy._get_attr(el, ["name", "Name"])
        if not name:
            continue
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type == "timing":
            continue
        has_layer = any(child.tag.endswith("EffectLayer") or child.tag.endswith("Layer") for child in list(el))
        has_effect = any(child.tag.endswith("Effect") for child in el.iter())
        if has_layer or has_effect:
            elements[name.strip()] = el

    on = legacy.EffectTemplate(settings=None, palette=None)
    ramp = legacy.EffectTemplate(settings=None, palette=None)

    first_on = None
    first_ramp = None
    for eff in legacy._find_any(root, "Effect"):
        effect_name = legacy._effect_name(eff).strip().lower()
        if first_on is None and effect_name == "on":
            first_on = eff
        if first_ramp is None and effect_name == "ramp":
            first_ramp = eff
        if first_on is not None and first_ramp is not None:
            break

    if first_on is not None:
        on.settings = legacy._effect_settings(first_on)
        on.palette = legacy._effect_palette(first_on)

    if first_ramp is not None:
        ramp.settings = legacy._effect_settings(first_ramp)
        ramp.palette = legacy._effect_palette(first_ramp)

    return legacy.XsqIndex(tree=tree, root=root, elements=elements, on_tpl=on, ramp_tpl=ramp)


def ensure_layer(el: ET.Element, layer_name: str) -> ET.Element:
    legacy = _legacy()
    for child in list(el):
        if child.tag.endswith("EffectLayer") or child.tag.endswith("Layer"):
            name = legacy._get_attr(child, ["name", "Name"])
            if name and name.strip() == layer_name:
                return child
    for child in list(el):
        if child.tag.endswith("EffectLayer") or child.tag.endswith("Layer"):
            name = (legacy._get_attr(child, ["name", "Name"]) or "").strip()
            if not name:
                child.attrib["name"] = layer_name
                child.attrib.setdefault("visible", "1")
                return child
    layer_tag = None
    for child in list(el):
        if child.tag.endswith("EffectLayer"):
            layer_tag = child.tag
            break
        if child.tag.endswith("Layer"):
            layer_tag = child.tag
            break
    if layer_tag is None:
        layer_tag = "EffectLayer"
    layer = ET.Element(layer_tag)
    layer.attrib["name"] = layer_name
    layer.attrib.setdefault("visible", "1")
    el.append(layer)
    return layer


def clear_effects(el: ET.Element, mode: str, layer_name: str) -> None:
    legacy = _legacy()
    layers = legacy._iter_layers(el)
    if mode == "all":
        for layer in layers:
            for eff in list(layer):
                if eff.tag.endswith("Effect"):
                    layer.remove(eff)
        return
    for layer in layers:
        name = legacy._get_attr(layer, ["name", "Name"]) or ""
        if name.strip() == layer_name:
            for eff in list(layer):
                if eff.tag.endswith("Effect"):
                    layer.remove(eff)
            return


def add_effect(layer: ET.Element, start_ms: int, end_ms: int, name: str, tpl: "EffectTemplate") -> ET.Element:
    effect_tag = None
    for child in list(layer):
        if child.tag.endswith("Effect"):
            effect_tag = child.tag
            break
    if effect_tag is None:
        effect_tag = "Effect"

    start_ms = int(start_ms)
    end_ms = int(max(start_ms + 1, end_ms))

    effect = ET.Element(effect_tag)
    effect.attrib["name"] = name
    effect.attrib["startTime"] = str(start_ms)
    effect.attrib["endTime"] = str(end_ms)

    if tpl.settings is not None:
        effect.attrib["settings"] = tpl.settings
    if tpl.palette is not None:
        effect.attrib["palette"] = tpl.palette

    layer.append(effect)
    return effect


def replace_audio_references(root: ET.Element, new_audio: Path) -> int:
    new_name = new_audio.name
    changed = 0
    pattern = re.compile(r'[^\\/\"]+\.(wav|mp3|flac|ogg|m4a)', re.IGNORECASE)

    for el in root.iter():
        tag_name = el.tag.rsplit("}", 1)[-1].lower() if isinstance(el.tag, str) else ""
        handled_text = False

        if tag_name == "mediafile":
            current = (el.text or "").strip()
            if current != new_name:
                el.text = new_name
                changed += 1
            handled_text = True

        for key in list(el.attrib.keys()):
            value = el.attrib[key]
            if not isinstance(value, str):
                continue
            if pattern.search(value):
                new_value, replacements = pattern.subn(new_name, value)
                if replacements:
                    el.attrib[key] = new_value
                    changed += replacements
        if not handled_text and el.text and pattern.search(el.text):
            new_text, replacements = pattern.subn(new_name, el.text)
            if replacements:
                el.text = new_text
                changed += replacements
    return changed


def find_root_child(root: ET.Element, suffix: str) -> ET.Element | None:
    for child in list(root):
        if child.tag.endswith(suffix):
            return child
    return None
