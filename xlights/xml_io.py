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

    from xlights.layout_sync import collect_effect_elements

    elements = collect_effect_elements(root)

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
        on.settings = legacy._effect_settings(first_on, root)
        on.palette = legacy._effect_palette(first_on, root)

    if first_ramp is not None:
        ramp.settings = legacy._effect_settings(first_ramp, root)
        ramp.palette = legacy._effect_palette(first_ramp, root)

    return legacy.XsqIndex(tree=tree, root=root, elements=elements, on_tpl=on, ramp_tpl=ramp)


def _is_effect_layer(tag: str) -> bool:
    return tag.endswith("EffectLayer") or (tag.endswith("Layer") and not tag.endswith("SubModelEffectLayer"))


def ensure_layer(el: ET.Element, layer_name: str) -> ET.Element:
    legacy = _legacy()
    for child in list(el):
        if isinstance(child.tag, str) and _is_effect_layer(child.tag):
            name = legacy._get_attr(child, ["name", "Name"])
            if name and name.strip() == layer_name:
                return child
    for child in list(el):
        if isinstance(child.tag, str) and _is_effect_layer(child.tag):
            name = (legacy._get_attr(child, ["name", "Name"]) or "").strip()
            if not name:
                child.attrib["name"] = layer_name
                child.attrib.setdefault("visible", "1")
                return child
    layer_tag = None
    for child in list(el):
        if isinstance(child.tag, str) and child.tag.endswith("EffectLayer") and not child.tag.endswith("SubModelEffectLayer"):
            layer_tag = child.tag
            break
        if isinstance(child.tag, str) and _is_effect_layer(child.tag):
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
    layers = [layer for layer in legacy._iter_layers(el) if _is_effect_layer(layer.tag)]
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


def _index_text(value: str | None) -> int | None:
    raw = (value or "").strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)


def _direct_children(parent: ET.Element, suffix: str) -> list[ET.Element]:
    return [child for child in list(parent) if isinstance(child.tag, str) and child.tag.endswith(suffix)]


def _ensure_library(root: ET.Element, tag: str) -> ET.Element:
    found = find_root_child(root, tag)
    if found is not None:
        return found
    library = ET.Element(tag)
    insert_at = len(list(root))
    for index, child in enumerate(list(root)):
        if isinstance(child.tag, str) and child.tag.endswith("ElementEffects"):
            insert_at = index
            break
    root.insert(insert_at, library)
    return library


def effect_db_entries(root: ET.Element) -> list[ET.Element]:
    library = find_root_child(root, "EffectDB")
    if library is None:
        return []
    return _direct_children(library, "Effect")


def color_palette_entries(root: ET.Element) -> list[ET.Element]:
    library = find_root_child(root, "ColorPalettes")
    if library is None:
        return []
    return _direct_children(library, "ColorPalette")


def effect_settings_text(eff: ET.Element, root: ET.Element | None = None) -> str | None:
    """Return the effect setting string, resolving ``ref`` through EffectDB when present."""

    ref = _index_text(eff.attrib.get("ref", eff.attrib.get("Ref")))
    if ref is not None and root is not None:
        entries = effect_db_entries(root)
        if 0 <= ref < len(entries):
            return (entries[ref].text or "").strip()
        return None
    direct = None
    for key in ("settings", "Settings", "data", "Data"):
        if key in eff.attrib:
            direct = eff.attrib[key]
            break
    if direct is None:
        return None
    return direct.strip()


def effect_palette_text(eff: ET.Element, root: ET.Element | None = None) -> str | None:
    """Return the palette string, resolving a numeric ``palette`` index through ColorPalettes."""

    raw = None
    for key in ("palette", "Palette"):
        if key in eff.attrib:
            raw = eff.attrib[key]
            break
    if raw is None:
        return None
    index = _index_text(raw)
    if index is None:
        return raw.strip()
    if root is None:
        return None
    entries = color_palette_entries(root)
    if 0 <= index < len(entries):
        return (entries[index].text or "").strip()
    return None


def intern_effect_settings(root: ET.Element, settings: str) -> str:
    """Return the EffectDB index for ``settings``, appending an entry when needed."""

    text = settings.strip()
    library = _ensure_library(root, "EffectDB")
    entries = _direct_children(library, "Effect")
    for index, entry in enumerate(entries):
        if (entry.text or "").strip() == text:
            return str(index)
    entry = ET.SubElement(library, "Effect")
    entry.text = text
    return str(len(entries))


def intern_color_palette(root: ET.Element, palette: str) -> str:
    """Return the ColorPalettes index for ``palette``, appending an entry when needed."""

    text = palette.strip()
    existing = _index_text(text)
    entries = color_palette_entries(root)
    if existing is not None and 0 <= existing < len(entries):
        return str(existing)
    library = _ensure_library(root, "ColorPalettes")
    entries = _direct_children(library, "ColorPalette")
    for index, entry in enumerate(entries):
        if (entry.text or "").strip() == text:
            return str(index)
    entry = ET.SubElement(library, "ColorPalette")
    entry.text = text
    return str(len(entries))


def unresolved_effect_references(root: ET.Element) -> list[str]:
    """List Effect rows whose ``ref`` or ``palette`` index does not resolve."""

    errors: list[str] = []
    settings = effect_db_entries(root)
    palettes = color_palette_entries(root)
    for effect in root.iter():
        if not (isinstance(effect.tag, str) and effect.tag.endswith("Effect")):
            continue
        if effect.get("label") and "name" not in effect.attrib and "ref" not in effect.attrib:
            continue
        ref = _index_text(effect.attrib.get("ref"))
        if "ref" in effect.attrib and (ref is None or ref >= len(settings)):
            errors.append(f"unresolved ref={effect.attrib.get('ref')!r} on {effect.attrib.get('name', '')}")
        elif ref is not None and effect_settings_text(effect, root) is None:
            errors.append(f"empty ref={ref} on {effect.attrib.get('name', '')}")
        palette = effect.attrib.get("palette")
        palette_index = _index_text(palette)
        if palette is not None and palette_index is not None and palette_index >= len(palettes):
            errors.append(f"unresolved palette={palette!r} on {effect.attrib.get('name', '')}")
        elif palette is not None and effect_palette_text(effect, root) is None:
            errors.append(f"unresolved palette={palette!r} on {effect.attrib.get('name', '')}")
    return errors


def add_effect(
    layer: ET.Element,
    start_ms: int,
    end_ms: int,
    name: str,
    tpl: "EffectTemplate",
    root: ET.Element | None = None,
) -> ET.Element:
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

    if root is not None:
        if tpl.settings is not None:
            effect.attrib["ref"] = intern_effect_settings(root, tpl.settings)
        if tpl.palette is not None:
            effect.attrib["palette"] = intern_color_palette(root, tpl.palette)
    else:
        if tpl.settings is not None:
            effect.attrib["settings"] = tpl.settings
        if tpl.palette is not None:
            effect.attrib["palette"] = tpl.palette

    layer.append(effect)
    return effect


def apply_sequence_duration(root: ET.Element, duration_s: float) -> dict[str, float | int]:
    """Set ``<head><sequenceDuration>`` and keep effects and timing marks inside it.

    xLights stores ``sequenceDuration`` in seconds. Effect and timing-mark
    ``startTime`` / ``endTime`` values are milliseconds. Marks that begin at or
    after the new end are removed. Marks that cross the end are clipped.
    """

    duration = float(duration_s)
    if duration <= 0:
        raise ValueError(f"sequence duration must be positive, got {duration_s}")
    duration_ms = max(1, int(round(duration * 1000.0)))
    head = find_root_child(root, "head")
    if head is None:
        head = ET.Element("head")
        root.insert(0, head)
    duration_node = None
    for child in list(head):
        if child.tag.endswith("sequenceDuration"):
            duration_node = child
            break
    if duration_node is None:
        duration_node = ET.SubElement(head, "sequenceDuration")
    duration_node.text = f"{duration:.3f}"

    parents: dict[int, ET.Element] = {}
    for parent in root.iter():
        for child in list(parent):
            parents[id(child)] = parent

    def owning_element(node: ET.Element) -> ET.Element | None:
        current: ET.Element | None = node
        while current is not None:
            if isinstance(current.tag, str) and current.tag.endswith("Element"):
                return current
            current = parents.get(id(current))
        return None

    clipped = 0
    removed = 0
    timing_clipped = 0
    timing_removed = 0
    for effect in list(root.iter()):
        if not (isinstance(effect.tag, str) and effect.tag.endswith("Effect")):
            continue
        start_raw = effect.attrib.get("startTime", effect.attrib.get("StartTime"))
        end_raw = effect.attrib.get("endTime", effect.attrib.get("EndTime"))
        if start_raw is None or end_raw is None:
            continue
        try:
            start_ms = int(round(float(start_raw)))
            end_ms = int(round(float(end_raw)))
        except ValueError:
            continue
        owner = owning_element(effect)
        owner_type = ((owner.attrib.get("type") or owner.attrib.get("Type") or "") if owner is not None else "").lower()
        is_timing = owner_type == "timing"
        if start_ms >= duration_ms or end_ms <= start_ms:
            parent = parents.get(id(effect))
            if parent is not None:
                parent.remove(effect)
                if is_timing:
                    timing_removed += 1
                else:
                    removed += 1
            continue
        if end_ms > duration_ms:
            end_key = "endTime" if "endTime" in effect.attrib or "EndTime" not in effect.attrib else "EndTime"
            effect.attrib[end_key] = str(duration_ms)
            if is_timing:
                timing_clipped += 1
            else:
                clipped += 1
        if start_ms < 0:
            start_key = "startTime" if "startTime" in effect.attrib or "StartTime" not in effect.attrib else "StartTime"
            effect.attrib[start_key] = "0"
    return {
        "sequence_duration": round(duration, 3),
        "duration_ms": duration_ms,
        "clipped": clipped,
        "removed": removed,
        "timing_clipped": timing_clipped,
        "timing_removed": timing_removed,
    }


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
