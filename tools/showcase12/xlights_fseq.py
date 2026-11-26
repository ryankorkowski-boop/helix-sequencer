"""Render Helix sequences with xLights and read the FSEQ channel data.

This module does not simulate effects. Pixel colors come from an FSEQ file
written by xLights --headless (AppImage 2026.19 or another build on PATH).
"""

from __future__ import annotations

import os
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from core import model_parser as xmp


DEFAULT_XLIGHTS = Path("/tmp/xlights/squashfs-root/AppRun")


class FseqData:
    def __init__(self, channels: int, frames: int, step_ms: int, samples: np.ndarray, sparse_start: int) -> None:
        self.channels = channels
        self.frames = frames
        self.step_ms = step_ms
        self.samples = samples  # uint8 [frames, channels]
        self.sparse_start = sparse_start  # 0-based absolute channel index of column 0

    def fps(self) -> int:
        return max(1, int(round(1000.0 / max(1, self.step_ms))))


def load_fseq(path: Path) -> FseqData:
    import zstandard

    data = path.read_bytes()
    if data[:4] != b"PSEQ":
        raise RuntimeError(f"{path} is not an FSEQ file (magic {data[:4]!r})")
    data_offset = struct.unpack_from("<H", data, 4)[0]
    major = data[7]
    if major < 2:
        raise RuntimeError(f"{path} is FSEQ v{major}; this bench reads v2")
    channels = struct.unpack_from("<I", data, 10)[0]
    frames = struct.unpack_from("<I", data, 14)[0]
    step_ms = int(data[18]) or 50
    compression = data[20] & 0x0F
    block_count = ((data[20] >> 4) << 8) | data[21]
    sparse_count = data[22]
    pos = 32
    blocks: list[tuple[int, int]] = []
    for _ in range(block_count):
        first_frame, length = struct.unpack_from("<II", data, pos)
        blocks.append((first_frame, length))
        pos += 8
    sparse_start = 0
    for _ in range(sparse_count):
        raw = data[pos : pos + 6]
        start = raw[0] | (raw[1] << 8) | (raw[2] << 16)
        pos += 6
        sparse_start = start
        break
    if channels <= 0 or frames <= 0:
        raise RuntimeError(f"{path} has no channel data (channels={channels} frames={frames})")
    buffer = np.zeros((frames, channels), dtype=np.uint8)
    if compression == 0:
        raw = data[data_offset : data_offset + frames * channels]
        if len(raw) < frames * channels:
            raise RuntimeError(f"{path} uncompressed payload is short")
        buffer[:, :] = np.frombuffer(raw[: frames * channels], dtype=np.uint8).reshape(frames, channels)
    elif compression == 1:
        decoder = zstandard.ZstdDecompressor()
        cursor = data_offset
        for first_frame, length in blocks:
            if length <= 0:
                continue
            chunk = data[cursor : cursor + length]
            cursor += length
            raw = decoder.decompress(chunk, max_output_size=frames * channels)
            frame_span = len(raw) // channels
            buffer[first_frame : first_frame + frame_span, :] = np.frombuffer(raw, dtype=np.uint8).reshape(frame_span, channels)
    else:
        raise RuntimeError(f"{path} uses unsupported FSEQ compression type {compression}")
    return FseqData(channels, frames, step_ms, buffer, sparse_start)


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
    if fseq_path.exists() and fseq_path.stat().st_size > 64:
        return "cached"
    binary = xlights_binary()
    if show_dir.exists():
        shutil.rmtree(show_dir)
    show_dir.mkdir(parents=True)
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
    completed = subprocess.run(cmd, env=env, stdout=log_path.open("w"), stderr=subprocess.STDOUT, check=False)
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    produced = out_dir / f"{xsq_path.stem}.fseq"
    if completed.returncode != 0 or not produced.exists():
        tail = log_text[-1500:]
        raise RuntimeError(
            f"xLights --headless failed for {xsq_path.name} (exit {completed.returncode}).\n{tail}"
        )
    fseq_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(produced, fseq_path)
    version = "unknown"
    spdlog = home / ".local" / "state" / "xLights" / "xLights_spdlog.log"
    haystacks = [log_text]
    if spdlog.exists():
        haystacks.append(spdlog.read_text(encoding="utf-8", errors="replace"))
    for text in haystacks:
        for line in text.splitlines():
            if "Version:" in line and "WX Version" not in line:
                version = line.split("Version:")[-1].strip()
    return version


def _hex_color(model: xmp.Model) -> tuple[int, int, int]:
    raw = (model.raw_attrs.get("CustomColor") or "").strip()
    if raw.startswith("#") and len(raw) == 7:
        try:
            return tuple(int(raw[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]
        except ValueError:
            pass
    return (230, 230, 230)


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
        for point in model.geometry_points:
            xs.append(point[0])
            ys.append(point[1])
        prepared.append((model, points))
    house_path = Path(layout_xml).with_name("house.json")
    house_polys: list[tuple[str, list[tuple[float, float]]]] = []
    if house_path.exists():
        import json
        payload = json.loads(house_path.read_text(encoding="utf-8"))
        for poly in payload.get("polygons", []):
            pts = [(float(p[0]), float(p[1])) for p in poly.get("points", [])]
            if len(pts) >= 3:
                house_polys.append((str(poly.get("kind", "wall")), pts))
                xs.extend(p[0] for p in pts)
                ys.extend(p[1] for p in pts)
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
            geo = [(point[0], point[1]) for point in model.geometry_points] or points
            strands.append((model.name, [project(x, y) for x, y in geo], _hex_color(model), origin))
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
        "house": [(kind, [project(x, y) for x, y in pts]) for kind, pts in house_polys],
    }


def model_channel_report(layout_xml: Path, fseq: FseqData) -> list[dict]:
    """Per-model lit/varying stats from the real FSEQ. Used as a sanity check."""
    parsed = xmp.parse_layout(layout_xml)
    roots = sorted(
        (model for model in parsed.models.values() if not model.is_submodel and model.start_channel),
        key=lambda model: int(model.start_channel or 0),
    )
    reports = []
    for index, model in enumerate(roots):
        per = 3 if model.is_rgb_capable() else 1
        start = int(model.start_channel) - 1 - fseq.sparse_start
        count = model.total_pixels * per
        end = start + count
        if start < 0 or end > fseq.channels:
            reports.append(
                {
                    "name": model.name,
                    "status": "out_of_range",
                    "start": int(model.start_channel or 0),
                    "channels": count,
                }
            )
            continue
        block = fseq.samples[:, start:end]
        lit = int(np.count_nonzero(np.any(block > 0, axis=1)))
        # A frame varies when two nodes (or channels) disagree.
        if block.shape[1] > 1:
            varying = int(np.count_nonzero(block.max(axis=1) != block.min(axis=1)))
        else:
            varying = 0
        reports.append(
            {
                "name": model.name,
                "display": model.display_as,
                "status": "rendered" if lit else "blank",
                "lit_frames": lit,
                "varying_frames": varying,
                "max": int(block.max()) if block.size else 0,
                "channels": count,
                "rgb": model.is_rgb_capable(),
            }
        )
    return reports
