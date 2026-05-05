from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def normalize_name(name: str) -> str:
    return " ".join((name or "").lower().replace("_", " ").replace("-", " ").split())


OFFICIAL_DISPLAY_ALIASES = {
    "vert matrix": "matrix",
    "horiz matrix": "matrix",
    "tree 360": "tree",
    "tree flat": "tree",
    "tree ribbon": "tree",
    "tree angled": "tree",
    "modelgroup": "model group",
    "objectgroup": "object group",
    "submodel": "submodel",
    "dmxmovinghead": "dmx moving head",
    "dmxmovingheadadv": "dmx moving head adv",
    "dmxfloodarea": "dmx flood area",
    "dmxfloodlight": "dmx floodlight",
    "dmxgeneral": "dmx general",
    "dmxservo": "dmx servo",
    "dmxservo3d": "dmx servo 3d",
    "dmxservo3axis": "dmx servo 3d",
    "dmxskull": "dmx skull",
    "windowframe": "window frame",
    "candycane": "candy cane",
    "singleline": "single line",
    "polyline": "poly line",
    "channelblock": "channel block",
    "multipoint": "multipoint",
    "terrian": "terrain",
}


def _canonical_display(display_as: str) -> str:
    display = normalize_name(display_as)
    return OFFICIAL_DISPLAY_ALIASES.get(display, display)


def _float_attr(attrs: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = (attrs.get(key) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _int_attr(attrs: dict[str, str], key: str, default: int = 0) -> int:
    raw = (attrs.get(key) or "").strip()
    if not raw:
        return default
    try:
        return int(round(float(raw)))
    except Exception:
        return default


def _first_positive_int(attrs: dict[str, str], *keys: str, default: int = 0) -> int:
    for key in keys:
        value = _int_attr(attrs, key, 0)
        if value > 0:
            return value
    return default


def _parse_csv_models(raw: str) -> list[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


def _parse_point_data(raw: str, origin: tuple[float, float, float]) -> list[tuple[float, float, float]]:
    values: list[float] = []
    for part in (raw or "").split(","):
        token = part.strip()
        if not token:
            continue
        try:
            values.append(float(token))
        except Exception:
            continue
    triples: list[tuple[float, float, float]] = []
    for idx in range(0, len(values), 3):
        chunk = values[idx: idx + 3]
        if len(chunk) < 3:
            break
        triples.append((origin[0] + chunk[0], origin[1] + chunk[1], origin[2] + chunk[2]))
    return triples


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _sample_path(points: list[tuple[float, float, float]], count: int) -> list[tuple[float, float, float]]:
    if not points:
        return []
    if len(points) == 1 or count <= 1:
        return [points[0]]
    seg_lengths = [_distance(points[idx], points[idx + 1]) for idx in range(len(points) - 1)]
    total_len = sum(seg_lengths)
    if total_len <= 0.0001:
        return [points[0] for _ in range(max(1, count))]
    out: list[tuple[float, float, float]] = []
    cumulative = [0.0]
    for length in seg_lengths:
        cumulative.append(cumulative[-1] + length)
    for slot in range(max(1, count)):
        target = 0.0 if count == 1 else (total_len * slot) / max(1, count - 1)
        seg_index = 0
        while seg_index + 1 < len(cumulative) and cumulative[seg_index + 1] < target:
            seg_index += 1
        if seg_index >= len(points) - 1:
            out.append(points[-1])
            continue
        seg_start = points[seg_index]
        seg_end = points[seg_index + 1]
        span = max(0.0001, cumulative[seg_index + 1] - cumulative[seg_index])
        ratio = (target - cumulative[seg_index]) / span
        out.append(
            (
                seg_start[0] + (seg_end[0] - seg_start[0]) * ratio,
                seg_start[1] + (seg_end[1] - seg_start[1]) * ratio,
                seg_start[2] + (seg_end[2] - seg_start[2]) * ratio,
            )
        )
    return out


def _ellipse_points(center: tuple[float, float, float], rx: float, ry: float, count: int) -> list[tuple[float, float, float]]:
    out: list[tuple[float, float, float]] = []
    for idx in range(max(1, count)):
        angle = (math.pi * 2.0 * idx) / max(1, count)
        out.append((center[0] + math.cos(angle) * rx, center[1] + math.sin(angle) * ry, center[2]))
    return out


def _star_outline_points(center: tuple[float, float, float], rx: float, ry: float, count: int, tips: int) -> list[tuple[float, float, float]]:
    vertices: list[tuple[float, float, float]] = []
    point_count = max(3, tips)
    inner_scale = 0.42
    for idx in range(point_count * 2):
        radius_x = rx if idx % 2 == 0 else max(4.0, rx * inner_scale)
        radius_y = ry if idx % 2 == 0 else max(4.0, ry * inner_scale)
        angle = -math.pi / 2.0 + (math.pi * idx / point_count)
        vertices.append((center[0] + math.cos(angle) * radius_x, center[1] + math.sin(angle) * radius_y, center[2]))
    vertices.append(vertices[0])
    return _sample_path(vertices, count)


def _dominant_orientation(points: list[tuple[float, float, float]]) -> str:
    if len(points) < 2:
        return "point"
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    if span_x < 1.0 and span_y >= 1.0:
        return "vertical"
    if span_y < 1.0 and span_x >= 1.0:
        return "horizontal"
    if span_x >= 1.0 and span_y >= 1.0:
        return "diagonal" if abs(span_x - span_y) < max(span_x, span_y) * 0.35 else ("horizontal" if span_x > span_y else "vertical")
    return "point"


def _polyline_curvature(points: list[tuple[float, float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    start = points[0]
    end = points[-1]
    base_len = max(0.0001, _distance(start, end))
    max_dev = 0.0
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    for point in points[1:-1]:
        px = point[0] - start[0]
        py = point[1] - start[1]
        area = abs(dx * py - dy * px)
        max_dev = max(max_dev, area / base_len)
    return max_dev / base_len


def _semantic_type(display_as: str, attrs: dict[str, str], points: list[tuple[float, float, float]]) -> str:
    display = _canonical_display(display_as)
    if display in {"model group", "object group"}:
        return "group"
    if display == "submodel":
        return "submodel"
    if display in {"gridlines", "terrain", "mesh", "ruler"}:
        return "view_object"
    if display in {"dmx flood area", "dmx floodlight"} or ("dmx" in display and any(token in display for token in ("flood", "strobe"))):
        return "flood"
    if display in {"dmx moving head", "dmx moving head adv", "dmx servo", "dmx servo 3d", "dmx skull"}:
        return "spinner"
    if "dmx" in display and any(token in display for token in ("moving", "servo", "skull", "pan", "tilt")):
        return "spinner"
    if display == "dmx general":
        return "line"
    if display.startswith("dmx"):
        return "line"
    if "matrix" in display:
        return "matrix"
    if "image" in display:
        return "image"
    if "tree" in display:
        return "tree"
    if "arches" in display:
        return "arch"
    if "candy cane" in display:
        return "cane"
    if "icicle" in display:
        return "icicle"
    if "window frame" in display:
        return "window"
    if "channel block" in display:
        return "channelblock"
    if "cube" in display:
        return "cube"
    if "single line" in display:
        return "line"
    if "poly line" in display:
        return "arch" if _polyline_curvature(points) >= 0.08 else "line"
    if "circle" in display:
        return "circle"
    if "wreath" in display:
        return "wreath"
    if "star" in display:
        return "star"
    if "spinner" in display or "pinwheel" in display:
        return "spinner"
    if "sphere" in display or "orb" in display:
        return "sphere"
    if "multipoint" in display:
        return "multipoint"
    if "custom" in display:
        return "custom"
    if points:
        if len(points) >= 3 and _polyline_curvature(points) >= 0.08:
            return "arch"
        if len(points) >= 2:
            return "line"
        return "multipoint"
    return "custom"


def _infer_string_counts(display_as: str, semantic_type: str, attrs: dict[str, str], point_count: int) -> tuple[int, int]:
    parm1 = max(0, _int_attr(attrs, "parm1", 0))
    parm2 = max(0, _int_attr(attrs, "parm2", 0))
    parm3 = max(0, _int_attr(attrs, "parm3", 0))
    display = _canonical_display(display_as)

    if semantic_type == "view_object":
        return 1, 1
    if semantic_type in {"group", "submodel"}:
        return 1, 1
    if semantic_type == "flood":
        return 1, max(1, _first_positive_int(attrs, "NumChannels", "parm1", "parm2", default=point_count or 1))

    if semantic_type == "matrix":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", "parm3", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm2", default=1))
        return strings, nodes_per_string
    if semantic_type == "image":
        return 1, 1
    if semantic_type == "tree":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", "parm3", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm2", default=1))
        return strings, nodes_per_string
    if semantic_type == "arch":
        strings = max(1, _first_positive_int(attrs, "NumArches", "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerArch", "NodesPerString", "parm2", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "cane":
        strings = max(1, _first_positive_int(attrs, "NumCanes", "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerCane", "NodesPerString", "parm2", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "icicle":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "LightsPerString", "NodesPerString", "parm2", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "window":
        top_nodes = max(0, _first_positive_int(attrs, "TopNodes", default=0))
        side_nodes = max(0, _first_positive_int(attrs, "SideNodes", default=0))
        bottom_nodes = max(0, _first_positive_int(attrs, "BottomNodes", default=0))
        total = top_nodes + side_nodes * 2 + bottom_nodes
        return 1, max(1, total or point_count or parm1 or parm2 or 1)
    if semantic_type == "channelblock":
        return 1, max(1, _first_positive_int(attrs, "NumChannels", "parm1", "parm2", default=point_count or 1))
    if semantic_type == "cube":
        width = max(1, _first_positive_int(attrs, "CubeWidth", default=parm1 or 1))
        height = max(1, _first_positive_int(attrs, "CubeHeight", default=parm2 or 1))
        depth = max(1, _first_positive_int(attrs, "CubeDepth", default=parm3 or 1))
        return max(1, width * depth), max(1, height)
    if semantic_type == "circle":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm3", "parm2", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "wreath":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm2", "parm3", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "star":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm2", "parm3", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "spinner":
        string_count = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
        arms_per_string = max(1, _first_positive_int(attrs, "ArmsPerString", default=1))
        nodes_per_arm = max(1, _first_positive_int(attrs, "NodesPerArm", "parm2", default=point_count or 1))
        return max(1, string_count * arms_per_string), nodes_per_arm
    if semantic_type == "sphere":
        strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
        nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm2", default=point_count or 1))
        return strings, nodes_per_string
    if semantic_type == "multipoint":
        return 1, max(1, point_count or parm1 or parm2 or 1)
    if semantic_type == "custom":
        width = max(1, _first_positive_int(attrs, "CustomWidth", default=parm1 or 1))
        height = max(1, _first_positive_int(attrs, "CustomHeight", default=parm2 or 1))
        return width, height
    strings = max(1, _first_positive_int(attrs, "NumStrings", "parm1", default=1))
    nodes_per_string = max(1, _first_positive_int(attrs, "NodesPerString", "parm2", "parm3", default=point_count or 1))
    return strings, nodes_per_string


def _infer_color_family(attrs: dict[str, str]) -> str | None:
    haystack = " ".join(
        part
        for part in (
            attrs.get("StringType", ""),
            attrs.get("TagColour", ""),
            attrs.get("CustomColor", ""),
        )
        if part
    ).lower()
    if "#ff0000" in haystack or " red" in f" {haystack} ":
        return "red"
    if "#00ff00" in haystack or " green" in f" {haystack} " or "lime" in haystack:
        return "green"
    if "#ffffff" in haystack or " white" in f" {haystack} ":
        return "white"
    if "rgb" in haystack or "pixel" in haystack:
        return "rgb"
    return None


@dataclass(frozen=True)
class PixelPoint:
    index: int
    x: float
    y: float
    z: float = 0.0
    string_index: int = 0
    node_index: int = 0


@dataclass(frozen=True)
class ModelRegion:
    name: str
    role: str
    pixel_indexes: tuple[int, ...]
    center: tuple[float, float, float]
    source: str = "virtual"


@dataclass
class Model:
    name: str
    display_as: str
    type: str
    strings: int
    nodes_per_string: int
    total_pixels: int
    start_channel: int | None
    coordinates: tuple[float, float, float] | None
    end_coordinates: tuple[float, float, float] | None
    orientation: str | None
    wiring: str | None
    string_type: str
    color_family: str | None
    aliases: list[str] = field(default_factory=list)
    submodels: list[str] = field(default_factory=list)
    geometry_points: list[tuple[float, float, float]] = field(default_factory=list)
    raw_attrs: dict[str, str] = field(default_factory=dict)
    parent_name: str | None = None
    is_submodel: bool = False
    region_role: str | None = None

    def is_pixel_model(self) -> bool:
        return self.total_pixels > 1

    def is_rgb_capable(self) -> bool:
        text = self.string_type.lower()
        if "single color" in text:
            return False
        return any(token in text for token in ("rgb", "pixel", "node", "nodes", "ws2811", "ws2812", "gece"))

    def is_single_color(self) -> bool:
        return "single color" in self.string_type.lower()

    def center(self) -> tuple[float, float, float]:
        points = self.geometry_points or [self.coordinates or (0.0, 0.0, 0.0)]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        zs = [point[2] for point in points]
        return (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))

    def bounding_box(self) -> tuple[float, float, float, float, float, float]:
        points = self.geometry_points or [self.coordinates or (0.0, 0.0, 0.0)]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        zs = [point[2] for point in points]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def pixel_region(self, start_ratio: float, end_ratio: float) -> list[PixelPoint]:
        pixels = self.virtual_pixel_map()
        if not pixels:
            return []
        lo = max(0.0, min(1.0, start_ratio))
        hi = max(lo, min(1.0, end_ratio))
        start_index = int(math.floor(lo * max(0, len(pixels) - 1)))
        end_index = int(math.ceil(hi * max(0, len(pixels) - 1))) + 1
        return pixels[start_index:end_index]

    def virtual_pixel_map(self) -> list[PixelPoint]:
        if self.geometry_points:
            samples = _sample_path(self.geometry_points, max(1, self.total_pixels))
        elif self.coordinates and self.end_coordinates:
            samples = _sample_path([self.coordinates, self.end_coordinates], max(1, self.total_pixels))
        elif self.coordinates:
            samples = [self.coordinates]
        else:
            samples = [(0.0, 0.0, 0.0)]
        return [
            PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
            for idx, point in enumerate(samples)
        ]

    def virtual_regions(self) -> list[ModelRegion]:
        pixels = self.virtual_pixel_map()
        if len(pixels) < 4:
            return []
        orientation = normalize_name(self.orientation or "")
        if self.type == "matrix":
            regions = [
                ("top", 0.0, 0.34),
                ("middle", 0.33, 0.67),
                ("bottom", 0.66, 1.0),
                ("left", 0.0, 0.34),
                ("center", 0.33, 0.67),
                ("right", 0.66, 1.0),
            ]
        elif self.type == "tree":
            regions = [("top", 0.0, 0.28), ("middle", 0.28, 0.68), ("bottom", 0.68, 1.0)]
        elif self.type in {"line", "arch", "cane", "icicle", "window", "channelblock", "multipoint"}:
            if orientation == "vertical":
                regions = [("bottom", 0.0, 0.34), ("middle", 0.33, 0.67), ("top", 0.66, 1.0)]
            else:
                regions = [("left", 0.0, 0.34), ("center", 0.33, 0.67), ("right", 0.66, 1.0)]
        elif self.type in {"circle", "sphere", "wreath"}:
            regions = [("north", 0.0, 0.25), ("east", 0.25, 0.5), ("south", 0.5, 0.75), ("west", 0.75, 1.0)]
        elif self.type == "star":
            regions = [("top", 0.0, 0.2), ("right", 0.2, 0.45), ("bottom", 0.45, 0.7), ("left", 0.7, 1.0)]
        elif self.type == "cube":
            regions = [("front", 0.0, 0.32), ("middle", 0.32, 0.68), ("rear", 0.68, 1.0)]
        else:
            regions = [("lead", 0.0, 0.34), ("middle", 0.33, 0.67), ("tail", 0.66, 1.0)]
        out: list[ModelRegion] = []
        for role, start_ratio, end_ratio in regions:
            segment = self.pixel_region(start_ratio, end_ratio)
            if not segment:
                continue
            indexes = tuple(point.index for point in segment)
            cx = sum(point.x for point in segment) / len(segment)
            cy = sum(point.y for point in segment) / len(segment)
            cz = sum(point.z for point in segment) / len(segment)
            out.append(ModelRegion(name=f"{self.name}/{role.title()}", role=role, pixel_indexes=indexes, center=(cx, cy, cz)))
        return out


@dataclass
class LineModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        samples = _sample_path(self.geometry_points or [self.coordinates or (0.0, 0.0, 0.0), self.end_coordinates or self.coordinates or (0.0, 0.0, 0.0)], max(1, self.total_pixels))
        return [
            PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
            for idx, point in enumerate(samples)
        ]


@dataclass
class CaneModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        canes = max(1, self.strings)
        nodes = max(1, self.nodes_per_string)
        center = self.coordinates or (0.0, 0.0, 0.0)
        width = max(18.0, abs((self.end_coordinates or center)[0] - center[0]) or (_float_attr(self.raw_attrs, "ScaleX", 1.0) * 18.0))
        height = max(36.0, abs((self.end_coordinates or center)[1] - center[1]) or (_float_attr(self.raw_attrs, "ScaleY", 1.0) * 42.0))
        spacing = max(18.0, width * 0.95)
        out: list[PixelPoint] = []
        index = 0
        total_width = spacing * max(0, canes - 1)
        start_x = center[0] - (total_width / 2.0)
        upright_ratio = 0.62
        for cane_index in range(canes):
            cane_x = start_x + cane_index * spacing
            upright_h = height * upright_ratio
            hook_radius = max(6.0, width * 0.35)
            path = [
                (cane_x, center[1] - height * 0.5, center[2]),
                (cane_x, center[1] - height * 0.5 + upright_h, center[2]),
                (cane_x + hook_radius, center[1] + height * 0.5, center[2]),
            ]
            samples = _sample_path(path, nodes)
            for node_index, point in enumerate(samples):
                out.append(PixelPoint(index=index, x=point[0], y=point[1], z=point[2], string_index=cane_index, node_index=node_index))
                index += 1
        return out


@dataclass
class MatrixModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        cols = max(1, self.strings)
        rows = max(1, self.nodes_per_string)
        center = self.coordinates or (0.0, 0.0, 0.0)
        end = self.end_coordinates or (center[0] + float(cols - 1), center[1] + float(rows - 1), center[2])
        width = max(1.0, abs(end[0] - center[0]))
        height = max(1.0, abs(end[1] - center[1]))
        origin_x = center[0] - (width * 0.5)
        origin_y = center[1] - (height * 0.5)
        out: list[PixelPoint] = []
        index = 0
        for string_index in range(cols):
            x = origin_x + (width * (string_index / max(1, cols - 1)))
            for node_index in range(rows):
                y = origin_y + (height * (node_index / max(1, rows - 1)))
                out.append(PixelPoint(index=index, x=x, y=y, z=center[2], string_index=string_index, node_index=node_index))
                index += 1
        return out


@dataclass
class TreeModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        strings = max(1, self.strings)
        nodes = max(1, self.nodes_per_string)
        center = self.coordinates or (0.0, 0.0, 0.0)
        radius = max(12.0, abs((self.end_coordinates or center)[0] - center[0]) * 0.5 + 18.0)
        height = max(24.0, abs((self.end_coordinates or center)[1] - center[1]) + 24.0)
        out: list[PixelPoint] = []
        index = 0
        for string_index in range(strings):
            angle = (math.pi * 2.0 * string_index) / max(1, strings)
            base_x = center[0] + math.cos(angle) * radius
            for node_index in range(nodes):
                y = center[1] - (height * (node_index / max(1, nodes - 1)))
                out.append(PixelPoint(index=index, x=base_x, y=y, z=center[2], string_index=string_index, node_index=node_index))
                index += 1
        return out


@dataclass
class SpinnerVirtualModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        arms = max(1, self.strings)
        nodes = max(1, self.nodes_per_string)
        center = self.coordinates or (0.0, 0.0, 0.0)
        radius = max(16.0, abs((self.end_coordinates or center)[0] - center[0]) * 0.5 + 22.0)
        out: list[PixelPoint] = []
        index = 0
        for arm_index in range(arms):
            angle = (math.pi * 2.0 * arm_index) / max(1, arms)
            for node_index in range(nodes):
                ratio = (node_index + 1) / max(1, nodes)
                x = center[0] + math.cos(angle) * radius * ratio
                y = center[1] + math.sin(angle) * radius * ratio
                out.append(PixelPoint(index=index, x=x, y=y, z=center[2], string_index=arm_index, node_index=node_index))
                index += 1
        return out


@dataclass
class SphereModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        longs = max(1, self.strings)
        lats = max(1, self.nodes_per_string)
        center = self.coordinates or (0.0, 0.0, 0.0)
        rx = max(12.0, _float_attr(self.raw_attrs, "ScaleX", 1.6) * 12.0)
        ry = max(12.0, _float_attr(self.raw_attrs, "ScaleY", 1.6) * 12.0)
        out: list[PixelPoint] = []
        index = 0
        for lon in range(longs):
            theta = (math.pi * 2.0 * lon) / max(1, longs)
            for lat in range(lats):
                phi = -math.pi / 2.0 + (math.pi * lat) / max(1, lats - 1)
                x = center[0] + math.cos(theta) * math.cos(phi) * rx
                y = center[1] + math.sin(phi) * ry
                z = center[2] + math.sin(theta) * math.cos(phi) * rx
                out.append(PixelPoint(index=index, x=x, y=y, z=z, string_index=lon, node_index=lat))
                index += 1
        return out


@dataclass
class CircleModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        center = self.coordinates or (0.0, 0.0, 0.0)
        rx = max(8.0, _float_attr(self.raw_attrs, "ScaleX", 1.0) * 12.0)
        ry = max(8.0, _float_attr(self.raw_attrs, "ScaleY", 1.0) * 12.0)
        samples = _ellipse_points(center, rx, ry, max(1, self.total_pixels))
        return [
            PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
            for idx, point in enumerate(samples)
        ]


@dataclass
class StarModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        center = self.coordinates or (0.0, 0.0, 0.0)
        rx = max(10.0, _float_attr(self.raw_attrs, "ScaleX", 1.0) * 10.0)
        ry = max(10.0, _float_attr(self.raw_attrs, "ScaleY", 1.0) * 10.0)
        tips = max(5, _int_attr(self.raw_attrs, "parm3", 5))
        samples = _star_outline_points(center, rx, ry, max(1, self.total_pixels), tips)
        return [
            PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
            for idx, point in enumerate(samples)
        ]


@dataclass
class IcicleModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        strings = max(1, self.strings)
        nodes = max(1, self.nodes_per_string)
        center = self.coordinates or (0.0, 0.0, 0.0)
        spacing = max(10.0, abs((self.end_coordinates or center)[0] - center[0]) / max(1, strings - 1) if strings > 1 else 12.0)
        drops = [int(piece) for piece in re.findall(r"\d+", self.raw_attrs.get("DropPattern", ""))]
        if not drops:
            drops = [nodes, max(1, nodes - 2), max(1, nodes - 4), max(1, nodes - 1)]
        total_width = spacing * max(0, strings - 1)
        start_x = center[0] - (total_width / 2.0)
        out: list[PixelPoint] = []
        index = 0
        for string_index in range(strings):
            drop_len = max(1, drops[string_index % len(drops)])
            x = start_x + string_index * spacing
            for node_index in range(nodes):
                ratio = node_index / max(1, nodes - 1)
                y = center[1] - (drop_len * ratio * 6.0)
                out.append(PixelPoint(index=index, x=x, y=y, z=center[2], string_index=string_index, node_index=node_index))
                index += 1
        return out


@dataclass
class WindowFrameVirtualModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        center = self.coordinates or (0.0, 0.0, 0.0)
        top = max(1, _first_positive_int(self.raw_attrs, "TopNodes", default=max(1, self.nodes_per_string // 4)))
        side = max(1, _first_positive_int(self.raw_attrs, "SideNodes", default=max(1, self.nodes_per_string // 6)))
        bottom = max(1, _first_positive_int(self.raw_attrs, "BottomNodes", default=top))
        width = max(float(max(top, bottom)) * 6.0, 24.0)
        height = max(float(side) * 6.0, 18.0)
        path = [
            (center[0] - width / 2.0, center[1] - height / 2.0, center[2]),
            (center[0] - width / 2.0, center[1] + height / 2.0, center[2]),
            (center[0] + width / 2.0, center[1] + height / 2.0, center[2]),
            (center[0] + width / 2.0, center[1] - height / 2.0, center[2]),
            (center[0] - width / 2.0, center[1] - height / 2.0, center[2]),
        ]
        samples = _sample_path(path, max(1, top + top + side + side))
        return [
            PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
            for idx, point in enumerate(samples)
        ]


@dataclass
class CubeVirtualModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        width = max(1, _first_positive_int(self.raw_attrs, "CubeWidth", default=max(1, self.strings // 2)))
        height = max(1, _first_positive_int(self.raw_attrs, "CubeHeight", default=max(1, self.nodes_per_string)))
        depth = max(1, _first_positive_int(self.raw_attrs, "CubeDepth", default=2))
        center = self.coordinates or (0.0, 0.0, 0.0)
        scale = 8.0
        out: list[PixelPoint] = []
        index = 0
        for z_index in range(depth):
            for x_index in range(width):
                for y_index in range(height):
                    x = center[0] + (x_index - (width - 1) / 2.0) * scale + z_index * (scale * 0.45)
                    y = center[1] + (y_index - (height - 1) / 2.0) * scale - z_index * (scale * 0.35)
                    z = center[2] + (z_index - (depth - 1) / 2.0) * scale
                    out.append(PixelPoint(index=index, x=x, y=y, z=z, string_index=z_index * width + x_index, node_index=y_index))
                    index += 1
        return out


@dataclass
class MultiPointModel(Model):
    def virtual_pixel_map(self) -> list[PixelPoint]:
        if self.geometry_points:
            return [
                PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
                for idx, point in enumerate(self.geometry_points)
            ]
        center = self.coordinates or (0.0, 0.0, 0.0)
        radius = max(8.0, _float_attr(self.raw_attrs, "ScaleX", 1.2) * 8.0)
        samples = _ellipse_points(center, radius, radius * 0.7, max(1, self.total_pixels))
        return [
            PixelPoint(index=idx, x=point[0], y=point[1], z=point[2], string_index=0, node_index=idx)
            for idx, point in enumerate(samples)
        ]


@dataclass
class CustomModel(Model):
    pass


@dataclass
class ModelGroup:
    name: str
    models: list[str]
    coordinates: tuple[float, float] | None
    raw_attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedLayout:
    path: Path
    models: dict[str, Model]
    groups: dict[str, ModelGroup]
    aliases: dict[str, str]

    def model_for(self, name: str) -> Model | None:
        target = normalize_name(name)
        if target in self.aliases:
            return self.models.get(self.aliases[target])
        for model_name, model in self.models.items():
            if normalize_name(model_name) == target:
                return model
        return None

    def coordinate_map(self, available_names: list[str]) -> dict[str, tuple[float, float]]:
        out: dict[str, tuple[float, float]] = {}
        for name in available_names:
            model = self.model_for(name)
            if model is not None:
                center = model.center()
                out[name] = (center[0], center[1])
                continue
            group_name = self.aliases.get(normalize_name(name), name)
            group = self.groups.get(group_name)
            if group is not None and group.coordinates is not None:
                out[name] = group.coordinates
        return out

    def model_names_by_type(self, *semantic_types: str) -> list[str]:
        wanted = {normalize_name(item) for item in semantic_types}
        return [name for name, model in self.models.items() if normalize_name(model.type) in wanted]

    def pixel_capable_models(self) -> list[str]:
        return [name for name, model in self.models.items() if model.is_pixel_model()]

    def root_models(self) -> list[str]:
        return [name for name, model in self.models.items() if not model.is_submodel]

    def submodel_names(self) -> list[str]:
        return [name for name, model in self.models.items() if model.is_submodel]

    def preferred_sequence_targets(self, name: str, category: str | None = None, *, limit: int | None = None) -> list[str]:
        model = self.model_for(name)
        if model is None:
            return [name]
        if model.is_submodel or not model.submodels:
            return [model.name]
        preferred = [self.models[sub_name] for sub_name in model.submodels if sub_name in self.models]
        if not preferred:
            return [model.name]
        ranked = sorted(preferred, key=lambda item: _submodel_rank(item, category or ""))
        count = limit if limit is not None else _submodel_limit(category or "", model.type)
        chosen = [item.name for item in ranked[: max(1, count)]]
        return chosen if chosen else [model.name]


def _model_from_xml(model_el: ET.Element) -> Model:
    attrs = dict(model_el.attrib)
    name = (attrs.get("name") or "").strip()
    display_as = (attrs.get("DisplayAs") or "Custom").strip()
    origin = (
        _float_attr(attrs, "WorldPosX", 0.0),
        _float_attr(attrs, "WorldPosY", 0.0),
        _float_attr(attrs, "WorldPosZ", 0.0),
    )
    delta = (
        origin[0] + _float_attr(attrs, "X2", 0.0),
        origin[1] + _float_attr(attrs, "Y2", 0.0),
        origin[2] + _float_attr(attrs, "Z2", 0.0),
    )
    geometry_points = _parse_point_data(attrs.get("PointData", ""), origin)
    if not geometry_points and (delta != origin):
        geometry_points = [origin, delta]
    semantic_type = _semantic_type(display_as, attrs, geometry_points or [origin, delta])
    strings, nodes_per_string = _infer_string_counts(display_as, semantic_type, attrs, len(geometry_points))
    total_pixels = max(1, strings * nodes_per_string)
    aliases = [child.attrib.get("name", "").strip() for child in model_el.findall("./Aliases/alias") if child.attrib.get("name", "").strip()]
    string_type = (attrs.get("StringType") or "").strip()
    wiring = " ".join(part for part in (attrs.get("StartSide", ""), attrs.get("Dir", ""), attrs.get("StarStartLocation", "")) if part).strip() or None
    orientation = _dominant_orientation(geometry_points or [origin, delta])
    model_cls: type[Model]
    if semantic_type == "matrix":
        model_cls = MatrixModel
    elif semantic_type == "image":
        model_cls = CustomModel
    elif semantic_type == "tree":
        model_cls = TreeModel
    elif semantic_type == "spinner":
        model_cls = SpinnerVirtualModel
    elif semantic_type == "sphere":
        model_cls = SphereModel
    elif semantic_type in {"line", "arch"}:
        model_cls = LineModel
    elif semantic_type == "cane":
        model_cls = CaneModel
    elif semantic_type == "icicle":
        model_cls = IcicleModel
    elif semantic_type == "window":
        model_cls = WindowFrameVirtualModel
    elif semantic_type == "cube":
        model_cls = CubeVirtualModel
    elif semantic_type in {"channelblock", "multipoint"}:
        model_cls = MultiPointModel
    elif semantic_type == "circle":
        model_cls = CircleModel
    elif semantic_type == "wreath":
        model_cls = CircleModel
    elif semantic_type == "star":
        model_cls = StarModel
    else:
        model_cls = CustomModel
    return model_cls(
        name=name,
        display_as=display_as,
        type=semantic_type,
        strings=max(1, strings),
        nodes_per_string=max(1, nodes_per_string),
        total_pixels=max(1, total_pixels),
        start_channel=_int_attr(attrs, "StartChannel", 0) or None,
        coordinates=origin,
        end_coordinates=delta,
        orientation=orientation,
        wiring=wiring,
        string_type=string_type,
        color_family=_infer_color_family(attrs),
        aliases=aliases,
        submodels=[],
        geometry_points=geometry_points,
        raw_attrs=attrs,
        parent_name=None,
        is_submodel=False,
        region_role=None,
    )


def _submodel_limit(category: str, semantic_type: str) -> int:
    key = normalize_name(category)
    if key in {"matrix", "talking_heads"}:
        return 4
    if key in {"spinner", "sphere", "stars", "snowflakes"}:
        return 4
    if key in {"line", "arch", "mega", "gt"}:
        return 3
    if normalize_name(semantic_type) in {"matrix", "tree"}:
        return 3
    return 2


def _infer_submodel_role(name: str) -> str:
    norm = normalize_name(name)
    checks = (
        ("mouth", ("mouth", "jaw", "sing", "lyric")),
        ("eye", ("eye", "eyes", "pupil")),
        ("outline", ("outline", "frame", "border")),
        ("top", ("top", "upper", "north")),
        ("bottom", ("bottom", "lower", "south")),
        ("left", ("left", "west")),
        ("right", ("right", "east")),
        ("center", ("center", "centre", "middle", "mid")),
        ("arm", ("arm", "branch", "spoke")),
        ("inner", ("inner", "inside")),
        ("outer", ("outer", "outside")),
    )
    for role, tokens in checks:
        if any(token in norm for token in tokens):
            return role
    return "detail"


def _submodel_rank(model: Model, category: str) -> tuple[int, str]:
    role = normalize_name(model.region_role or _infer_submodel_role(model.name))
    category_key = normalize_name(category)
    if category_key == "talking_heads":
        priority = {"mouth": 0, "eye": 1, "outline": 2, "center": 3, "detail": 4}
    elif category_key == "matrix":
        priority = {"top": 0, "center": 1, "middle": 1, "bottom": 2, "left": 3, "right": 4, "detail": 5}
    elif category_key in {"line", "arch", "mega", "gt"}:
        priority = {"left": 0, "bottom": 0, "center": 1, "middle": 1, "right": 2, "top": 2, "detail": 3}
    elif category_key in {"spinner", "sphere", "stars", "snowflakes"}:
        priority = {"arm": 0, "outer": 1, "inner": 2, "top": 3, "left": 4, "right": 5, "bottom": 6, "detail": 7}
    else:
        priority = {"top": 0, "left": 1, "center": 2, "middle": 2, "right": 3, "bottom": 4, "detail": 5}
    return (priority.get(role, 99), normalize_name(model.name))


def _parse_submodel_indexes(raw: str) -> list[int]:
    indexes: set[int] = set()
    for token in re.findall(r"\d+\s*-\s*\d+|\d+", raw or ""):
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text.strip())
            end = int(end_text.strip())
            lo, hi = sorted((start, end))
            for value in range(lo, hi + 1):
                indexes.add(value - 1)
        else:
            indexes.add(int(token) - 1)
    return sorted(index for index in indexes if index >= 0)


def _submodel_geometry(parent: Model, sub_el: ET.Element) -> tuple[list[tuple[float, float, float]], str | None]:
    attrs = dict(sub_el.attrib)
    indexes: list[int] = []
    for key, value in attrs.items():
        if key.lower().startswith("line"):
            indexes.extend(_parse_submodel_indexes(value))
    if not indexes and attrs.get("subBuffer"):
        indexes.extend(_parse_submodel_indexes(attrs.get("subBuffer", "")))
    parent_pixels = parent.virtual_pixel_map()
    if indexes and parent_pixels:
        seen: set[int] = set()
        subset = [parent_pixels[idx] for idx in indexes if 0 <= idx < len(parent_pixels) and idx not in seen and not seen.add(idx)]
        if subset:
            return ([(point.x, point.y, point.z) for point in subset], None)
    role = _infer_submodel_role(attrs.get("name", ""))
    for region in parent.virtual_regions():
        if normalize_name(region.role) == normalize_name(role):
            return ([(point.x, point.y, point.z) for point in parent.pixel_region(0.0, 1.0) if point.index in set(region.pixel_indexes)], role)
    return (parent.geometry_points[:] if parent.geometry_points else [(parent.center())], role)


def _build_submodel(parent: Model, sub_el: ET.Element) -> Model | None:
    attrs = dict(sub_el.attrib)
    short_name = (attrs.get("name") or "").strip()
    if not short_name:
        return None
    full_name = f"{parent.name}/{short_name}"
    geometry_points, role = _submodel_geometry(parent, sub_el)
    origin = geometry_points[0] if geometry_points else (parent.center())
    delta = geometry_points[-1] if geometry_points else origin
    aliases = [child.attrib.get("name", "").strip() for child in sub_el.findall("./aliases/alias") if child.attrib.get("name", "").strip()]
    model_cls: type[Model]
    semantic_type = parent.type
    if semantic_type == "matrix":
        model_cls = MatrixModel
    elif semantic_type == "spinner":
        model_cls = SpinnerVirtualModel
    elif semantic_type == "sphere":
        model_cls = SphereModel
    elif semantic_type == "tree":
        model_cls = TreeModel
    elif semantic_type in {"line", "arch"}:
        model_cls = LineModel
    elif semantic_type == "cane":
        model_cls = CaneModel
    elif semantic_type == "icicle":
        model_cls = IcicleModel
    elif semantic_type == "window":
        model_cls = WindowFrameVirtualModel
    elif semantic_type == "cube":
        model_cls = CubeVirtualModel
    elif semantic_type in {"channelblock", "multipoint"}:
        model_cls = MultiPointModel
    elif semantic_type == "circle":
        model_cls = CircleModel
    elif semantic_type == "wreath":
        model_cls = CircleModel
    elif semantic_type == "star":
        model_cls = StarModel
    else:
        model_cls = CustomModel
    total_pixels = max(1, len(geometry_points) if geometry_points else max(1, parent.total_pixels // 3))
    return model_cls(
        name=full_name,
        display_as="SubModel",
        type=semantic_type,
        strings=max(1, parent.strings),
        nodes_per_string=max(1, min(parent.nodes_per_string, total_pixels)),
        total_pixels=total_pixels,
        start_channel=parent.start_channel,
        coordinates=origin,
        end_coordinates=delta,
        orientation=_dominant_orientation(geometry_points or [origin, delta]),
        wiring=parent.wiring,
        string_type=parent.string_type,
        color_family=parent.color_family,
        aliases=aliases,
        submodels=[],
        geometry_points=geometry_points,
        raw_attrs=attrs,
        parent_name=parent.name,
        is_submodel=True,
        region_role=role or _infer_submodel_role(short_name),
    )


def _parse_layout_uncached(layout_path: Path) -> ParsedLayout:
    tree = ET.parse(layout_path)
    root = tree.getroot()
    models: dict[str, Model] = {}
    groups: dict[str, ModelGroup] = {}
    aliases: dict[str, str] = {}

    for model_el in root.findall(".//models/model"):
        model = _model_from_xml(model_el)
        if not model.name:
            continue
        models[model.name] = model
        aliases[normalize_name(model.name)] = model.name
        for alias in model.aliases:
            aliases[normalize_name(alias)] = model.name
        submodels: list[str] = []
        for sub_el in model_el.findall("./subModel"):
            submodel = _build_submodel(model, sub_el)
            if submodel is None or not submodel.name:
                continue
            models[submodel.name] = submodel
            aliases[normalize_name(submodel.name)] = submodel.name
            aliases[normalize_name(f"{model.name}/{(sub_el.attrib.get('name') or '').strip()}")] = submodel.name
            for alias in submodel.aliases:
                aliases[normalize_name(alias)] = submodel.name
                aliases[normalize_name(f"{model.name}/{alias}")] = submodel.name
            submodels.append(submodel.name)
        model.submodels = submodels

    for group_el in root.findall(".//modelGroups/modelGroup"):
        attrs = dict(group_el.attrib)
        name = (attrs.get("name") or "").strip()
        if not name:
            continue
        coords: tuple[float, float] | None = None
        if attrs.get("centrex") or attrs.get("centrey"):
            coords = (_float_attr(attrs, "centrex", 0.0), _float_attr(attrs, "centrey", 0.0))
        group = ModelGroup(
            name=name,
            models=_parse_csv_models(attrs.get("models", "")),
            coordinates=coords,
            raw_attrs=attrs,
        )
        groups[name] = group
        aliases[normalize_name(name)] = name

    return ParsedLayout(path=layout_path, models=models, groups=groups, aliases=aliases)


@lru_cache(maxsize=8)
def _parse_layout_cached(path_str: str, mtime_ns: int) -> ParsedLayout:
    return _parse_layout_uncached(Path(path_str))


def parse_layout(layout_path: Path) -> ParsedLayout:
    resolved = layout_path.resolve()
    stat = resolved.stat()
    return _parse_layout_cached(str(resolved), int(stat.st_mtime_ns))
