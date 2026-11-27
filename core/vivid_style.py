"""Add sparse, section-colored responses to source musical cues."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Callable

from core.orchestration_balance import AttackBudget, model_role

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
    report = style_sequence(tree.getroot(), layout_path, keep_bed=keep_bed,
                            sections=sections, features=features)
    tree.write(xsq_path, encoding="utf-8", xml_declaration=True)
    return report


def style_sequence(
    root: ET.Element,
    layout_path: Path | None,
    *,
    keep_bed: bool = False,
    sections: list[dict] | None = None,
    features: object | None = None,
    cue_times: dict[str, list[int]] | None = None,
    quiet_windows: tuple[tuple[int, int], ...] | list[tuple[int, int]] = (),
    layout=None,
    protected_targets: frozenset[str] = frozenset(),
    target_roots: Callable[[str], frozenset[str]] | None = None,
    budget: AttackBudget | None = None,
) -> dict:
    if not keep_bed:
        _strip_bed(root)
    effects_root = root.find("ElementEffects")
    if effects_root is None:
        return {"ac_models": 0, "rgb_models": 0, "added": 0, "bed_kept": keep_bed}

    if layout is None and layout_path and Path(layout_path).is_file():
        from core.model_parser import parse_layout
        layout = parse_layout(layout_path)

    duration = _duration_ms(root)
    song_sections = sections or _sections_from_sequence(root, duration)
    palette_for = _palettes_for_layout(root, layout_path, song_sections, features)
    rows = {element.get("name", ""): element for element in effects_root.findall("Element")
            if element.get("type", "").lower() != "timing"}
    known_groups = layout.groups if layout is not None else {}
    if layout is None:
        names = sorted(name for name, row in rows.items()
                       if name and row.get("type", "").lower() == "model" and "/" not in name)
    else:
        names = layout.root_models()
    names = [name for name in names if name not in protected_targets and not is_performance_prop(name)]
    ac_names = {
        name for name in names if layout is not None
        and (not layout.models[name].is_rgb_capable() or layout.models[name].total_pixels == 1)
    }
    positions = {name: layout.models[name].center() for name in names} if layout is not None else {}
    budget = budget if budget is not None else AttackBudget(len(names))

    if target_roots is None:
        def target_roots(name: str) -> frozenset[str]:
            members = layout.expand_group_members(name) if name in known_groups else [name]
            return frozenset(member.split("/", 1)[0] for member in members)

    occupied: dict[str, list[tuple[int, int]]] = defaultdict(list)
    observed_hits: set[int] = set()
    for name, element in rows.items():
        footprint = target_roots(name)
        for effect in element.findall(".//Effect"):
            source = effect.get("source")
            if source == "HelixMusicalBed":
                continue
            try:
                start, end = int(effect.get("startTime", "")), int(effect.get("endTime", ""))
            except ValueError:
                continue
            if end <= start:
                continue
            if source != "HelixVivid" and not any(is_performance_prop(member) for member in footprint):
                observed_hits.add(start)
            for member in footprint:
                occupied[member].append((start, end))

    available_cues = cue_times if cue_times is not None else {"accent": sorted(observed_hits)}
    candidates = _accent_cues(song_sections, available_cues)
    routes = {
        role: _spatial_route([name for name in names if model_role(name) == role], positions)
        for role in _ACCENT_ROLES
    }
    cursors: dict[str, int] = defaultdict(int)
    added = 0
    last_cue = -1000
    last_white = -8000
    for start, cue, part, section_end, spacing in candidates:
        end = min(duration, section_end, start + _ACCENT_DURATION[cue])
        if start < 0 or end - start < 60 or start - last_cue < spacing:
            continue
        if any(start < right and left < end for left, right in quiet_windows):
            continue
        for role in _ACCENT_TARGETS[cue]:
            route = routes[role]
            for offset in range(len(route)):
                index = (cursors[role] + offset) % len(route)
                name = route[index]
                if any(start < right and left < end for left, right in occupied[name]):
                    continue
                if not budget.take((name,), start, part):
                    break
                white_accent = cue == "impact" and name in ac_names and start - last_white >= 8000
                element = rows.get(name)
                if element is None:
                    element = ET.SubElement(effects_root, "Element", {"type": "model", "name": name})
                    rows[name] = element
                layer = element.find("EffectLayer[@name='Helix Vivid']")
                if layer is None:
                    layer = ET.SubElement(element, "EffectLayer", {"name": "Helix Vivid"})
                _add_on(layer, start, end, palette_for(name, start, white_accent=white_accent),
                        cue=cue, accent_white=white_accent)
                occupied[name].append((start, end))
                if white_accent:
                    last_white = start
                last_cue = start
                cursors[role] = index + 1
                added += 1
                break
            if last_cue == start:
                break
    return {"ac_models": len(ac_names), "rgb_models": len(names) - len(ac_names),
            "added": added, "bed_kept": keep_bed, "hits": len(candidates),
            "strategy": palette_for.strategy}


_ACCENT_TARGETS = {
    "melody": ("arch", "matrix", "hero", "fill", "house"),
    "bass": ("hero", "house", "fill", "arch", "matrix"),
    "build": ("house", "hero", "arch", "fill", "matrix"),
    "impact": ("hero", "house", "matrix", "arch", "fill"),
    "accent": ("arch", "hero", "house", "matrix", "fill"),
}
_ACCENT_ROLES = ("arch", "matrix", "hero", "fill", "house")
_ACCENT_DURATION = {"melody": 180, "bass": 145, "build": 320, "impact": 220, "accent": 145}


def _accent_cues(sections: list[dict], cue_times: dict[str, list[int]]) -> list[tuple[int, str, str, int, int]]:
    """Prefer phrase detail in verses and reserve impacts for section arrivals."""
    plans = {
        "INTRO": (("melody",), 660),
        "VERSE": (("melody", "bass"), 430),
        "PRECHORUS": (("build", "melody"), 340),
        "BRIDGE": (("melody",), 520),
        "CHORUS": (("impact", "melody", "bass"), 300),
        "OUTRO": (("melody",), 650),
    }
    selected = []
    for section in sections:
        label = section["label"].upper()
        part = {"GROOVE": "VERSE", "BUILD": "PRECHORUS", "DROP": "CHORUS"}.get(label, label)
        cues, spacing = plans.get(part, (("melody",), 500))
        starts = {}
        for cue in (*cues, "accent"):
            for start in cue_times.get(cue, ()):
                if section["start_ms"] <= start < section["end_ms"]:
                    if cue == "impact" and start > section["start_ms"] + 850:
                        continue
                    starts.setdefault(start, cue)
                    if cue == "impact":
                        break
        # A nearby release or build takes precedence over a less distinct hit.
        structural = {start for start, cue in starts.items() if cue in {"impact", "build"}}
        for start, cue in sorted(starts.items()):
            if cue not in {"impact", "build"} and any(abs(start - anchor) < spacing for anchor in structural):
                continue
            selected.append((start, cue, part, section["end_ms"], spacing))
    return sorted(selected)


def _spatial_route(names: list[str], positions: dict) -> list[str]:
    if len(names) < 2 or not positions:
        return sorted(names)
    axis = max(range(3), key=lambda i: max(positions[n][i] for n in names) - min(positions[n][i] for n in names))
    ordered = sorted(names, key=lambda name: (positions[name][axis], name))
    return ordered + ordered[-2:0:-1]


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
        return max(0, int(float(text) * 1000))
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
    return palette_for


def _add_on(layer: ET.Element, start: int, end: int, palette: str, *, cue: str, accent_white: bool) -> None:
    levels = (15, 78) if cue == "build" else (100, 0)
    ET.SubElement(layer, "Effect", {
        "name": "On",
        "startTime": str(start),
        "endTime": str(end),
        "palette": palette,
        "settings": blend_settings(
            f"E_TEXTCTRL_Eff_On_Start={levels[0]},E_TEXTCTRL_Eff_On_End={levels[1]}",
            "Normal",
        ),
        "source": "HelixVivid",
        "label": "white accent" if accent_white else f"vivid {cue}",
    })


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
