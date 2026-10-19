from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.model_parser import Model, parse_layout


@dataclass(frozen=True)
class ChannelUsage:
    model_name: str
    start_channel: int | None
    channel_count: int
    end_channel: int
    rgb: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControllerSizingReport:
    schema: str
    layout_path: str
    model_count: int
    models_with_channels: int
    required_channels: int
    recommended_channels: int
    padding_channels: int
    warnings: list[str] = field(default_factory=list)
    usages: list[ChannelUsage] = field(default_factory=list)
    xml_patched: bool = False
    output_path: str | None = None
    report_path: str | None = None
    patched_attributes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["usages"] = [usage.to_dict() for usage in self.usages]
        return data


_NON_RGB_TYPES = {"channelblock", "flood", "dmx", "dmxgeneral", "dmxflood", "dmxfloodlight", "dmxfloodarea"}
_CHANNEL_COUNT_ATTR_TOKENS = ("channels", "channelcount", "numchannels", "maxchannels", "endchannel")
_CONTROLLER_CONTEXT_TOKENS = ("controller", "controllers", "output", "outputs", "network", "networks", "e131", "ddp", "dmx", "universe")
_MODEL_CONTEXT_TOKENS = ("model", "submodel", "modelgroup", "models")


def _normalize(value: object) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(round(float(str(value).strip())))
    except (TypeError, ValueError):
        return default


def estimate_model_channel_count(model: Model) -> int:
    pixels = max(0, int(getattr(model, "total_pixels", 0) or 0))
    if pixels <= 0:
        return 0
    model_type = _normalize(getattr(model, "type", ""))
    if model.is_single_color() or model_type in _NON_RGB_TYPES:
        return pixels
    if model.is_rgb_capable():
        return pixels * 3
    return pixels * 3 if pixels > 1 else 1


def _usage_reason(model: Model, rgb: bool) -> str:
    model_type = _normalize(getattr(model, "type", ""))
    if model.is_single_color() or model_type in _NON_RGB_TYPES:
        return "single_color_or_channel_count_model"
    if rgb:
        return "rgb_capable_three_channels_per_pixel"
    return "conservative_default"


def analyze_layout_channel_usage(layout_path: Path, padding_channels: int = 50) -> ControllerSizingReport:
    path = Path(layout_path)
    parsed = parse_layout(path)
    warnings: list[str] = []
    usages: list[ChannelUsage] = []
    required_channels = 0

    root_models = [model for model in parsed.models.values() if not getattr(model, "is_submodel", False)]
    for model in root_models:
        start = model.start_channel
        if start is None or int(start) <= 0:
            warnings.append(f"Model '{model.name}' has no positive StartChannel; skipped for controller sizing.")
            continue
        channel_count = estimate_model_channel_count(model)
        if channel_count <= 0:
            warnings.append(f"Model '{model.name}' has no estimated channel usage; skipped for controller sizing.")
            continue
        end_channel = int(start) + int(channel_count) - 1
        required_channels = max(required_channels, end_channel)
        rgb = bool(model.is_rgb_capable() and not model.is_single_color())
        usages.append(ChannelUsage(model.name, int(start), int(channel_count), int(end_channel), rgb, _usage_reason(model, rgb)))

    padding = max(0, int(padding_channels))
    recommended_channels = required_channels + padding if required_channels > 0 else 0
    return ControllerSizingReport(
        schema="helix.controller_sizing.v1",
        layout_path=str(path),
        model_count=len(root_models),
        models_with_channels=len(usages),
        required_channels=int(required_channels),
        recommended_channels=int(recommended_channels),
        padding_channels=padding,
        warnings=warnings,
        usages=usages,
    )


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _is_model_context(element: ET.Element) -> bool:
    tag = _normalize(_tag_name(element))
    return tag in _MODEL_CONTEXT_TOKENS or tag.endswith("model") or tag.endswith("submodel")


def _is_controller_context(element: ET.Element) -> bool:
    tag = _normalize(_tag_name(element))
    if any(token in tag for token in _CONTROLLER_CONTEXT_TOKENS):
        return True
    values = " ".join(str(value) for value in element.attrib.values()).lower()
    return any(token in values for token in _CONTROLLER_CONTEXT_TOKENS)


def _is_channel_capacity_attr(name: str) -> bool:
    key = _normalize(name)
    if "startchannel" in key:
        return False
    return key in {"channel", "channels"} or any(token in key for token in _CHANNEL_COUNT_ATTR_TOKENS)


def _positive_int(value: object) -> bool:
    return _as_int(value, 0) > 0


def _patch_controller_attrs(root: ET.Element, recommended_channels: int) -> tuple[int, list[str]]:
    patched = 0
    patched_attrs: list[str] = []
    for element in root.iter():
        if _is_model_context(element) or not _is_controller_context(element):
            continue
        for attr_name, attr_value in list(element.attrib.items()):
            if not _is_channel_capacity_attr(attr_name) or not _positive_int(attr_value):
                continue
            current = _as_int(attr_value)
            if current >= recommended_channels:
                continue
            element.set(attr_name, str(recommended_channels))
            patched += 1
            patched_attrs.append(f"{_tag_name(element)}@{attr_name}:{current}->{recommended_channels}")
    return patched, patched_attrs


def _copy_report(report: ControllerSizingReport, **updates: Any) -> ControllerSizingReport:
    data = report.to_dict()
    data.update(updates)
    data["usages"] = list(report.usages)
    return ControllerSizingReport(**data)


def patch_layout_controller_capacity(
    layout_path: Path,
    output_path: Path | None = None,
    padding_channels: int = 50,
    dry_run: bool = False,
) -> ControllerSizingReport:
    source = Path(layout_path)
    report = analyze_layout_channel_usage(source, padding_channels=padding_channels)
    warnings = list(report.warnings)

    if dry_run:
        return _copy_report(report, xml_patched=False, output_path=None, report_path=None, warnings=warnings, patched_attributes=[])

    destination = Path(output_path) if output_path is not None else source.with_name(f"{source.stem}.autosized{source.suffix}")
    tree = ET.parse(source)
    root = tree.getroot()
    patched_count, patched_attrs = _patch_controller_attrs(root, report.recommended_channels)
    if patched_count == 0:
        warnings.append(f"No controller/output channel-count attributes needed updating; recommended capacity is {report.recommended_channels}.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    report_path = destination.with_suffix(destination.suffix + ".controller_sizing_report.json")
    final_report = _copy_report(
        report,
        warnings=warnings,
        xml_patched=patched_count > 0,
        output_path=str(destination),
        report_path=str(report_path),
        patched_attributes=patched_attrs,
    )
    report_path.write_text(json.dumps(final_report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return final_report
