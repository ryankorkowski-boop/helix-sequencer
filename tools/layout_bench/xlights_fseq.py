"""Render Helix sequences with xLights and read the FSEQ channel data.

This module does not simulate effects. Pixel colors come from an FSEQ file
written by xLights --headless (AppImage 2026.19 or another build on PATH).
"""

from __future__ import annotations

import os
import shutil
from tempfile import TemporaryDirectory
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from core import model_parser as xmp
from core.output_provenance import sha256
from tools.fseq_pixel_preview import FseqReader
from tools.layout_bench.render_cache import cached_render, publish_render


DEFAULT_XLIGHTS = Path("/tmp/xlights/squashfs-root/AppRun")


class FseqData:
    """Stream absolute channel rows, reconstructing dark gaps between sparse ranges."""

    def __init__(self, path: Path):
        self.reader = FseqReader(path)
        info = self.reader.info
        self.frames = info.frames
        self.step_ms = info.step_ms
        self.sparse_start = info.ranges[0][0] if info.ranges else 0
        self.channels = (sum(info.ranges[-1]) - self.sparse_start
                         if info.ranges else info.channels)

    def fps(self) -> float:
        return 1000.0 / self.step_ms

    def rows(self):
        ranges = self.reader.info.ranges
        for frame in self.reader.iter_frames():
            packed = np.frombuffer(frame, dtype=np.uint8)
            if len(ranges) < 2:
                yield packed
                continue
            result = np.zeros(self.channels, dtype=np.uint8)
            offset = 0
            for start, length in ranges:
                column = start - self.sparse_start
                result[column:column + length] = packed[offset:offset + length]
                offset += length
            yield result


def load_fseq(path: Path) -> FseqData:
    return FseqData(path)


def xlights_binary() -> Path:
    env = os.environ.get("XLIGHTS_BIN")
    if env:
        path = Path(env)
        if path.exists():
            return path
    if DEFAULT_XLIGHTS.exists():
        return DEFAULT_XLIGHTS
    found = shutil.which("xLights") or shutil.which("xlights")
    if found:
        return Path(found)
    raise FileNotFoundError(
        "xLights binary not found. Set XLIGHTS_BIN to the AppImage or extracted AppRun."
    )


def _media_name(xsq_path: Path) -> str:
    root = ET.parse(xsq_path).getroot()
    node = root.find("./head/mediaFile")
    if node is not None and (node.text or "").strip():
        return Path(node.text.strip()).name
    return ""


def _channel_extent(layout_xml: Path) -> int:
    parsed = xmp.parse_layout(layout_xml)
    extent = 1
    for model in parsed.models.values():
        if model.is_submodel or not model.start_channel:
            continue
        width = 3 if model.is_rgb_capable() else 1
        extent = max(extent, int(model.start_channel) - 1 + model.total_pixels * width)
    return extent


def render_sequence_to_fseq(
    *,
    layout_xml: Path,
    xsq_path: Path,
    media_path: Path,
    fseq_path: Path,
    show_dir: Path,
) -> str:
    """Run xLights --headless. Returns the version string from the log."""
    binary = xlights_binary().resolve()
    executable = binary.parent / "usr/bin/xLights" if binary.name == "AppRun" else binary
    inputs = {
        "layout": sha256(layout_xml), "sequence": sha256(xsq_path), "media": sha256(media_path),
        "xlights": sha256(executable), "launcher": sha256(binary),
        "bench": sha256(__file__), "parser": sha256(xmp.__file__),
    }
    receipt = cached_render(fseq_path, inputs)
    if receipt:
        return receipt["version"]
    show_dir.mkdir(parents=True, exist_ok=True)
    # Concurrent renders and failed retries must not remove one another's show or log.
    with TemporaryDirectory(dir=show_dir, prefix="run-") as workspace:
        work = Path(workspace)
        try:
            produced, version = _run_xlights(binary, layout_xml, xsq_path, media_path, work)
            for _ in FseqReader(produced).iter_frames():
                pass
            fseq_path.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=fseq_path.parent) as staging:
                staged = Path(staging) / fseq_path.name
                shutil.copyfile(produced, staged)
                publish_render(staged, fseq_path, inputs, version=version)
            return version
        finally:
            log = work / "xlights.log"
            if log.is_file():
                log.replace(show_dir / "xlights.log")


def _run_xlights(binary: Path, layout_xml: Path, xsq_path: Path, media_path: Path,
                 show_dir: Path) -> tuple[Path, str]:
    show_dir = show_dir.resolve()
    shutil.copy2(layout_xml, show_dir / "xlights_rgbeffects.xml")
    channels = _channel_extent(layout_xml)
    networks = f"""<?xml version="1.0" encoding="UTF-8"?>
<Networks computer="bench" GlobalFPPProxy="" GlobalForceLocalIP="" DisableOutput="1">
  <network NetworkType="NULL" Description="Null" MaxChannels="{channels}" BaudRate="115200" ComPort="1"/>
</Networks>
"""
    (show_dir / "xlights_networks.xml").write_text(networks, encoding="utf-8")
    staged_xsq = show_dir / xsq_path.name
    shutil.copy2(xsq_path, staged_xsq)
    media_file = _media_name(xsq_path) or media_path.name
    link = show_dir / media_file
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(media_path.resolve())
    out_dir = show_dir / "fseq"
    out_dir.mkdir()
    log_path = show_dir / "xlights.log"
    env = os.environ.copy()
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    home = show_dir / "home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    cmd = [
        "xvfb-run",
        "-a",
        "-s",
        "-screen 0 1280x1024x24",
        str(binary),
        "--headless",
        "-q",
        "-s",
        str(show_dir),
        "--outputdir",
        str(out_dir),
        str(staged_xsq),
    ]
    with log_path.open("w") as log:
        completed = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    produced = out_dir / f"{xsq_path.stem}.fseq"
    if completed.returncode != 0 or not produced.exists():
        tail = log_text[-1500:]
        raise RuntimeError(
            f"xLights --headless failed for {xsq_path.name} (exit {completed.returncode}).\n{tail}"
        )
    version = "unknown"
    spdlog = home / ".local" / "state" / "xLights" / "xLights_spdlog.log"
    haystacks = [log_text]
    if spdlog.exists():
        haystacks.append(spdlog.read_text(encoding="utf-8", errors="replace"))
    for text in haystacks:
        for line in text.splitlines():
            if "Version:" in line and "WX Version" not in line:
                version = line.split("Version:")[-1].strip()
    return produced, version


BULB_COLORS = (
    (255, 0, 64),
    (0, 240, 255),
    (255, 230, 0),
    (255, 43, 214),
    (57, 255, 20),
    (68, 102, 255),
)


def _hex_color(model: xmp.Model) -> tuple[int, int, int]:
    raw = (model.raw_attrs.get("CustomColor") or "").strip()
    parsed = None
    if raw.startswith("#") and len(raw) == 7:
        try:
            parsed = tuple(int(raw[i : i + 2], 16) for i in (1, 3, 5))
        except ValueError:
            parsed = None
    if not model.is_rgb_capable() or model.total_pixels <= 1:
        return saturated_bulb(model.name, parsed)
    if parsed is None:
        return saturated_bulb(model.name, None)
    if _is_neutral(parsed):
        return saturated_bulb(model.name, parsed)
    return parsed  # type: ignore[return-value]


def _is_neutral(color: tuple[int, int, int]) -> bool:
    spread = max(color) - min(color)
    return spread < 40 or min(color) > 210


def saturated_bulb(name: str, custom: tuple[int, int, int] | None) -> tuple[int, int, int]:
    """AC bulbs render as saturated color. White and gray are not the bulb color."""
    if custom is not None and not _is_neutral(custom) and max(custom) > 160:
        return custom
    return BULB_COLORS[sum(ord(char) for char in name) % len(BULB_COLORS)]


def build_node_drawlist(layout_xml: Path, width: int, height: int, header_h: int = 36) -> dict:
    """Map each root-model node to panel pixels and an FSEQ channel index."""
    parsed = xmp.parse_layout(layout_xml)
    roots = [model for model in parsed.models.values() if not model.is_submodel and model.name]
    xs: list[float] = []
    ys: list[float] = []
    prepared = []
    for model in roots:
        pixels = model.virtual_pixel_map()
        points = [(point.x, point.y) for point in pixels] if pixels else []
        if len(points) < 2 and model.geometry_points:
            points = [(point[0], point[1]) for point in model.geometry_points]
        if not points and model.coordinates:
            points = [(model.coordinates[0], model.coordinates[1])]
        xs.extend(point[0] for point in points)
        ys.extend(point[1] for point in points)
        prepared.append((model, points))
    if not xs:
        xs, ys = [0.0, 1.0], [0.0, 1.0]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(1.0, max_x - min_x)
    span_y = max(1.0, max_y - min_y)
    margin = 8
    draw_w = width - margin * 2
    draw_h = height - header_h - margin
    scale = min(draw_w / span_x, draw_h / span_y)
    offset_x = margin + (draw_w - span_x * scale) / 2.0
    offset_y = header_h + (draw_h - span_y * scale) / 2.0

    def project(x: float, y: float) -> tuple[int, int]:
        px = int(round(offset_x + (x - min_x) * scale))
        py = int(round(offset_y + (max_y - y) * scale))
        return px, py

    nodes_xy: list[tuple[int, int]] = []
    nodes_ch: list[int] = []
    nodes_rgb: list[bool] = []
    nodes_color: list[tuple[int, int, int]] = []
    nodes_model: list[str] = []
    strands: list[tuple[str, list[tuple[int, int]], tuple[int, int, int], int]] = []
    for model, points in prepared:
        if not model.start_channel:
            continue
        rgb = model.is_rgb_capable()
        per = 3 if rgb else 1
        origin = int(model.start_channel) - 1
        projected = [project(x, y) for x, y in points]
        if model.total_pixels <= 1:
            strands.append((model.name, projected, _hex_color(model), origin))
            continue
        count = min(model.total_pixels, max(1, len(projected)))
        for index in range(count):
            src = int(round(index * (len(projected) - 1) / max(1, count - 1))) if len(projected) != count else index
            nodes_xy.append(projected[min(src, len(projected) - 1)])
            nodes_ch.append(origin + index * per)
            nodes_rgb.append(rgb)
            nodes_color.append(_hex_color(model))
            nodes_model.append(model.name)
    return {
        "xy": nodes_xy,
        "ch": nodes_ch,
        "rgb": nodes_rgb,
        "color": nodes_color,
        "model": nodes_model,
        "strands": strands,
    }


def model_channel_report(layout_xml: Path, fseq: FseqData) -> list[dict]:
    """Per-model lit/varying stats from the real FSEQ. Used as a sanity check."""
    parsed = xmp.parse_layout(layout_xml)
    roots = sorted(
        (model for model in parsed.models.values() if not model.is_submodel and model.start_channel),
        key=lambda model: int(model.start_channel or 0),
    )
    reports = []
    spans = []
    for model in roots:
        count = model.total_pixels * (3 if model.is_rgb_capable() else 1)
        start = int(model.start_channel) - 1 - fseq.sparse_start
        end = start + count
        if start < 0 or end > fseq.channels:
            reports.append({"name": model.name, "status": "out_of_range",
                            "start": int(model.start_channel), "channels": count})
            continue
        stats = {"name": model.name, "display": model.display_as, "status": "blank",
                 "lit_frames": 0, "varying_frames": 0, "max": 0, "channels": count,
                 "rgb": model.is_rgb_capable()}
        reports.append(stats)
        spans.append((start, end, stats))

    # Amortize per-model reductions without retaining the full song in RAM.
    capacity = max(1, min(fseq.frames, (4 * 1024 * 1024) // fseq.channels))
    batch = np.empty((capacity, fseq.channels), dtype=np.uint8)
    for index, row in enumerate(fseq.rows()):
        slot = index % capacity
        batch[slot] = row
        if slot + 1 < capacity and index + 1 != fseq.frames:
            continue
        for start, end, stats in spans:
            block = batch[:slot + 1, start:end]
            bright = block.max(axis=1)
            stats["lit_frames"] += int(np.count_nonzero(bright))
            stats["varying_frames"] += int(np.count_nonzero(bright != block.min(axis=1)))
            stats["max"] = max(stats["max"], int(bright.max()))
            if stats["max"]:
                stats["status"] = "rendered"
    return reports
