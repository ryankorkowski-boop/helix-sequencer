from __future__ import annotations

import re
import math
from pathlib import Path
from typing import TYPE_CHECKING
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    from xlights.xsq_writer import EffectTemplate, XsqIndex


def _legacy():
    from xlights import xsq_writer as legacy

    return legacy


def effect_template_values(root: ET.Element, effect: ET.Element) -> tuple[str | None, str | None]:
    """Resolve native tables before reusing a template on another effect row."""
    legacy = _legacy()
    settings, palette = legacy._effect_settings(effect), legacy._effect_palette(effect)
    ref = effect.get('ref')
    if ref is not None:
        table = root.findall('./EffectDB/Effect')
        if not ref.isdigit() or int(ref) >= len(table):
            raise ValueError('Invalid native EffectDB template reference: ' + ref)
        settings = table[int(ref)].text or ''
    if palette is not None and palette.isdigit():
        table = root.findall('./ColorPalettes/ColorPalette')
        if int(palette) >= len(table):
            raise ValueError('Invalid native palette template reference: ' + palette)
        palette = table[int(palette)].text or ''
    return settings, palette


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
        on.settings, on.palette = effect_template_values(root, first_on)

    if first_ramp is not None:
        ramp.settings, ramp.palette = effect_template_values(root, first_ramp)

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


def materialize_native_effect_tables(root: ET.Element) -> dict[str, int]:
    """Serialize inline Helix templates into native xLights reference tables.

    Settings remain available to legacy readers. Native palette/ref indices,
    existing table order, all targets and every source timestamp are preserved.
    A missing palette retains xLights' white default explicitly.
    """
    elements = root.find('ElementEffects')
    if elements is None:
        return {'settings_added': 0, 'palettes_added': 0, 'effects': 0}
    palette_root = root.find('ColorPalettes')
    if palette_root is None:
        palette_root = ET.SubElement(root, 'ColorPalettes')
    database = root.find('EffectDB')
    if database is None:
        database = ET.SubElement(root, 'EffectDB')
    palettes = [node.text or '' for node in palette_root.findall('ColorPalette')]
    settings = [node.text or '' for node in database.findall('Effect')]
    before_palette, before_settings = len(palettes), len(settings)
    # Table cardinality, rather than unique-value count, determines new indices.
    pmap, smap = {v:i for i,v in enumerate(palettes)}, {v:i for i,v in enumerate(settings)}
    effects = [effect for element in elements if element.get('type') != 'timing'
               for layer in element if layer.tag in {'EffectLayer', 'SubModelEffectLayer'}
               for effect in layer.findall('Effect')]
    if not palettes and any(effect.get('palette') is None for effect in effects):
        # Native missing palettes use table0. Preserve that white default when
        # creating a previously absent table, but keep the attribute absent so
        # the existing explicit neon post-pass can still assign its palette.
        white = 'C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
        pmap[white] = 0
        palettes.append(white)
        ET.SubElement(palette_root, 'ColorPalette').text = white
    next_id = max((int(e.get('id')) for e in effects if e.get('id', '').isdigit()), default=0) + 1
    for effect in effects:
        ref = effect.get('ref')
        if ref is None:
            value = effect.get('settings', '')
            if value not in smap:
                smap[value] = len(settings)
                settings.append(value)
                ET.SubElement(database, 'Effect').text = value
            effect.set('ref', str(smap[value]))
        elif not ref.isdigit() or int(ref) >= len(settings):
            raise ValueError('Invalid native EffectDB reference: ' + ref)
        value = effect.get('palette')
        if value is None:
            pass
        elif not value.isdigit():
            if value not in pmap:
                pmap[value] = len(palettes)
                palettes.append(value)
                ET.SubElement(palette_root, 'ColorPalette').text = value
            effect.set('palette', str(pmap[value]))
        elif int(value) >= len(palettes):
            raise ValueError('Invalid native ColorPalettes reference: ' + value)
        if effect.get('id') is None:
            effect.set('id', str(next_id))
            next_id += 1
    next_node = root.find('nextid')
    if next_node is None:
        next_node = ET.SubElement(root, 'nextid')
    next_node.text = str(next_id)
    return dict(settings_added=len(settings)-before_settings,
                palettes_added=len(palettes)-before_palette, effects=len(effects))


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


def set_sequence_duration(root: ET.Element, duration_seconds: float) -> int:
    """Bind the media sequence length to decoded audio, never the old template.

    xLights uses this head value for FSEQ/preview length even when editable
    effects continue beyond it. Retain the existing writer contract of nearest-millisecond precision.
    """
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError('Media duration requires finite positive seconds')
    duration_ms = max(1, round(duration_seconds * 1000))
    namespace = root.tag.rpartition('}')[0] + '}' if '}' in root.tag else ''
    head = root.find(namespace + 'head')
    if head is None:
        head = ET.SubElement(root, namespace + 'head')
    for name, value in (('sequenceDuration', f'{duration_ms / 1000:.3f}'),
                        ('sequenceType', 'Media')):
        element = head.find(namespace + name)
        if element is None:
            element = ET.SubElement(head, namespace + name)
        element.text = value
    return duration_ms


def bound_media_effects(root: ET.Element, duration_ms: int) -> dict[str, int]:
    """Bound generated lighting/timing intervals to the actual audio clock."""
    if duration_ms < 1:
        raise ValueError('Media duration must be positive')
    counts = {'trimmed': 0, 'removed': 0}
    for parent in root.iter():
        for effect in list(parent):
            if (not isinstance(effect.tag, str) or effect.tag.rsplit('}', 1)[-1] != 'Effect'
                    or 'startTime' not in effect.attrib or 'endTime' not in effect.attrib):
                continue
            start, end = int(effect.get('startTime')), int(effect.get('endTime'))
            lo, hi = max(0, start), min(duration_ms, end)
            if hi <= lo:
                parent.remove(effect)
                counts['removed'] += 1
            elif (lo, hi) != (start, end):
                effect.set('startTime', str(lo))
                effect.set('endTime', str(hi))
                counts['trimmed'] += 1
    return counts


def find_root_child(root: ET.Element, suffix: str) -> ET.Element | None:
    for child in list(root):
        if child.tag.endswith(suffix):
            return child
    return None
