from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from core.model_parser import Model, parse_layout

NETWORKS_FILENAME = "xlights_networks.xml"
PREVIEW_NETWORK_DESC = "Helix preview null controller"
MIN_PREVIEW_CHANNELS = 1

_CHANNEL_KEYS = (
    "ChannelCount",
    "channelCount",
    "Channels",
    "channels",
    "NumChannels",
    "numChannels",
    "MaxChannels",
    "maxChannels",
    "Size",
    "size",
)
_START_KEYS = (
    "StartChannel",
    "startChannel",
    "StartChan",
    "startChan",
    "Start",
    "start",
)
_NAME_KEYS = ("name", "Name", "Description", "description", "Controller", "controller")


@dataclass(frozen=True)
class ControllerInfo:
    name: str
    channels: int
    start_channel: int | None = None
    source_tag: str = "controller"
    raw_attrs: dict[str, str] = field(default_factory=dict)

    @property
    def end_channel(self) -> int:
        if self.start_channel is None:
            return self.channels
        return max(self.start_channel, self.start_channel + self.channels - 1)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "channels": self.channels,
            "start_channel": self.start_channel,
            "end_channel": self.end_channel,
            "source_tag": self.source_tag,
        }


@dataclass(frozen=True)
class ControllerPlan:
    source: str
    channel_count: int
    layout_channel_count: int
    networks_path: Path | None = None
    controllers: tuple[ControllerInfo, ...] = ()
    synthesized_null_controller: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "channel_count": self.channel_count,
            "layout_channel_count": self.layout_channel_count,
            "networks_path": str(self.networks_path) if self.networks_path is not None else None,
            "synthesized_null_controller": self.synthesized_null_controller,
            "controllers": [controller.to_dict() for controller in self.controllers],
        }


def discover_networks_path(layout_path: Path) -> Path:
    """Return the xLights networks XML beside the rgbeffects/layout file."""

    return Path(layout_path).expanduser().resolve().parent / NETWORKS_FILENAME


def parse_networks(networks_path: Path) -> tuple[ControllerInfo, ...]:
    """Parse controller/output channel sizing from xlights_networks.xml.

    xLights has used several XML shapes over time, so this parser is deliberately
    attribute-driven. It accepts common controller/network/output channel fields
    and also handles controller elements whose children carry the per-output
    channel counts.
    """

    path = Path(networks_path)
    if not path.exists():
        return ()

    root = ET.parse(path).getroot()
    controllers: list[ControllerInfo] = []
    seen: set[int] = set()

    for element in root.iter():
        if element is root:
            continue
        if not _looks_like_controller(element):
            continue
        info = _controller_from_element(element)
        if info is None or info.channels <= 0:
            continue
        marker = id(element)
        if marker in seen:
            continue
        seen.add(marker)
        controllers.append(info)

    return tuple(controllers)


def layout_channel_count(layout_path: Path) -> int:
    """Return the highest channel required by the xLights layout models."""

    layout = parse_layout(Path(layout_path))
    sequential_total = 0
    max_end_channel = 0
    for name in layout.root_models():
        model = layout.models[name]
        channels = _model_channel_span(model)
        sequential_total += channels
        if model.start_channel is not None and model.start_channel > 0:
            max_end_channel = max(max_end_channel, model.start_channel + channels - 1)
    return max(max_end_channel, sequential_total)


def build_controller_plan(
    layout_path: Path,
    *,
    padding: int = 50,
    networks_path: Path | None = None,
) -> ControllerPlan:
    """Resolve controller sizing from xlights_networks.xml, with preview fallback.

    If a sibling networks file has controller/channel data, that wins. When it is
    missing or empty, Helix synthesizes a preview-only null controller sized just
    above the layout channel count.
    """

    layout_count = layout_channel_count(layout_path)
    candidate_networks = Path(networks_path) if networks_path is not None else discover_networks_path(layout_path)
    controllers = parse_networks(candidate_networks)
    if controllers:
        controller_count = max(controller.end_channel for controller in controllers)
        return ControllerPlan(
            source="xlights_networks",
            channel_count=max(layout_count, controller_count),
            layout_channel_count=layout_count,
            networks_path=candidate_networks,
            controllers=controllers,
            synthesized_null_controller=False,
        )

    null_channels = max(MIN_PREVIEW_CHANNELS, layout_count + max(0, int(padding)))
    return ControllerPlan(
        source="layout_fallback",
        channel_count=null_channels,
        layout_channel_count=layout_count,
        networks_path=candidate_networks if candidate_networks.exists() else None,
        controllers=(
            ControllerInfo(
                name="Helix Preview Null Controller",
                channels=null_channels,
                start_channel=1,
                source_tag="synthetic-null",
            ),
        ),
        synthesized_null_controller=True,
    )


def write_networks_file(plan: ControllerPlan, target: Path) -> Path:
    """Write or copy xlights_networks.xml for an output show folder."""

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if plan.source == "xlights_networks" and plan.networks_path is not None and plan.networks_path.exists():
        source = plan.networks_path.resolve()
        destination = target.resolve(strict=False)
        if source != destination:
            shutil.copy2(source, target)
        return target

    root = ET.Element("Networks", {"computer": os.environ.get("COMPUTERNAME", "WINDOWS")})
    ET.SubElement(
        root,
        "network",
        {
            "NetworkType": "NULL",
            "MaxChannels": str(max(MIN_PREVIEW_CHANNELS, int(plan.channel_count))),
            "Description": PREVIEW_NETWORK_DESC,
        },
    )
    _indent_xml(root)
    ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
    return target


def write_networks_for_xsq_outputs(plan: ControllerPlan, output_paths: list[Path]) -> list[Path]:
    """Place xlights_networks.xml beside generated XSQ files or directories."""

    targets: dict[Path, Path] = {}
    for path in output_paths:
        path = Path(path)
        folder = path if path.suffix.lower() != ".xsq" else path.parent
        targets[folder.resolve(strict=False)] = folder / NETWORKS_FILENAME
    return [write_networks_file(plan, target) for target in targets.values()]


def _controller_from_element(element: ET.Element) -> ControllerInfo | None:
    attrs = {str(key): str(value) for key, value in element.attrib.items()}
    direct_channels = _first_int(attrs, _CHANNEL_KEYS)
    child_channels = sum(
        max(0, _first_int({str(key): str(value) for key, value in child.attrib.items()}, _CHANNEL_KEYS))
        for child in element
    )
    channels = max(direct_channels, child_channels)
    if channels <= 0:
        channels = _channels_from_universes(attrs)
    if channels <= 0:
        return None
    return ControllerInfo(
        name=_name_for(element, attrs),
        channels=channels,
        start_channel=_first_int(attrs, _START_KEYS) or None,
        source_tag=_strip_namespace(element.tag),
        raw_attrs=attrs,
    )


def _looks_like_controller(element: ET.Element) -> bool:
    tag = _strip_namespace(element.tag).lower()
    attrs = {str(key): str(value) for key, value in element.attrib.items()}
    if any(token in tag for token in ("controller", "network")):
        return True
    if _first_int(attrs, _CHANNEL_KEYS) > 0 and any(key in attrs for key in _NAME_KEYS):
        return True
    return False


def _model_channel_span(model: Model) -> int:
    raw_num_channels = _first_int(model.raw_attrs, _CHANNEL_KEYS)
    if raw_num_channels > 0:
        return raw_num_channels
    if model.is_rgb_capable():
        return max(1, model.total_pixels * 3)
    return max(1, model.total_pixels)


def _channels_from_universes(attrs: dict[str, str]) -> int:
    universes = _first_int(attrs, ("Universes", "universes", "NumUniverses", "numUniverses"))
    per_universe = _first_int(attrs, ("ChannelsPerUniverse", "channelsPerUniverse", "UniverseSize", "universeSize"))
    if universes <= 0:
        return 0
    return universes * (per_universe if per_universe > 0 else 510)


def _first_int(attrs: dict[str, str], keys: tuple[str, ...]) -> int:
    for key in keys:
        raw = attrs.get(key)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            return max(0, int(round(float(str(raw).strip()))))
        except ValueError:
            continue
    return 0


def _name_for(element: ET.Element, attrs: dict[str, str]) -> str:
    for key in _NAME_KEYS:
        value = (attrs.get(key) or "").strip()
        if value:
            return value
    return _strip_namespace(element.tag)


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    pad = "\n" + ("  " * level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = pad + "  "
        for child in elem:
            _indent_xml(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = pad
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = pad


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
