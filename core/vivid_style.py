"""Vivid show style: bright AC banks and saturated RGB on black.

The musical bed stays available. This pass removes it unless asked to keep
it, because an always-on dim wash reads as a white or gray field. AC props
are driven to full brightness with chases and alternating banks. RGB props
use a two- or three-colour saturated palette that changes by section, with
instant attack and a short decay. White is an occasional accent.

Nothing here is tuned to one song. Timing comes from the effects already
in the sequence.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from xlights.layer_blend import blend_settings


# Fully saturated. White is not in the rotating set.
SECTION_PALETTES = (
    ("#FF2BD6", "#00F0FF", "#FFE600"),
    ("#FF2200", "#FF8A00", "#39E7FF"),
    ("#39FF14", "#FF2BD6", "#7C4DFF"),
    ("#2266FF", "#FF3D8A", "#5CFFD1"),
)
WHITE = "#FFFFFF"
AC_BULBS = ("#FF0040", "#00F0FF", "#FFE600", "#FF2BD6", "#39FF14", "#4466FF")


def palette_text(colors: tuple[str, ...] | list[str]) -> str:
    parts = []
    for index, color in enumerate(colors, start=1):
        parts.append(f"C_BUTTON_Palette{index}={color}")
        parts.append(f"C_CHECKBOX_Palette{index}=1")
    return ",".join(parts)


def append_show_grove(layout_path: Path, output_path: Path, *, spirals: int = 24, dna_pairs: int = 8) -> dict:
    """Add spiral trees and DNA sculptures after the existing channel map.

    Existing models keep their start channels. The real 256-channel house
    file should not be passed here.
    """
    from tools.layout_bench.generate_layouts import helix, spiral

    from core.model_parser import parse_layout

    layout = parse_layout(layout_path)
    end = 0
    xs, ys, zs = [], [], []
    for model in layout.models.values():
        if model.is_submodel or not model.start_channel:
            continue
        per = 3 if model.is_rgb_capable() else 1
        end = max(end, int(model.start_channel) + model.total_pixels * per - 1)
        for point in model.geometry_points or [model.center()]:
            xs.append(point[0]); ys.append(point[1]); zs.append(point[2])
    if not xs:
        xs, ys, zs = [0.0, 1000.0], [0.0, 600.0], [0.0, 40.0]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(200.0, max_x - min_x)
    span_y = max(160.0, max_y - min_y)
    base_z = max(zs)
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models = root.find("models")
    if models is None:
        models = ET.SubElement(root, "models")
    groups = root.find("modelGroups")
    if groups is None:
        groups = ET.SubElement(root, "modelGroups")
    channel = end + 1
    spiral_names: list[str] = []
    dna_names: list[str] = []
    columns = 8
    rows = max(1, (spirals + columns - 1) // columns)
    for index in range(spirals):
        column = index % columns
        row = index // columns
        cx = min_x + span_x * (column + 0.5) / columns
        cy = min_y + span_y * (row + 0.15) / max(1, rows)
        points = spiral(cx, cy, span_x * 0.035, span_y * 0.42, 4.0 + (index % 3), z=base_z + 10 + row * 15, steps=72)
        name = f"HX Vivid Spiral {index + 1:02d}"
        pixels = len(points)
        _append_rgb(models, name, "Tree 360", points, pixels, AC_BULBS[index % len(AC_BULBS)], channel, {"parm1": "1", "parm2": str(pixels)})
        spiral_names.append(name)
        channel += pixels * 3
    for index in range(dna_pairs):
        cx = min_x + span_x * ((index % 4) + 0.5) / 4
        cy = min_y + span_y * (0.55 + 0.35 * (index // 4))
        for strand, phase, tint in ((0, 0.0, "#00F0FF"), (1, 3.14159, "#FF2BD6")):
            points = helix(cx, cy, span_x * 0.03, span_y * 0.45, 5.0, phase, steps=80)
            name = f"HX Vivid DNA {index + 1:02d} {'A' if strand == 0 else 'B'}"
            pixels = len(points)
            _append_rgb(models, name, "Single Line", points, pixels, tint, channel, {"parm1": "1", "parm2": str(pixels)})
            dna_names.append(name)
            channel += pixels * 3
    _append_group(groups, "HX Vivid Spirals", spiral_names)
    _append_group(groups, "HX Vivid DNA", dna_names)
    _append_group(groups, "HX Vivid Grove", spiral_names + dna_names)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return {"spirals": len(spiral_names), "dna": len(dna_names), "next_channel": channel}


def is_performance_prop(name: str) -> bool:
    """Band, singing-face and drummer props keep the effects the sequencer wrote."""
    text = name.lower().replace("_", " ")
    if "singing face" in text or "/mouth" in text or "/eyes" in text:
        return True
    if "drummer" in text or "snowman" in text:
        return True
    return any(token in text for token in ("bassist", "guitarist", "keyboardist", "lead singer", "harmony singer"))


def apply_vivid_style(
    xsq_path: Path,
    layout_path: Path | None = None,
    *,
    keep_bed: bool = False,
    sections: list[dict] | None = None,
    features: object | None = None,
) -> dict:
    tree = ET.parse(xsq_path)
    root = tree.getroot()
    if not keep_bed:
        _strip_bed(root)
    duration = _duration_ms(root)
    song_sections = sections or _sections_from_sequence(root, duration)
    palette_index, palette_for = _palettes_for_layout(root, layout_path, song_sections, features)
    hits = _hit_times(root)
    effects_root = root.find("ElementEffects")
    if effects_root is None:
        return {"ac_models": 0, "rgb_models": 0, "added": 0}
    kind = _model_kinds(layout_path) if layout_path and Path(layout_path).exists() else {}
    positions = _positions(layout_path) if layout_path and Path(layout_path).exists() else {}
    added = 0
    ac_names: list[str] = []
    rgb_names: list[str] = []
    for element in list(effects_root.findall("Element")):
        if (element.attrib.get("type") or "").lower() == "timing":
            continue
        name = element.attrib.get("name") or ""
        if kind.get(name) == "group" or is_performance_prop(name):
            continue
        ac = kind.get(name, "rgb") == "ac"
        (ac_names if ac else rgb_names).append(name)
    if layout_path and Path(layout_path).exists():
        present = {element.attrib.get("name") for element in effects_root.findall("Element")}
        display = root.find("DisplayElements")
        if display is None:
            display = ET.SubElement(root, "DisplayElements")
        shown = {element.attrib.get("name") for element in display.findall("Element")}
        for name, model_kind in kind.items():
            if model_kind == "group" or name in shown:
                continue
            ET.SubElement(display, "Element", {"collapsed": "0", "type": "model", "name": name, "visible": "1"})
            shown.add(name)
        for name, model_kind in kind.items():
            if name in present or model_kind == "group" or is_performance_prop(name):
                continue
            element = ET.SubElement(effects_root, "Element", {"type": "model", "name": name})
            ET.SubElement(element, "EffectLayer")
            if model_kind == "ac":
                ac_names.append(name)
            else:
                rgb_names.append(name)
    ac_names = _ordered(ac_names, positions, "x")
    rgb_names = _ordered(rgb_names, positions, "x")
    rgb_by_z = _ordered(list(rgb_names), positions, "z")
    beats = _beats(hits, duration)
    added += _ac_motion(effects_root, ac_names, duration, beats, palette_for)
    added += _rgb_motion(effects_root, rgb_names, rgb_by_z, duration, beats, palette_for)
    added += _group_motion(effects_root, _chase_groups(layout_path, kind), duration, beats, song_sections, palette_for)
    display = root.find("DisplayElements")
    effects_node = root.find("ElementEffects")
    if display is not None and effects_node is not None:
        children = list(root)
        if children.index(display) > children.index(effects_node):
            root.remove(display)
            root.insert(list(root).index(effects_node), display)
    if layout_path and Path(layout_path).exists():
        for index, name in enumerate(models_without_effects(root, layout_path)):
            if is_performance_prop(name):
                continue
            start = beats[index % len(beats)] if beats else 0
            if _add_on(_vivid_layer(effects_root, name), start, min(duration, start + 140), palette_for(name, start)):
                added += 1
    tree.write(xsq_path, encoding="utf-8", xml_declaration=True)
    return {
        "ac_models": len(ac_names),
        "rgb_models": len(rgb_names),
        "added": added,
        "bed_kept": keep_bed,
        "hits": len(hits),
        "strategy": getattr(palette_for, "strategy", ""),
    }


def _append_rgb(models: ET.Element, name: str, display: str, points: list, pixels: int, tint: str, start: int, extra: dict) -> None:
    x, y, z = points[0]
    attrs = {
        "name": name,
        "DisplayAs": display,
        "StringType": "RGB Nodes",
        "CustomColor": tint,
        "TagColour": tint,
        "Antialias": "1",
        "PixelSize": "2",
        "Transparency": "0",
        "LayoutGroup": "Default",
        "Dir": "L",
        "StartSide": "B",
        "WorldPosX": f"{x:.4f}",
        "WorldPosY": f"{y:.4f}",
        "WorldPosZ": f"{z:.4f}",
        "ScaleX": "1.0000",
        "ScaleY": "1.0000",
        "ScaleZ": "1.0000",
        "versionNumber": "7",
        "StartChannel": str(start),
        "NumPoints": str(len(points)),
        "PointData": ",".join(f"{px:.3f},{py:.3f},{pz:.3f}" for px, py, pz in points),
        "parm1": extra.get("parm1", "1"),
        "parm2": extra.get("parm2", str(pixels)),
    }
    ET.SubElement(models, "model", attrs).append(ET.Element("ControllerConnection", {"Protocol": "ws2811"}))


def _append_group(groups: ET.Element, name: str, members: list[str]) -> None:
    if not members:
        return
    ET.SubElement(groups, "modelGroup", {"name": name, "models": ",".join(members), "layout": "minimalGrid", "GridSize": "400", "LayoutGroup": "Default"})


def _strip_bed(root: ET.Element) -> None:
    for parent in list(root.iter()):
        for child in list(parent):
            if child.tag == "Effect" and child.attrib.get("source") == "HelixMusicalBed":
                parent.remove(child)
    for parent in list(root.iter()):
        for child in list(parent):
            if child.tag == "EffectLayer" and child.attrib.get("name") == "Helix Bed" and not list(child):
                parent.remove(child)


def _duration_ms(root: ET.Element) -> int:
    text = root.findtext("./head/sequenceDuration") or "30"
    try:
        return max(1000, int(float(text) * 1000))
    except ValueError:
        return 30000


def vivid_colors() -> tuple[str, ...]:
    return tuple(color for palette in SECTION_PALETTES for color in palette)


def _ensure_palettes(root: ET.Element) -> dict[int, str]:
    palettes = root.find("ColorPalettes")
    if palettes is None:
        palettes = ET.Element("ColorPalettes")
        root.insert(0, palettes)
    index_of: dict[int, str] = {}
    for index, color in enumerate(vivid_colors()):
        index_of[index] = _palette_index(palettes, palette_text((color,)))
    # Keep occasional white highlights without creating white-only effects.
    # xLights chooses from enabled colors; a white-only palette fails the
    # packaged Windows color-quality gate even for a short accent.
    index_of[-1] = _palette_index(palettes, palette_text((WHITE, "#FF2BD6", "#00F0FF")))
    return index_of


def _color_index(name: str, section: int) -> int:
    return (sum(ord(char) for char in name) + section * 3) % len(vivid_colors())


def _palette_index(palettes: ET.Element, text: str) -> str:
    for index, palette in enumerate(list(palettes)):
        if (palette.text or "") == text:
            return str(index)
    element = ET.SubElement(palettes, "ColorPalette")
    element.text = text
    return str(len(list(palettes)) - 1)


def _beats(hits: list[int], duration: int) -> list[int]:
    """Phrase beats only. A gap longer than 700 ms is silence, not a filled clock."""
    return [hit for hit in hits if 0 <= hit < duration]


def _sections_from_sequence(root: ET.Element, duration: int) -> list[dict]:
    found = []
    effects_root = root.find("ElementEffects")
    if effects_root is not None:
        for element in effects_root.findall("Element"):
            if (element.attrib.get("type") or "").lower() != "timing":
                continue
            if (element.attrib.get("name") or "").lower() not in {"sections", "phrases", "structure"}:
                continue
            for effect in element.findall(".//Effect"):
                label = effect.attrib.get("label") or effect.attrib.get("name") or "GROOVE"
                try:
                    start = int(float(effect.attrib.get("startTime", "0") or 0))
                    end = int(float(effect.attrib.get("endTime", "0") or 0))
                except ValueError:
                    continue
                if end > start:
                    found.append({"label": label, "start_ms": start, "end_ms": end, "energy": 0.6})
    if found:
        return sorted(found, key=lambda item: item["start_ms"])
    return [{"label": "GROOVE", "start_ms": 0, "end_ms": duration, "energy": 0.6}]


def _section_label(start: int, sections: list[dict]) -> str:
    for section in sections:
        if section["start_ms"] <= start < section["end_ms"]:
            return str(section["label"])
    return str(sections[-1]["label"]) if sections else "GROOVE"


def _palettes_for_layout(root: ET.Element, layout_path: Path | None, sections: list[dict], features: object | None):
    from helix_style.palette_chooser import STRATEGIES, SongFeatures, choose_palette

    if features is None:
        features = SongFeatures(
            tempo_bpm=120,
            intensity=0.7,
            sections=sections,
            lyrics=["lights"],
            key="C major",
        )
    identity = Path(layout_path).name if layout_path else "layout"
    strategy = STRATEGIES[sum(ord(char) for char in identity) % len(STRATEGIES)]
    decision = choose_palette(features, strategy)
    palettes = root.find("ColorPalettes")
    if palettes is None:
        palettes = ET.Element("ColorPalettes")
        root.insert(0, palettes)
    index_of: dict[str, str] = {}

    def install(color: str) -> str:
        if color in index_of:
            return index_of[color]
        index_of[color] = _palette_index(palettes, palette_text((color,)))
        return index_of[color]

    for color in list(decision.palette) + [item for cols in decision.section_palettes.values() for item in cols]:
        install(color)

    def palette_for(name: str, start: int, *, white_accent: bool = False) -> str:
        colors = decision.for_section(_section_label(start, sections)) or decision.palette
        usable = [color for color in colors if color.upper() not in {"#FFFFFF", "#FFF1D0", "#E8F6FF"}] or list(colors)
        chosen = usable[sum(ord(char) for char in name) % len(usable)]
        if white_accent:
            # The highlight must contain white AND a saturated color, never
            # a white-only palette. Previously its label said white accent
            # while the selected palette excluded white entirely.
            return _palette_index(palettes, palette_text(("#FFFFFF", chosen if chosen.upper() != "#FFFFFF" else "#FF2BD6")))
        return install(chosen)

    palette_for.strategy = strategy
    return {}, palette_for


def _hit_times(root: ET.Element) -> list[int]:
    hits = []
    for effect in root.iter("Effect"):
        if effect.attrib.get("source") == "HelixMusicalBed":
            continue
        try:
            start = int(float(effect.attrib.get("startTime", "0") or 0))
            end = int(float(effect.attrib.get("endTime", "0") or 0))
        except ValueError:
            continue
        if end > start:
            hits.append(start)
    return sorted(set(hits))


def _model_kinds(layout_path: Path) -> dict[str, str]:
    from core.model_parser import parse_layout

    layout = parse_layout(layout_path)
    kinds = {name: "group" for name in layout.groups}
    for name, model in layout.models.items():
        if model.is_submodel:
            kinds[name] = "rgb" if model.is_rgb_capable() else "ac"
            continue
        kinds[name] = "rgb" if model.is_rgb_capable() and model.total_pixels > 1 else "ac"
    return kinds


def _positions(layout_path: Path) -> dict[str, tuple[float, float, float]]:
    from core.model_parser import parse_layout

    layout = parse_layout(layout_path)
    positions = {}
    for name, model in layout.models.items():
        positions[name] = model.center()
    for name, group in layout.groups.items():
        members = layout.expand_group_members(name)
        centers = [positions[member] for member in members if member in positions]
        if centers:
            count = float(len(centers))
            positions[name] = (
                sum(point[0] for point in centers) / count,
                sum(point[1] for point in centers) / count,
                sum(point[2] for point in centers) / count,
            )
    return positions


def _ordered(names: list[str], positions: dict[str, tuple[float, float, float]], axis: str) -> list[str]:
    index = {"x": 0, "y": 1, "z": 2}[axis]
    return sorted(names, key=lambda name: (positions.get(name, (0.0, 0.0, 0.0))[index], name))


def _section(start: int, duration: int, sections: int) -> int:
    width = max(1, duration // sections)
    return min(sections - 1, max(0, start // width))


def _restyle_effect(effect: ET.Element, *, name: str, ac: bool, duration: int, palette_index: dict[int, str], sections: int) -> None:
    try:
        start = int(float(effect.attrib.get("startTime", "0") or 0))
        end = int(float(effect.attrib.get("endTime", "0") or 0))
    except ValueError:
        return
    length = max(0, end - start)
    section = _section(start, duration, sections)
    chosen = palette_index[_color_index(name, section)]
    if length >= 700:
        effect.attrib["palette"] = chosen
        if (effect.attrib.get("name") or "") == "On":
            effect.attrib["settings"] = blend_settings(
                "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100",
                "Normal",
            )
        return
    cap = 220 if ac else 140
    effect.attrib["endTime"] = str(start + min(length or cap, cap))
    effect.attrib["palette"] = chosen
    if (effect.attrib.get("name") or "") == "On":
        effect.attrib["settings"] = blend_settings(
            "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=0",
            "Normal",
        )


def _vivid_layer(effects_root: ET.Element, name: str, element_type: str = "model") -> ET.Element:
    """Vivid effects live on their own layer and never share it with sequencer effects."""
    element = None
    for candidate in effects_root.findall("Element"):
        if candidate.attrib.get("name") == name:
            element = candidate
            break
    if element is None:
        element = ET.SubElement(effects_root, "Element", {"type": element_type, "name": name})
    elif element_type == "modelGroup":
        element.attrib["type"] = "modelGroup"
    for layer in element.findall("EffectLayer"):
        if layer.attrib.get("name") == "Helix Vivid":
            return layer
    return ET.SubElement(element, "EffectLayer", {"name": "Helix Vivid"})


def _overlaps(layer: ET.Element, start: int, end: int) -> bool:
    for effect in layer.findall("Effect"):
        try:
            other_start = int(float(effect.attrib.get("startTime", "0") or 0))
            other_end = int(float(effect.attrib.get("endTime", "0") or 0))
        except ValueError:
            continue
        if start < other_end and other_start < end:
            return True
    return False


def _add_on(layer: ET.Element, start: int, end: int, palette: str, *, accent_white: bool = False) -> bool:
    if end <= start or _overlaps(layer, start, end):
        return False
    ET.SubElement(layer, "Effect", {
        "name": "On",
        "startTime": str(start),
        "endTime": str(end),
        "palette": palette,
        "settings": blend_settings(
            "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=0",
            "Normal",
        ),
        "source": "HelixVivid",
        "label": "white accent" if accent_white else "vivid",
    })
    return True


def _ac_motion(effects_root: ET.Element, names: list[str], duration: int, beats: list[int], palette_for) -> int:
    if not names or not beats:
        return 0
    added = 0
    window = max(8, len(names) // 2) if len(names) <= 32 else max(24, len(names) // 5)
    for tick, start in enumerate(beats):
        if start >= duration:
            continue
        end = min(duration, start + 140)
        for offset in range(window):
            name = names[(tick + offset) % len(names)]
            accent = tick % 17 == 0 and offset == 0
            if _add_on(_vivid_layer(effects_root, name), start, end, palette_for(name, start, white_accent=accent), accent_white=accent):
                added += 1
        bank = [name for index, name in enumerate(names) if index % 2 == tick % 2]
        if len(bank) > 24:
            bank = bank[:: max(1, len(bank) // 24)]
        for name in bank:
            if _add_on(_vivid_layer(effects_root, name), start, min(duration, start + 160), palette_for(name, start)):
                added += 1
    return added


def models_without_effects(root: ET.Element, layout_path: Path | None) -> list[str]:
    """Root models with no effect. Submodels share the parent channel buffer."""
    if layout_path is None or not Path(layout_path).exists():
        return []
    from core.model_parser import parse_layout

    layout = parse_layout(layout_path)
    wanted = [name for name, model in layout.models.items() if not model.is_submodel]
    covered: set[str] = set()
    effects_root = root.find("ElementEffects")
    if effects_root is not None:
        for element in effects_root.findall("Element"):
            if element.findall(".//Effect"):
                covered.add(element.attrib.get("name") or "")
    return sorted(name for name in wanted if name not in covered)


def _chase_groups(layout_path: Path | None, kind: dict[str, str]) -> list[str]:
    """Groups small enough that one effect is a motif, not a full-yard blast."""
    if layout_path is None or not Path(layout_path).exists():
        return []
    from core.model_parser import parse_layout

    layout = parse_layout(layout_path)
    model_count = max(1, sum(1 for model in layout.models.values() if not model.is_submodel))
    ceiling = max(6, int(model_count * 0.35))
    chosen = []
    for name, model_kind in kind.items():
        if model_kind != "group":
            continue
        members = [member for member in layout.expand_group_members(name) if member in layout.models and not layout.models[member].is_submodel]
        if any(is_performance_prop(member) for member in members):
            continue
        if 2 <= len(set(members)) <= ceiling:
            chosen.append(name)
    return chosen


def _rgb_motion(effects_root, names, by_z, duration, beats, palette_for) -> int:
    """Light about a quarter of the RGB models on each beat.

    Beats only exist inside active phrases, so the gaps stay black. A beat
    in the 200 ms before a drop is skipped. Existing effects are not moved.
    """
    if not names or not beats:
        return 0
    added = 0
    window = max(1, int(round(len(names) * 0.22)))
    buckets = _buckets(beats, duration)
    for tick, start in enumerate(beats):
        if start >= duration or _in_blackout(start, buckets):
            continue
        end = min(duration, start + 120)
        for offset in range(window):
            name = names[(tick + offset) % len(names)]
            if _add_on(_vivid_layer(effects_root, name), start, end, palette_for(name, start)):
                added += 1
        if by_z:
            name = by_z[(tick * 3) % len(by_z)]
            if _add_on(_vivid_layer(effects_root, name), start, end, palette_for(name, start)):
                added += 1
    return added


def _group_motion(effects_root, names: list[str], duration: int, beats: list[int], sections: list[dict], palette_for) -> int:
    if not names or not beats:
        return 0
    added = 0
    for section in sections:
        start = next((beat for beat in beats if section["start_ms"] <= beat < section["end_ms"]), None)
        if start is None:
            continue
        for name in names:
            if is_performance_prop(name):
                continue
            if _add_on(_vivid_layer(effects_root, name, element_type="modelGroup"), start, min(duration, start + 120), palette_for(name, start)):
                added += 1
    return added


def _in_blackout(start: int, buckets: list[int]) -> bool:
    second = min(len(buckets) - 1, max(0, start // 1000))
    if not _heavy(buckets, second):
        return False
    drop = second * 1000
    return drop - 200 <= start < drop


def _buckets(hits: list[int], duration: int) -> list[int]:
    count = max(1, duration // 1000 + 1)
    buckets = [0] * count
    for hit in hits:
        if 0 <= hit < duration:
            buckets[hit // 1000] += 1
    return buckets


def _heavy(buckets: list[int], second: int) -> bool:
    earlier = [value for value in buckets[max(0, second - 3):second] if value]
    baseline = (sum(earlier) / len(earlier)) if earlier else 1.0
    return buckets[second] >= 4 and buckets[second] > baseline * 2.2


def _blackouts(effects_root: ET.Element, hits: list[int], duration: int) -> int:
    buckets = _buckets(hits, duration)
    windows = []
    for second, count in enumerate(buckets):
        if _heavy(buckets, second):
            start = second * 1000
            windows.append((max(0, start - 200), start))
    if not windows:
        return 0
    removed = 0
    for effect in list(effects_root.iter("Effect")):
        try:
            start = int(float(effect.attrib.get("startTime", "0") or 0))
            end = int(float(effect.attrib.get("endTime", "0") or 0))
        except ValueError:
            continue
        for left, right in windows:
            if start >= left and start < right:
                parent = _parent(effects_root, effect)
                if parent is not None:
                    parent.remove(effect)
                    removed += 1
                break
            if start < left < end:
                effect.attrib["endTime"] = str(left)
    return removed


def _parent(root: ET.Element, child: ET.Element) -> ET.Element | None:
    for parent in root.iter():
        if child in list(parent):
            return parent
    return None
