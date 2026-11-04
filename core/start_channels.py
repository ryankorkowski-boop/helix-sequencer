"""Resolve xLights model StartChannel strings to absolute channels.

The math follows xLights ``Model::GetNumberFromChannelString`` and
``OutputManager::DecodeStartChannel`` (1-based channels):

- ``123`` is an absolute channel.
- ``@Model:N`` is the referenced model's start channel plus ``N - 1``.
- ``>Model:N`` is the referenced model's last channel plus ``N``.
- ``#universe:channel`` and ``#ip:universe:channel`` use the universe table built
  from ``xlights_networks.xml`` controller order and per-universe sizes.
- ``!Controller:N`` is that controller's first channel plus ``N - 1``.

xLights also refuses a ``>`` chain when the referenced model has no controller.
Helix still resolves the channel math so a layout without controller names
remains usable, and records the controller when the networks file identifies one.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

_EXPLICIT_CHANNEL_KEYS = (
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
_START_KEYS = ("StartChannel", "startChannel", "StartChan", "startChan")
_UNIVERSE_TYPES = {"e131", "e1.31", "artnet", "ddp", "kinet", "twinkly"}
_DEFAULT_UNIVERSE_SIZE = 510


class StartChannelError(ValueError):
    """A start channel cannot be turned into an absolute channel."""


class _Wait(Exception):
    """A dependency is not resolved yet."""


@dataclass(frozen=True)
class ControllerSpan:
    name: str
    ip: str | None
    start_channel: int
    channels: int


@dataclass(frozen=True)
class UniverseSpan:
    universe: int
    start_channel: int
    channels: int
    ip: str | None
    controller_name: str


@dataclass(frozen=True)
class NetworkMap:
    controllers: tuple[ControllerSpan, ...] = ()
    universes: tuple[UniverseSpan, ...] = ()

    def controller_named(self, name: str) -> ControllerSpan | None:
        wanted = name.strip()
        for controller in self.controllers:
            if controller.name == wanted:
                return controller
        return None

    def controller_for_channel(self, channel: int) -> str | None:
        for controller in self.controllers:
            if controller.channels <= 0:
                continue
            end = controller.start_channel + controller.channels - 1
            if controller.start_channel <= channel <= end:
                return controller.name
        return None

    def universe(self, ip: str | None, universe: int) -> UniverseSpan | None:
        for item in self.universes:
            if item.universe != universe:
                continue
            if ip is None or item.ip == ip:
                return item
        return None


@dataclass(frozen=True)
class _Resolved:
    start: int
    end: int | None
    controller: str | None


def channels_per_node(model: object) -> int:
    if callable(getattr(model, "is_rgb_capable", None)) and model.is_rgb_capable():  # type: ignore[attr-defined]
        return 3
    text = str(getattr(model, "string_type", "") or "").lower()
    if any(token in text for token in ("rgb", "pixel", "node", "ws2811", "ws2812")):
        return 3
    return 1


def node_numbers(attrs: Mapping[str, str]) -> list[int]:
    """Return 1-based node numbers from submodel ``line*`` / ``subBuffer`` ranges."""

    import re

    chunks: list[str] = []
    for key, value in attrs.items():
        lowered = key.lower()
        if lowered.startswith("line") or lowered in {"subbuffer", "submodelbuffer"}:
            chunks.append(str(value))
    numbers: list[int] = []
    for token in re.findall(r"\d+\s*-\s*\d+|\d+", " ".join(chunks)):
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            lo, hi = sorted((int(start_text), int(end_text)))
            numbers.extend(range(lo, hi + 1))
        else:
            numbers.append(int(token))
    return [number for number in numbers if number > 0]


def model_channel_count(model: object) -> int:
    if getattr(model, "custom_grid_missing", False) and not getattr(model, "is_submodel", False):
        return 0
    attrs = getattr(model, "raw_attrs", {}) or {}
    if getattr(model, "is_submodel", False):
        numbers = node_numbers(attrs)
        if numbers:
            return (max(numbers) - min(numbers) + 1) * channels_per_node(model)
    explicit = _first_int(attrs, _EXPLICIT_CHANNEL_KEYS)
    if explicit > 0 and not getattr(model, "is_submodel", False):
        return explicit
    pixels = int(getattr(model, "total_pixels", 0) or 0)
    if pixels <= 0:
        return 0
    return pixels * channels_per_node(model)


def load_network_map(path: Path | None) -> NetworkMap:
    if path is None or not Path(path).exists():
        return NetworkMap()
    root = ET.parse(path).getroot()
    controllers: list[ControllerSpan] = []
    universes: list[UniverseSpan] = []
    cursor = 1
    next_universe = 1
    index = 0
    for element in list(root):
        if not _is_output_element(element):
            continue
        index += 1
        name = _controller_name(element, fallback=f"Controller {index}")
        ip = _ip_address(element)
        specs, channel_count, next_universe = _expand_output(element, name, ip, next_universe, cursor)
        if channel_count <= 0:
            continue
        controllers.append(ControllerSpan(name=name, ip=ip, start_channel=cursor, channels=channel_count))
        universes.extend(specs)
        cursor += channel_count
    return NetworkMap(controllers=tuple(controllers), universes=tuple(universes))


def resolve_model_channels(
    models: Mapping[str, object],
    *,
    networks_path: Path | None = None,
    strict: bool = False,
) -> list[str]:
    """Fill start/end/controller on each model. Raise in strict mode when any model fails."""

    network = load_network_map(networks_path)
    order = list(models)
    pending = set(order)
    errors: list[str] = []
    progress = True
    while progress and pending:
        progress = False
        for name in order:
            if name not in pending:
                continue
            model = models[name]
            try:
                resolved = _resolve_one(model, models, network, order)
            except _Wait:
                continue
            except StartChannelError as exc:
                _mark_error(model, str(exc))
                errors.append(f"{name}: {exc}")
                pending.remove(name)
                progress = True
                continue
            _mark_resolved(model, resolved)
            pending.remove(name)
            progress = True
    for name in list(pending):
        message = _unresolved_message(name, models, pending, order)
        _mark_error(models[name], message)
        errors.append(f"{name}: {message}")
    if strict and errors:
        raise StartChannelError("; ".join(errors))
    return errors


def _resolve_one(model: object, models: Mapping[str, object], network: NetworkMap, order: list[str]) -> _Resolved:
    raw = _raw_start(model)
    count = model_channel_count(model)
    if getattr(model, "is_submodel", False) and not raw:
        parent_name = str(getattr(model, "parent_name", "") or "")
        parent = models.get(parent_name)
        if parent is None:
            raise StartChannelError(f"unresolvable start channel: parent {parent_name!r} is not in the layout")
        if getattr(parent, "start_channel_error", None):
            raise StartChannelError(str(parent.start_channel_error))
        if getattr(parent, "start_channel", None) is None:
            raise _Wait()
        if getattr(parent, "custom_grid_missing", False):
            raise StartChannelError(
                f"unresolvable start channel: parent {parent_name!r} has no custom-model grid, so submodel node numbers cannot be placed"
            )
        return _from_parent(model, parent)
    if not raw:
        return _chain_from_previous(model, models, network, order, count)
    return _parse_start(raw, model, models, network, count)


def _from_parent(model: object, parent: object) -> _Resolved:
    parent_start = int(parent.start_channel)  # type: ignore[attr-defined]
    numbers = node_numbers(getattr(model, "raw_attrs", {}) or {})
    cpp = channels_per_node(parent)
    if numbers:
        start = parent_start + (min(numbers) - 1) * cpp
        end = parent_start + max(numbers) * cpp - 1
    else:
        start = parent_start
        end = getattr(parent, "end_channel", None)
    if start < 1:
        raise StartChannelError(f"unresolvable start channel: submodel {getattr(model, 'name', '')!r} resolved below channel 1")
    return _Resolved(start=start, end=end if isinstance(end, int) else None, controller=getattr(parent, "controller_name", None))


def _chain_from_previous(
    model: object,
    models: Mapping[str, object],
    network: NetworkMap,
    order: list[str],
    count: int,
) -> _Resolved:
    roots = [name for name in order if not getattr(models[name], "is_submodel", False)]
    name = str(getattr(model, "name", ""))
    if name not in roots:
        raise StartChannelError(f"unresolvable start channel for {name!r}: model is not a top-level model")
    index = roots.index(name)
    if index == 0:
        return _finish(1, count, network, None)
    previous = models[roots[index - 1]]
    if getattr(previous, "start_channel_error", None):
        raise StartChannelError(str(previous.start_channel_error))
    if getattr(previous, "end_channel", None) is None:
        raise _Wait()
    return _finish(int(previous.end_channel) + 1, count, network, getattr(previous, "controller_name", None))  # type: ignore[attr-defined]


def _parse_start(raw: str, model: object, models: Mapping[str, object], network: NetworkMap, count: int) -> _Resolved:
    text = raw.strip()
    if text[:1] in {"@", ">"}:
        return _parse_model_reference(text, model, models, network, count)
    if text.startswith("!"):
        return _parse_controller(text, network, count)
    if text.startswith("#"):
        return _parse_universe(text, network, count)
    if text.startswith(("+", "-")) or text.isdigit() or _is_number(text):
        try:
            start = int(text)
        except ValueError:
            start = int(round(float(text)))
        if start < 1:
            raise StartChannelError(f"unresolvable start channel {text!r}: channel must be >= 1")
        return _finish(start, count, network, None)
    raise StartChannelError(f"unresolvable start channel {text!r}: unrecognized format")


def _parse_model_reference(text: str, model: object, models: Mapping[str, object], network: NetworkMap, count: int) -> _Resolved:
    kind = text[0]
    target, separator, offset_text = text[1:].partition(":")
    target = target.strip()
    if not separator or not target:
        raise StartChannelError(f"unresolvable start channel {text!r}: expected {kind}Model:offset")
    try:
        offset = int(offset_text.strip())
    except ValueError as exc:
        raise StartChannelError(f"unresolvable start channel {text!r}: offset is not an integer") from exc
    own_name = str(getattr(model, "name", ""))
    if target == own_name:
        raise StartChannelError(f"circular start-channel reference: {own_name} -> {own_name}")
    other = models.get(target)
    if other is None:
        raise StartChannelError(f"unresolvable start channel {text!r}: model {target!r} is not in the layout")
    if getattr(other, "start_channel_error", None):
        raise StartChannelError(str(other.start_channel_error))
    if getattr(other, "start_channel", None) is None or (kind == ">" and getattr(other, "end_channel", None) is None):
        raise _Wait()
    if kind == "@":
        start = int(other.start_channel) + offset - 1  # type: ignore[attr-defined]
    else:
        start = int(other.end_channel) + offset  # type: ignore[attr-defined]
    if start < 1:
        raise StartChannelError(f"unresolvable start channel {text!r}: resolved channel {start} is below 1")
    controller = getattr(other, "controller_name", None) or network.controller_for_channel(start)
    return _finish(start, count, network, controller)


def _parse_controller(text: str, network: NetworkMap, count: int) -> _Resolved:
    target, separator, offset_text = text[1:].partition(":")
    target = target.strip()
    if not separator or not target:
        raise StartChannelError(f"unresolvable start channel {text!r}: expected !Controller:offset")
    try:
        offset = int(offset_text.strip())
    except ValueError as exc:
        raise StartChannelError(f"unresolvable start channel {text!r}: offset is not an integer") from exc
    if offset < 1:
        raise StartChannelError(f"unresolvable start channel {text!r}: controller offset must be >= 1")
    controller = network.controller_named(target)
    if controller is None:
        where = "xlights_networks.xml" if network.controllers else "xlights_networks.xml (file missing or empty)"
        raise StartChannelError(f"unresolvable start channel {text!r}: controller {target!r} was not found in {where}")
    return _finish(controller.start_channel + offset - 1, count, network, controller.name)


def _parse_universe(text: str, network: NetworkMap, count: int) -> _Resolved:
    parts = [part.strip() for part in text[1:].split(":")]
    ip: str | None
    try:
        if len(parts) == 2:
            ip = None
            universe = int(parts[0])
            channel = int(parts[1])
        elif len(parts) == 3:
            ip = parts[0]
            universe = int(parts[1])
            channel = int(parts[2])
        else:
            raise ValueError(text)
    except ValueError as exc:
        raise StartChannelError(
            f"unresolvable start channel {text!r}: expected #universe:channel or #ip:universe:channel"
        ) from exc
    if universe < 1 or channel < 1 or not ip and ip is not None:
        raise StartChannelError(f"unresolvable start channel {text!r}: universe and channel must be >= 1")
    if ip == "":
        raise StartChannelError(f"unresolvable start channel {text!r}: controller address is empty")
    found = network.universe(ip, universe)
    if found is None:
        where = "xlights_networks.xml" if network.universes or network.controllers else "xlights_networks.xml (file missing or empty)"
        target = f"{ip} universe {universe}" if ip else f"universe {universe}"
        raise StartChannelError(f"unresolvable start channel {text!r}: {target} is not defined in {where}")
    return _finish(found.start_channel + channel - 1, count, network, found.controller_name)


def _finish(start: int, count: int, network: NetworkMap, controller: str | None) -> _Resolved:
    if start < 1:
        raise StartChannelError(f"unresolvable start channel: resolved channel {start} is below 1")
    end = start + count - 1 if count > 0 else None
    return _Resolved(start=start, end=end, controller=controller or network.controller_for_channel(start))


def _raw_start(model: object) -> str:
    attrs = getattr(model, "raw_attrs", {}) or {}
    for key in _START_KEYS:
        raw = attrs.get(key)
        if raw is not None and str(raw).strip() != "":
            return str(raw).strip()
    return ""


def _mark_resolved(model: object, resolved: _Resolved) -> None:
    model.start_channel = resolved.start  # type: ignore[attr-defined]
    model.end_channel = resolved.end  # type: ignore[attr-defined]
    model.controller_name = resolved.controller  # type: ignore[attr-defined]
    model.start_channel_error = None  # type: ignore[attr-defined]


def _mark_error(model: object, message: str) -> None:
    model.start_channel = None  # type: ignore[attr-defined]
    model.end_channel = None  # type: ignore[attr-defined]
    model.controller_name = None  # type: ignore[attr-defined]
    model.start_channel_error = message  # type: ignore[attr-defined]


def _dependency_name(model: object, models: Mapping[str, object], order: list[str]) -> str | None:
    raw = _raw_start(model)
    if raw[:1] in {"@", ">"}:
        target = raw[1:].partition(":")[0].strip()
        return target or None
    if getattr(model, "is_submodel", False) and not raw:
        return str(getattr(model, "parent_name", "") or "") or None
    if not raw and not getattr(model, "is_submodel", False):
        roots = [name for name in order if not getattr(models[name], "is_submodel", False)]
        name = str(getattr(model, "name", ""))
        if name in roots:
            index = roots.index(name)
            if index > 0:
                return roots[index - 1]
    return None


def _unresolved_message(name: str, models: Mapping[str, object], pending: set[str], order: list[str]) -> str:
    chain = [name]
    seen = {name}
    current = name
    while True:
        dependency = _dependency_name(models[current], models, order)
        if not dependency or dependency not in models:
            return f"unresolvable start channel for {name!r}: dependency {dependency!r} was not resolved"
        if dependency in seen:
            start = chain.index(dependency)
            cycle = chain[start:] + [dependency]
            return "circular start-channel reference: " + " -> ".join(cycle)
        chain.append(dependency)
        seen.add(dependency)
        current = dependency
        if len(chain) > len(models) + 1:
            return "circular start-channel reference: " + " -> ".join(chain)


def _expand_output(
    element: ET.Element,
    name: str,
    ip: str | None,
    next_universe: int,
    absolute_start: int,
) -> tuple[list[UniverseSpan], int, int]:
    tag = _local(element.tag).lower()
    children = [
        child
        for child in list(element)
        if _local(child.tag).lower() in {"network", "output", "controller"} or _is_output_element(child)
    ]
    if children and tag != "network":
        specs: list[UniverseSpan] = []
        total = 0
        cursor = absolute_start
        for child in children:
            child_ip = _ip_address(child) or ip
            child_specs, child_count, next_universe = _expand_one(child, name, child_ip, next_universe, cursor)
            specs.extend(child_specs)
            total += child_count
            cursor += child_count
        return specs, total, next_universe
    return _expand_one(element, name, ip, next_universe, absolute_start)


def _expand_one(
    element: ET.Element,
    name: str,
    ip: str | None,
    next_universe: int,
    absolute_start: int,
) -> tuple[list[UniverseSpan], int, int]:
    attrs = {str(key): str(value) for key, value in element.attrib.items()}
    per = _first_int(attrs, ("MaxChannels", "maxChannels", "ChannelsPerUniverse", "channelsPerUniverse", "UniverseSize", "universeSize"))
    num = _first_int(attrs, ("NumUniverses", "numUniverses", "Universes", "universes"))
    start_universe = _first_int(attrs, ("StartUniverse", "startUniverse", "Universe", "universe"))
    network_type = (attrs.get("NetworkType") or attrs.get("networkType") or "").strip().lower()
    baud = _first_int(attrs, ("BaudRate", "baudRate"))
    if start_universe <= 0 and network_type in _UNIVERSE_TYPES and baud > 0 and num <= 1:
        start_universe = baud
    elif start_universe <= 0 and network_type in _UNIVERSE_TYPES and baud > 1 and num > 1:
        start_universe = baud
    universe_like = network_type in _UNIVERSE_TYPES or start_universe > 0
    if num <= 0 and per > 0 and universe_like:
        num = 1
    if num <= 0:
        channels = per or _first_int(attrs, ("ChannelCount", "channelCount", "Channels", "channels", "NumChannels", "numChannels"))
        return [], channels, next_universe
    if per <= 0:
        per = _DEFAULT_UNIVERSE_SIZE
    if start_universe <= 0:
        start_universe = next_universe
    specs = [
        UniverseSpan(
            universe=start_universe + index,
            start_channel=absolute_start + index * per,
            channels=per,
            ip=ip,
            controller_name=name,
        )
        for index in range(num)
    ]
    return specs, num * per, max(next_universe, start_universe + num)


def _is_output_element(element: ET.Element) -> bool:
    tag = _local(element.tag).lower()
    return any(token in tag for token in ("controller", "network", "output"))


def _controller_name(element: ET.Element, *, fallback: str) -> str:
    for key in ("Name", "name", "Description", "description", "Id", "ID", "id"):
        value = (element.attrib.get(key) or "").strip()
        if value:
            return value
    return fallback


def _ip_address(element: ET.Element) -> str | None:
    for key in ("IP", "ip", "Address", "address"):
        value = (element.attrib.get(key) or "").strip()
        if value:
            return value
    comport = (element.attrib.get("ComPort") or element.attrib.get("Comport") or "").strip()
    network_type = (element.attrib.get("NetworkType") or "").strip().lower()
    if not comport or comport.upper().startswith("COM"):
        return None
    if "." in comport or ":" in comport or network_type in _UNIVERSE_TYPES:
        return comport
    return None


def _first_int(attrs: Mapping[str, str], keys: tuple[str, ...]) -> int:
    for key in keys:
        raw = attrs.get(key)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            return max(0, int(str(raw).strip()))
        except ValueError:
            continue
    return 0


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True
