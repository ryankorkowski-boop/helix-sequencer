"""Read xLights tables and layout targets without changing either file."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


def finite(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"Expected a finite number, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Metrics require finite numbers")
    return result


def settings(text: str) -> dict[str, str]:
    return dict(re.findall(r"(?:^|,)([A-Za-z0-9_]+)=([^,]*)", text))


@dataclass(frozen=True)
class Model:
    name: str
    model_class: str
    channels: float | None


@dataclass(frozen=True)
class Effect:
    target: str
    layer: str
    models: tuple[str, ...]
    name: str
    start: float
    end: float
    signature: tuple[str, ...]
    palette: tuple[str, ...]
    start_level: float
    end_level: float

    def intensity(self, time: float) -> float:
        phase = (time - self.start) / (self.end - self.start)
        return self.start_level + phase * (self.end_level - self.start_level)


def read_layout(path: str | Path) -> tuple[
    dict[str, Model], dict[str, tuple[str, ...]]
]:
    root = ET.parse(path).getroot()
    models: dict[str, Model] = {}
    for node in root.findall("./models/model"):
        name = node.get("name", "")
        if not name or name in models:
            raise ValueError("Layout models need unique, nonempty names")
        raw_count = node.get("ChannelCount", node.get("channels"))
        channels = finite(raw_count) if raw_count is not None else None
        if channels is not None and channels <= 0:
            raise ValueError(f"Invalid channel count for {name}")
        models[name] = Model(
            name, node.get("DisplayAs", node.get("type", "unknown")), channels
        )
    if not models:
        raise ValueError("Layout contains no models")
    groups: dict[str, tuple[str, ...]] = {}
    for node in root.findall("./modelGroups/modelGroup"):
        name = node.get("name", "")
        if not name or name in models or name in groups:
            raise ValueError("Layout groups need unique, nonempty names")
        groups[name] = tuple(
            v.strip() for v in node.get("models", "").split(",") if v.strip()
        )
    targets: dict[str, tuple[str, ...]] = {name: (name,) for name in models}

    def expand(name: str, ancestors: frozenset[str]) -> tuple[str, ...]:
        if name in ancestors:
            raise ValueError(f"Cyclic layout group: {name}")
        if name in targets:
            return targets[name]
        if name not in groups:
            raise ValueError(f"Unknown layout group member: {name}")
        members = {
            leaf for child in groups[name]
            for leaf in expand(child, ancestors | {name})
        }
        if not members:
            raise ValueError(f"Empty layout group: {name}")
        targets[name] = tuple(sorted(members))
        return targets[name]

    for name in groups:
        expand(name, frozenset())
    return models, targets


def _table_value(raw: str, table: list[str], label: str) -> str:
    if not raw.isdigit():
        if raw and "=" not in raw:
            raise ValueError(f"Invalid {label} settings or reference: {raw}")
        return raw
    index = int(raw)
    if index >= len(table):
        raise ValueError(f"Invalid {label} table reference: {index}")
    return table[index]


def _palette(text: str) -> tuple[str, ...]:
    values = settings(text)
    default = "0" if any(k.startswith("C_CHECKBOX_Palette")
                         for k in values) else "1"
    return tuple(sorted({
        color.upper() for key, color in values.items()
        if re.fullmatch(r"C_BUTTON_Palette\d+", key)
        and values.get(key.replace("BUTTON", "CHECKBOX"), default) == "1"
        and re.fullmatch(r"#[0-9a-fA-F]{6}", color)
    }))


def _levels(name: str, params: dict[str, str]) -> tuple[float, float]:
    if name.lower() == "off":
        return 0.0, 0.0
    brightness = finite(params.get("B_SLIDER_Brightness", "100")) / 100
    start = end = 1.0
    if name.lower() == "on":
        start = finite(params.get("E_TEXTCTRL_Eff_On_Start", params.get(
            "E_SLIDER_Eff_On_Start", "100"))) / 100
        end = finite(params.get("E_TEXTCTRL_Eff_On_End", params.get(
            "E_SLIDER_Eff_On_End", "100"))) / 100
    if not all(0 <= v <= 1 for v in (brightness, start, end)):
        raise ValueError("Static intensity settings must be between 0 and 100")
    return start * brightness, end * brightness


def read_sequence(
    path: str | Path, targets: dict[str, tuple[str, ...]], *,
    legacy_millisecond_times: bool = False,
) -> tuple[
    list[Effect], float, list[str]
]:
    root = ET.parse(path).getroot()
    duration = finite(root.findtext("./head/sequenceDuration", "0")) * 1000
    db = [n.text or "" for n in root.findall("./EffectDB/Effect")]
    palettes = [n.text or "" for n in root.findall(
        "./ColorPalettes/ColorPalette")]
    effects: list[Effect] = []
    warnings: set[str] = set()
    fixed_point = root.get("FixedPointTiming") == "1"
    scale = 1 if fixed_point or legacy_millisecond_times else 1000
    if legacy_millisecond_times and not fixed_point:
        warnings.add("non_native_millisecond_timing_override")
    if root.find("DisplayElements") is None:
        warnings.add("missing_native_display_elements")

    def read_layers(node: ET.Element, target: str, prefix: str = "") -> None:
        if target not in targets:
            raise ValueError(f"Unknown sequence target: {target}")
        for index, layer in enumerate(node.findall("EffectLayer")):
            for item in layer.findall("Effect"):
                start = finite(item.get("startTime")) * scale
                end = finite(item.get("endTime")) * scale
                if start < 0 or end <= start:
                    raise ValueError(f"Invalid effect interval on {target}")
                raw = item.get("settings", item.text or "")
                if item.get("settings") and item.get("ref") is None:
                    warnings.add("settings_attribute_is_helix_metadata_only")
                if item.get("ref") is not None:
                    if not item.get("ref", "").isdigit():
                        raise ValueError("Invalid effect table reference")
                    raw = _table_value(item.get("ref", ""), db, "effect")
                palette_ref = item.get("palette", "")
                if "=" in palette_ref:
                    warnings.add("inline_palette_is_helix_metadata_only")
                palette_raw = _table_value(palette_ref, palettes, "palette")
                params = settings(raw)
                name = item.get("name", "")
                if not name:
                    raise ValueError("Model effects need an effect name")
                colors = _palette(palette_raw)
                levels = _levels(name, params)
                if colors == ("#000000",):
                    levels = (0.0, 0.0)
                if any("VALUECURVE" in k for k in params):
                    warnings.add("value_curves_not_evaluated")
                if name.lower() not in {"on", "off"}:
                    warnings.add("non_on_effect_occupancy_is_an_upper_bound")
                if not colors:
                    warnings.add("missing_or_unsupported_palette")
                effects.append(Effect(
                    target, f"{prefix}{index}", targets[target], name,
                    start, end,
                    (name, str(sorted(params.items())),
                     str(sorted(settings(palette_raw).items()))),
                    colors, *levels,
                ))
        for index, submodel in enumerate(node.findall("SubModel")):
            # Its physical channel subset is not available in this estimator.
            warnings.add("submodel_occupancy_uses_parent_model")
            read_layers(submodel, target, f"{prefix}s{index}:")

    container = root.find("ElementEffects")
    if container is None:
        raise ValueError("XSQ has no ElementEffects container")
    for node in container.findall("Element"):
        if node.get("type") == "timing":
            continue
        read_layers(node, node.get("name", ""))
    return sorted(effects, key=lambda e: (
        e.start, e.target, e.layer, e.name, e.signature
    )), duration, sorted(warnings)
