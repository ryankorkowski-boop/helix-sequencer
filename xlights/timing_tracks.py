from __future__ import annotations

import xml.etree.ElementTree as ET

from xlights import xml_io


def _legacy():
    from xlights import xsq_writer as legacy

    return legacy


def normalize_view_name(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    out: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        low = item.lower()
        if low in {"0", "default", "master", "master view", "masterview", "master_view"}:
            continue
        if item.isdigit():
            continue
        if low in seen:
            continue
        seen.add(low)
        out.append(item)
    return ",".join(out)


def ensure_last_view_index(root: ET.Element) -> int:
    last_view = root.find("lastView")
    value = (last_view.text or "").strip() if last_view is not None else ""
    try:
        normalized = max(0, int(value))
    except Exception:
        normalized = 0
    if last_view is None:
        last_view = ET.Element("lastView")
        root.append(last_view)
    last_view.text = str(normalized)
    return normalized


def is_generated_or_placeholder_timing_track(name: str) -> bool:
    legacy = _legacy()
    normalized = legacy.normalize_name(name)
    if not normalized:
        return False
    if normalized.startswith("auto "):
        return True
    return normalized in {"new timing", "empty", "empty 2"}


def timing_track_default_visible(track_name: str, active: bool) -> bool:
    if active:
        return True
    return not is_generated_or_placeholder_timing_track(track_name)


def ensure_timing_display_entry(root: ET.Element, track_name: str, active: bool = False) -> ET.Element:
    legacy = _legacy()
    ensure_last_view_index(root)
    display = xml_io.find_root_child(root, "DisplayElements")
    if display is None:
        display = ET.Element("DisplayElements")
        root.append(display)
    desired_visible = "1" if timing_track_default_visible(track_name, active) else "0"
    for el in list(display):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if element_type == "timing" and name == track_name:
            el.attrib["active"] = "1" if active else "0"
            el.attrib.setdefault("collapsed", "0")
            el.attrib["visible"] = desired_visible
            el.attrib["views"] = normalize_view_name(legacy._get_attr(el, ["views", "Views"]))
            return el
    new_el = ET.Element("Element")
    new_el.attrib.update(
        {
            "collapsed": "0",
            "type": "timing",
            "name": track_name,
            "visible": desired_visible,
            "views": "",
            "active": "1" if active else "0",
        }
    )
    insert_at = len(list(display))
    for idx, existing in enumerate(list(display)):
        element_type = (legacy._get_attr(existing, ["type", "Type"]) or "").lower()
        if element_type != "timing":
            insert_at = idx
            break
    display.insert(insert_at, new_el)
    return new_el


def ensure_timing_effect_track(root: ET.Element, track_name: str) -> ET.Element:
    legacy = _legacy()
    element_effects = xml_io.find_root_child(root, "ElementEffects")
    if element_effects is None:
        element_effects = ET.Element("ElementEffects")
        root.append(element_effects)
    for el in list(element_effects):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if element_type == "timing" and name == track_name:
            for child in list(el):
                el.remove(child)
            layer = ET.Element("EffectLayer")
            el.append(layer)
            return layer
    el = ET.Element("Element")
    el.attrib["type"] = "timing"
    el.attrib["name"] = track_name
    layer = ET.Element("EffectLayer")
    el.append(layer)
    insert_at = len(list(element_effects))
    for idx, existing in enumerate(list(element_effects)):
        element_type = (legacy._get_attr(existing, ["type", "Type"]) or "").lower()
        if element_type != "timing":
            insert_at = idx
            break
    element_effects.insert(insert_at, el)
    return layer


def write_timing_track(
    root: ET.Element, track_name: str, spans: list[tuple[str, int, int]], active: bool = False
) -> None:
    ensure_timing_display_entry(root, track_name, active=active)
    layer = ensure_timing_effect_track(root, track_name)
    for label, start_ms, end_ms in spans:
        effect = ET.Element("Effect")
        effect.attrib["label"] = label
        effect.attrib["startTime"] = str(int(start_ms))
        effect.attrib["endTime"] = str(int(max(start_ms + 1, end_ms)))
        layer.append(effect)


def prune_empty_timing_tracks(root: ET.Element, keep_prefixes: tuple[str, ...] = ()) -> int:
    legacy = _legacy()
    display = xml_io.find_root_child(root, "DisplayElements")
    element_effects = xml_io.find_root_child(root, "ElementEffects")
    if display is None or element_effects is None:
        return 0
    keep_prefixes = tuple(prefix for prefix in keep_prefixes if prefix)
    removed = 0
    keep_names: set[str] = set()
    for el in list(element_effects):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type != "timing":
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        if keep_prefixes and any(name.startswith(prefix) for prefix in keep_prefixes):
            keep_names.add(name)
            continue
        has_effect = any(child.tag.endswith("Effect") for child in el.iter())
        if not has_effect:
            element_effects.remove(el)
            removed += 1
        else:
            keep_names.add(name)

    for el in list(display):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type != "timing":
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if not name:
            continue
        if keep_prefixes and any(name.startswith(prefix) for prefix in keep_prefixes):
            continue
        if name not in keep_names:
            display.remove(el)
            removed += 1
    return removed


def remove_legacy_timing_tracks(root: ET.Element, *, current_version: str) -> int:
    legacy = _legacy()
    display = xml_io.find_root_child(root, "DisplayElements")
    element_effects = xml_io.find_root_child(root, "ElementEffects")
    if display is None or element_effects is None:
        return 0
    removed = 0
    keep_token = f" {current_version}".lower()
    for el in list(element_effects):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type != "timing":
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if name.lower().startswith("auto ") and keep_token not in name.lower():
            element_effects.remove(el)
            removed += 1
    for el in list(display):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        if element_type != "timing":
            continue
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if name.lower().startswith("auto ") and keep_token not in name.lower():
            display.remove(el)
            removed += 1
    return removed


def read_timing_track_marks_ms(root: ET.Element, track_name: str) -> list[int]:
    legacy = _legacy()
    timing_el = None
    for el in legacy._find_any(root, "Element"):
        element_type = (legacy._get_attr(el, ["type", "Type"]) or "").lower()
        name = (legacy._get_attr(el, ["name", "Name"]) or "").strip()
        if element_type == "timing" and name.lower() == track_name.lower():
            timing_el = el
            break
    if timing_el is None:
        return []

    marks_ms: list[int] = []
    for node in timing_el.iter():
        if node is timing_el:
            continue
        start = legacy._get_attr(node, ["startTime", "StartTime", "start", "Start", "time", "Time"])
        if start is None:
            continue
        try:
            value = int(round(float(start)))
        except Exception:
            continue
        if value >= 0:
            marks_ms.append(value)

    marks_ms = sorted(set(marks_ms))
    if len(marks_ms) > 20000:
        marks_ms = marks_ms[:20000]
    return marks_ms
