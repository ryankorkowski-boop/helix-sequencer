from __future__ import annotations

from collections import defaultdict
import copy
from pathlib import Path
from typing import TYPE_CHECKING
import xml.etree.ElementTree as ET

from xlights import timing_tracks, xml_io

if TYPE_CHECKING:
    from xlights.xsq_writer import XsqIndex


def _legacy():
    from xlights import xsq_writer as legacy

    return legacy


def name_lookup_keys(name: str) -> list[str]:
    legacy = _legacy()
    raw = (name or "").strip()
    if not raw:
        return []
    keys = [raw.lower()]
    normalized = legacy.normalize_name(raw)
    if normalized and normalized not in keys:
        keys.append(normalized)
    return keys


def register_lookup_name(lookup: dict[str, str], name: str, *, prefer_exact: bool) -> None:
    for key in name_lookup_keys(name):
        if prefer_exact:
            lookup[key] = name
        else:
            lookup.setdefault(key, name)


def _aliases(element: ET.Element) -> list[str]:
    names = []
    for container in element:
        if container.tag.lower() != "aliases":
            continue
        for alias in container:
            name = alias.get("name", "").strip()
            if name.lower().startswith("oldname:"):
                name = name.split(":", 1)[1].strip()
            if name:
                names.append(name)
    return names


def layout_entries_and_lookup(layout_path: Path) -> tuple[list[str], dict[str, str]]:
    tree = ET.parse(layout_path)
    root = tree.getroot()

    ordered_names: list[str] = []
    lookup: dict[str, str] = {}
    aliases_by_key: dict[str, set[str]] = defaultdict(set)

    def register_alias(alias: str, name: str) -> None:
        for key in name_lookup_keys(alias):
            aliases_by_key[key].add(name)

    groups_el = root.find("modelGroups")
    if groups_el is not None:
        for child in list(groups_el):
            name = (child.attrib.get("name") or "").strip()
            if not name:
                continue
            ordered_names.append(name)
            register_lookup_name(lookup, name, prefer_exact=True)
            for alias in _aliases(child):
                register_alias(alias, name)

    models_el = root.find("models")
    for child in models_el if models_el is not None else ():
        name = (child.attrib.get("name") or "").strip()
        if not name:
            continue
        ordered_names.append(name)
        register_lookup_name(lookup, name, prefer_exact=True)
        parent_aliases = _aliases(child)
        for alias in parent_aliases:
            register_alias(alias, name)
        for sub in list(child):
            if not sub.tag.endswith("subModel"):
                continue
            short_name = (sub.attrib.get("name") or "").strip()
            if not short_name:
                continue
            full_name = f"{name}/{short_name}"
            ordered_names.append(full_name)
            register_lookup_name(lookup, full_name, prefer_exact=True)
            sub_aliases = _aliases(sub)
            for alias in sub_aliases:
                register_alias(alias, full_name)
            for parent in [name, *parent_aliases]:
                for leaf in [short_name, *sub_aliases]:
                    register_alias(f"{parent}/{leaf}", full_name)
    for key, targets in aliases_by_key.items():
        if len(targets) == 1:
            lookup.setdefault(key, next(iter(targets)))
    return (ordered_names, lookup)


def map_layout_name(name: str, lookup: dict[str, str]) -> str | None:
    for key in name_lookup_keys(name):
        if key in lookup:
            return lookup[key]
    return None


def new_display_model_entry(name: str) -> ET.Element:
    el = ET.Element("Element")
    el.attrib.update(
        {
            "collapsed": "0",
            "type": "model",
            "name": name,
            "visible": "1",
        }
    )
    return el


def new_effect_model_entry(name: str) -> ET.Element:
    el = ET.Element("Element")
    el.attrib["type"] = "model"
    el.attrib["name"] = name
    el.append(ET.Element("EffectLayer"))
    return el


def merge_effect_model_entry(target: ET.Element, source: ET.Element) -> None:
    existing_names = set()
    unnamed_count = 0
    for layer in list(target):
        if not (layer.tag.endswith("EffectLayer") or layer.tag.endswith("Layer")):
            continue
        layer_name = (layer.attrib.get("name") or "").strip()
        if layer_name:
            existing_names.add(layer_name)
        else:
            unnamed_count += 1
    for layer in list(source):
        if not (layer.tag.endswith("EffectLayer") or layer.tag.endswith("Layer")):
            continue
        layer_name = (layer.attrib.get("name") or "").strip()
        already_present = layer_name in existing_names if layer_name else unnamed_count > 0
        if already_present:
            has_authored_effects = (
                not layer_name.startswith("AUTO_DreamSequenceWeaver_")
                and any(child.tag.endswith("Effect") for child in layer)
            )
            if not has_authored_effects or any(
                ET.tostring(existing) == ET.tostring(layer) for existing in target
            ):
                continue
        target.append(copy.deepcopy(layer))
        if layer_name:
            existing_names.add(layer_name)
        else:
            unnamed_count += 1


def collect_effect_elements(root: ET.Element) -> dict[str, ET.Element]:
    legacy = _legacy()
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
    return elements


def sync_xsq_to_layout(xsq: "XsqIndex", layout_path: Path | None) -> dict[str, int]:
    legacy = _legacy()
    if layout_path is None or not layout_path.exists():
        return {"layout_names": 0, "display_updated": 0, "effect_rows_updated": 0, "stale_removed": 0}

    ordered_names, lookup = layout_entries_and_lookup(layout_path)
    if not ordered_names:
        return {"layout_names": 0, "display_updated": 0, "effect_rows_updated": 0, "stale_removed": 0}

    root = xsq.root
    timing_tracks.ensure_last_view_index(root)
    display = xml_io.find_root_child(root, "DisplayElements")
    if display is None:
        display = ET.Element("DisplayElements")
        root.append(display)
    element_effects = xml_io.find_root_child(root, "ElementEffects")
    if element_effects is None:
        element_effects = ET.Element("ElementEffects")
        root.append(element_effects)

    active_timing_display: list[ET.Element] = []
    inactive_timing_display: list[ET.Element] = []
    model_display_by_name: dict[str, ET.Element] = {}
    stale_display = 0
    for el in list(display):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type == "timing":
            active = (legacy._get_attr(el, ["active", "Active"]) or "").strip()
            el.attrib["views"] = timing_tracks.normalize_view_name(legacy._get_attr(el, ["views", "Views"]))
            bucket = active_timing_display if active == "1" else inactive_timing_display
            bucket.append(copy.deepcopy(el))
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        mapped = map_layout_name(name, lookup)
        if not mapped:
            stale_display += 1
            continue
        clone = copy.deepcopy(el)
        clone.attrib["name"] = mapped
        clone.attrib["type"] = "model"
        if "Views" in clone.attrib:
            del clone.attrib["Views"]
        if "views" in clone.attrib:
            clone.attrib["views"] = timing_tracks.normalize_view_name(clone.attrib.get("views"))
        model_display_by_name.setdefault(mapped, clone)

    for child in list(display):
        display.remove(child)
    for el in active_timing_display:
        display.append(el)
    for name in ordered_names:
        display.append(model_display_by_name.get(name, new_display_model_entry(name)))
    for el in inactive_timing_display:
        display.append(el)

    active_timing_effects: list[ET.Element] = []
    inactive_timing_effects: list[ET.Element] = []
    model_effects_by_name: dict[str, ET.Element] = {}
    stale_effects = 0
    for el in list(element_effects):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type == "timing":
            active = (legacy._get_attr(el, ["active", "Active"]) or "").strip()
            bucket = active_timing_effects if active == "1" else inactive_timing_effects
            bucket.append(copy.deepcopy(el))
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        mapped = map_layout_name(name, lookup)
        if not mapped:
            stale_effects += 1
            continue
        clone = copy.deepcopy(el)
        clone.attrib["name"] = mapped
        clone.attrib["type"] = "model"
        existing = model_effects_by_name.get(mapped)
        if existing is None:
            model_effects_by_name[mapped] = clone
        else:
            merge_effect_model_entry(existing, clone)

    for child in list(element_effects):
        element_effects.remove(child)
    for el in active_timing_effects:
        element_effects.append(el)
    for name in ordered_names:
        element_effects.append(model_effects_by_name.get(name, new_effect_model_entry(name)))
    for el in inactive_timing_effects:
        element_effects.append(el)

    xsq.elements = collect_effect_elements(root)
    return {
        "layout_names": len(ordered_names),
        "display_updated": len(model_display_by_name),
        "effect_rows_updated": len(model_effects_by_name),
        "stale_removed": stale_display + stale_effects,
    }


def normalize_display_views(root: ET.Element, *, force: bool = True) -> int:
    legacy = _legacy()
    display = xml_io.find_root_child(root, "DisplayElements")
    if display is None:
        return 0
    timing_tracks.ensure_last_view_index(root)
    updated = 0
    for el in list(display):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").strip().lower()
        if not element_type:
            continue
        current = timing_tracks.normalize_view_name(legacy._get_attr(el, ["views", "Views"]))
        if "Views" in el.attrib:
            del el.attrib["Views"]
            updated += 1
        if force or "views" in el.attrib or current:
            if (el.attrib.get("views") or "") != current:
                el.attrib["views"] = current
                updated += 1
        if element_type == "timing":
            active = (legacy._get_attr(el, ["active", "Active"]) or "").strip() == "1"
            name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
            if active or timing_tracks.is_generated_or_placeholder_timing_track(name):
                desired_visible = "1" if timing_tracks.timing_track_default_visible(name, active) else "0"
                if (el.attrib.get("visible") or "") != desired_visible:
                    el.attrib["visible"] = desired_visible
                    updated += 1
            el.attrib.setdefault("collapsed", "0")
            el.attrib.setdefault("active", "1" if active else "0")
            continue
    return updated


def ensure_master_view_models(root: ET.Element) -> dict[str, int]:
    legacy = _legacy()
    timing_tracks.ensure_last_view_index(root)
    display = xml_io.find_root_child(root, "DisplayElements")
    if display is None:
        display = ET.Element("DisplayElements")
        root.append(display)
    element_effects = xml_io.find_root_child(root, "ElementEffects")
    if element_effects is None:
        element_effects = ET.Element("ElementEffects")
        root.append(element_effects)

    updated = 0
    added_display = 0
    added_effects = 0

    display_names: set[str] = set()
    for el in list(display):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").strip().lower()
        if not element_type:
            continue
        if element_type == "timing":
            normalized_views = timing_tracks.normalize_view_name(legacy._get_attr(el, ["views", "Views"]))
            if "Views" in el.attrib:
                del el.attrib["Views"]
                updated += 1
            if (el.attrib.get("views") or "") != normalized_views:
                el.attrib["views"] = normalized_views
                updated += 1
            active = (legacy._get_attr(el, ["active", "Active"]) or "").strip() == "1"
            name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
            if active or timing_tracks.is_generated_or_placeholder_timing_track(name):
                desired_visible = "1" if timing_tracks.timing_track_default_visible(name, active) else "0"
                if (el.attrib.get("visible") or "") != desired_visible:
                    el.attrib["visible"] = desired_visible
                    updated += 1
            el.attrib.setdefault("collapsed", "0")
            el.attrib.setdefault("visible", "1")
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        display_names.add(name)
        normalized_views = timing_tracks.normalize_view_name(legacy._get_attr(el, ["views", "Views"]))
        if "Views" in el.attrib:
            del el.attrib["Views"]
            updated += 1
        if "views" in el.attrib and (el.attrib.get("views") or "") != normalized_views:
            el.attrib["views"] = normalized_views
            updated += 1
        if el.attrib.get("type") != "model":
            el.attrib["type"] = "model"
            updated += 1
        el.attrib.setdefault("collapsed", "0")
        el.attrib.setdefault("visible", "1")

    effect_names: set[str] = set()
    for el in list(element_effects):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").strip().lower()
        if element_type == "timing":
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        effect_names.add(name)
        if el.attrib.get("type") != "model":
            el.attrib["type"] = "model"
            updated += 1
        if not any(child.tag.endswith("EffectLayer") or child.tag.endswith("Layer") for child in list(el)):
            el.append(ET.Element("EffectLayer"))
            updated += 1

    missing_display = sorted(effect_names - display_names)
    for name in missing_display:
        display.append(new_display_model_entry(name))
        added_display += 1

    missing_effects = sorted(display_names - effect_names)
    if missing_effects:
        insert_at = len(list(element_effects))
        for idx, existing in enumerate(list(element_effects)):
            element_type = (legacy._get_attr(existing, ["type", "Type"]) or "").strip().lower()
            if element_type != "timing":
                insert_at = idx
                break
        for offset, name in enumerate(missing_effects):
            element_effects.insert(insert_at + offset, new_effect_model_entry(name))
            added_effects += 1

    return {
        "display_added": added_display,
        "effects_added": added_effects,
        "rows_touched": updated,
    }
