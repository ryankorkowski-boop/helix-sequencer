from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from tools.build_helpers.helixville4_full_band import add_full_helixville4_band_models


@dataclass(frozen=True)
class PixelRun:
    name: str
    start: int
    end: int

    @property
    def line0(self) -> str:
        return f"{self.start}-{self.end}"

    @property
    def count(self) -> int:
        return self.end - self.start + 1


DRUMMER_SUBMODEL_NAMES: tuple[str, ...] = (
    "HX_SNOWMAN_DRUMMER_HEAD",
    "HX_SNOWMAN_DRUMMER_FACE",
    "HX_SNOWMAN_DRUMMER_HAT",
    "HX_SNOWMAN_DRUMMER_HAT_BAND",
    "HX_SNOWMAN_DRUMMER_HAT_HOLLY",
    "HX_SNOWMAN_DRUMMER_SCARF",
    "HX_SNOWMAN_DRUMMER_TORSO",
    "HX_SNOWMAN_DRUMMER_BUTTONS",
    "HX_SNOWMAN_DRUMMER_LEFT_ARM",
    "HX_SNOWMAN_DRUMMER_RIGHT_ARM",
    "HX_SNOWMAN_DRUMMER_LEFT_STICK",
    "HX_SNOWMAN_DRUMMER_RIGHT_STICK",
    "HX_SNOWMAN_DRUMMER_KICK",
    "HX_SNOWMAN_DRUMMER_KICK_RIM",
    "HX_SNOWMAN_DRUMMER_SNARE",
    "HX_SNOWMAN_DRUMMER_SNARE_RIM",
    "HX_SNOWMAN_DRUMMER_TOM_LEFT",
    "HX_SNOWMAN_DRUMMER_TOM_RIGHT",
    "HX_SNOWMAN_DRUMMER_HI_HAT",
    "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT",
    "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT",
    "HX_SNOWMAN_DRUMMER_STANDS",
    "HX_SNOWMAN_DRUMMER_PLATFORM",
)

DRUMMER_SUBMODEL_PIXEL_COUNTS: dict[str, int] = {
    "HX_SNOWMAN_DRUMMER_HEAD": 44,
    "HX_SNOWMAN_DRUMMER_FACE": 24,
    "HX_SNOWMAN_DRUMMER_HAT": 28,
    "HX_SNOWMAN_DRUMMER_HAT_BAND": 12,
    "HX_SNOWMAN_DRUMMER_HAT_HOLLY": 10,
    "HX_SNOWMAN_DRUMMER_SCARF": 22,
    "HX_SNOWMAN_DRUMMER_TORSO": 56,
    "HX_SNOWMAN_DRUMMER_BUTTONS": 9,
    "HX_SNOWMAN_DRUMMER_LEFT_ARM": 22,
    "HX_SNOWMAN_DRUMMER_RIGHT_ARM": 22,
    "HX_SNOWMAN_DRUMMER_LEFT_STICK": 12,
    "HX_SNOWMAN_DRUMMER_RIGHT_STICK": 12,
    "HX_SNOWMAN_DRUMMER_KICK": 72,
    "HX_SNOWMAN_DRUMMER_KICK_RIM": 48,
    "HX_SNOWMAN_DRUMMER_SNARE": 28,
    "HX_SNOWMAN_DRUMMER_SNARE_RIM": 18,
    "HX_SNOWMAN_DRUMMER_TOM_LEFT": 32,
    "HX_SNOWMAN_DRUMMER_TOM_RIGHT": 32,
    "HX_SNOWMAN_DRUMMER_HI_HAT": 22,
    "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT": 28,
    "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT": 28,
    "HX_SNOWMAN_DRUMMER_STANDS": 44,
    "HX_SNOWMAN_DRUMMER_PLATFORM": 36,
}

DRUMMER_ANIMATION_STATES: tuple[str, ...] = (
    "idle_ready",
    "kick_hit",
    "snare_hit",
    "hi_hat_pulse",
    "tom_fill",
    "cymbal_crash",
    "stick_accent",
    "both_arms_up",
    "downbeat_impact",
)


def _allocate_runs() -> list[PixelRun]:
    runs: list[PixelRun] = []
    cursor = 1
    for name in DRUMMER_SUBMODEL_NAMES:
        count = DRUMMER_SUBMODEL_PIXEL_COUNTS[name]
        runs.append(PixelRun(name=name, start=cursor, end=cursor + count - 1))
        cursor += count
    return runs


def _drummer_custom_model_text(width: int, height: int) -> str:
    grid = [["." for _ in range(width)] for _ in range(height)]
    cursor = 1

    def put_ellipse(cx: float, cy: float, rx: float, ry: float, count: int) -> None:
        nonlocal cursor
        import math

        for idx in range(count):
            angle = (math.tau * idx) / count
            x = int(round(cx + math.cos(angle) * rx))
            y = int(round(cy + math.sin(angle) * ry))
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = str(cursor)
            cursor += 1

    def put_line(x1: float, y1: float, x2: float, y2: float, count: int) -> None:
        nonlocal cursor
        for idx in range(count):
            ratio = 0 if count <= 1 else idx / (count - 1)
            x = int(round(x1 + (x2 - x1) * ratio))
            y = int(round(y1 + (y2 - y1) * ratio))
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = str(cursor)
            cursor += 1

    def put_rect_outline(x1: int, y1: int, x2: int, y2: int, count: int) -> None:
        nonlocal cursor
        points: list[tuple[int, int]] = []
        for x in range(x1, x2 + 1):
            points.append((x, y1))
        for y in range(y1 + 1, y2 + 1):
            points.append((x2, y))
        for x in range(x2 - 1, x1 - 1, -1):
            points.append((x, y2))
        for y in range(y2 - 1, y1, -1):
            points.append((x1, y))
        for idx in range(count):
            x, y = points[int(idx * len(points) / count) % len(points)]
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = str(cursor)
            cursor += 1

    put_ellipse(48, 19, 11, 8, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_HEAD"])
    put_ellipse(48, 20, 5, 3, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_FACE"])
    put_rect_outline(40, 5, 56, 13, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_HAT"])
    put_line(39, 13, 57, 13, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_HAT_BAND"])
    put_ellipse(58, 9, 3, 2, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_HAT_HOLLY"])
    put_line(38, 29, 58, 31, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_SCARF"])
    put_ellipse(48, 43, 17, 15, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_TORSO"])
    put_line(48, 34, 48, 52, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_BUTTONS"])
    put_line(37, 34, 20, 14, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_LEFT_ARM"])
    put_line(59, 34, 76, 14, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_RIGHT_ARM"])
    put_line(20, 14, 15, 3, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_LEFT_STICK"])
    put_line(76, 14, 81, 3, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_RIGHT_STICK"])
    put_ellipse(48, 55, 18, 11, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_KICK"])
    put_ellipse(48, 55, 15, 9, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_KICK_RIM"])
    put_ellipse(27, 48, 8, 5, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_SNARE"])
    put_ellipse(27, 48, 6, 3, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_SNARE_RIM"])
    put_ellipse(35, 40, 9, 5, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_TOM_LEFT"])
    put_ellipse(61, 40, 9, 5, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_TOM_RIGHT"])
    put_ellipse(18, 35, 9, 3, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_HI_HAT"])
    put_ellipse(17, 25, 13, 4, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_CYMBAL_LEFT"])
    put_ellipse(79, 25, 13, 4, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT"])
    put_line(18, 29, 18, 65, 11)
    put_line(79, 29, 79, 65, 11)
    put_line(27, 53, 20, 65, 11)
    put_line(69, 53, 76, 65, 11)
    put_line(8, 68, 88, 68, DRUMMER_SUBMODEL_PIXEL_COUNTS["HX_SNOWMAN_DRUMMER_PLATFORM"])

    return ";".join(",".join(row) for row in grid)


def build_drummer_submodel_runs() -> list[PixelRun]:
    return _allocate_runs()


def add_finished_snowman_drummer_model(models_el: ET.Element, *, start_channel: int = 900400) -> ET.Element:
    width = 96
    height = 72
    total_nodes = sum(DRUMMER_SUBMODEL_PIXEL_COUNTS.values())
    model = ET.SubElement(
        models_el,
        "model",
        {
            "name": "HX_SNOWMAN_DRUMMER",
            "DisplayAs": "Custom",
            "WorldPosX": "345.000",
            "WorldPosY": "-58.000",
            "WorldPosZ": "12.000",
            "StartChannel": str(start_channel),
            "StringType": "RGB Nodes",
            "parm1": str(width),
            "parm2": str(height),
            "CustomWidth": str(width),
            "CustomHeight": str(height),
            "CustomModel": _drummer_custom_model_text(width, height),
            "HelixVisualTarget": "docs/HELIXVILLE4_DRUMMER_TARGET.md",
            "HelixImplementationState": "finished_drummer_v1",
            "HelixAnimationStates": ",".join(DRUMMER_ANIMATION_STATES),
            "HelixNodeCount": str(total_nodes),
        },
    )
    for run in build_drummer_submodel_runs():
        ET.SubElement(
            model,
            "subModel",
            {
                "name": run.name,
                "line0": run.line0,
                "HelixPixelCount": str(run.count),
            },
        )
    return model


def add_finished_helixville4_band_models(layout_path: Path) -> None:
    """Add all approved Helixville4 snowman band models.

    The finished-band helper now delegates to the canonical full-band exporter so
    there is only one approved contract for singer, female singer, guitarist,
    bassist, and drummer geometry/submodels.
    """
    add_full_helixville4_band_models(layout_path)
