"""Render *actual xLights FSEQ channel values* as a per-node MP4 preview.

The FSEQ must come from native xLights rendering; this is not an XSQ effects
simulator. Pixel colors are faithful to FSEQ data, while auto-generated model
geometry from an xLights XML can be approximate (use --pixel-map for exact
node coordinates). Supports FSEQ v1/v2 dense or sparse, zlib and optional zstd.
"""
from __future__ import annotations

import argparse
import bisect
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import struct
import subprocess
import zlib


@dataclass(frozen=True)
class FseqInfo:
    version: int
    data_offset: int
    channels: int
    frames: int
    step_ms: int
    compression: int
    blocks: tuple[tuple[int, int], ...]
    ranges: tuple[tuple[int, int], ...]


class FseqReader:
    def __init__(self, path: Path):
        self.path = Path(path)
        with self.path.open("rb") as handle:
            raw = handle.read(32)
            if len(raw) < 28 or raw[:4] not in {b"PSEQ", b"FSEQ"}:
                raise ValueError("Not an FSEQ file (PSEQ/FSEQ magic missing)")
            version = raw[7]
            if version == 2 and len(raw) < 32:
                raise ValueError("Truncated FSEQ V2 header")
            if version not in (1, 2):
                raise ValueError(f"Unsupported FSEQ major version {version}")
            data_offset = struct.unpack_from("<H", raw, 4)[0]
            channels, frames = struct.unpack_from("<II", raw, 10)
            step_ms = raw[18]
            if min(data_offset, channels, frames, step_ms) <= 0:
                raise ValueError("Invalid FSEQ header values")
            if channels > 200_000_000 or frames > 5_000_000:
                raise ValueError("FSEQ declares unreasonable sequence dimensions")
            compression = (raw[20] & 0x0F) if version == 2 else 0
            if compression not in (0, 1, 2):
                raise ValueError(f"Unknown FSEQ compression {compression}")
            block_count = ((raw[20] & 0xF0) << 4) | raw[21] if version == 2 else 0
            range_count = raw[22] if version == 2 else 0
            blocks, ranges = [], []
            if version == 2:
                for _ in range(block_count):
                    entry = handle.read(8)
                    if len(entry) != 8:
                        raise ValueError("Truncated FSEQ compression index")
                    first, size = struct.unpack("<II", entry)
                    if size:
                        blocks.append((first, size))
                for _ in range(range_count):
                    entry = handle.read(6)
                    if len(entry) != 6:
                        raise ValueError("Truncated FSEQ sparse channel index")
                    start = int.from_bytes(entry[:3], "little")
                    count = int.from_bytes(entry[3:], "little")
                    if count <= 0:
                        raise ValueError("Invalid zero-length FSEQ sparse range")
                    ranges.append((start, count))
                if ranges and sum(n for _a, n in ranges) != channels:
                    raise ValueError("Sparse FSEQ channel count does not match header")
            for (previous, count), (following, _next_count) in zip(ranges, ranges[1:]):
                if following < previous + count:
                    raise ValueError("FSEQ sparse ranges must be ordered and nonoverlapping")
            if data_offset < (28 if version == 1 else 32) + block_count * 8 + range_count * 6:
                raise ValueError("Invalid FSEQ channel-data offset")
            if self.path.stat().st_size < data_offset:
                raise ValueError("FSEQ header declares data after end of file")
            self.info = FseqInfo(version, data_offset, channels, frames, step_ms,
                                 compression, tuple(blocks), tuple(ranges))
        self._range_starts = [a for a, _n in self.info.ranges]
        self._range_offsets = []
        offset = 0
        for _start, count in self.info.ranges:
            self._range_offsets.append(offset)
            offset += count

    def offset_for_channel(self, one_based_channel: int) -> int | None:
        idx = one_based_channel - 1
        if idx < 0:
            return None
        if not self.info.ranges:
            return idx if idx < self.info.channels else None
        slot = bisect.bisect_right(self._range_starts, idx) - 1
        if slot < 0:
            return None
        start, count = self.info.ranges[slot]
        if idx >= start + count:
            return None
        return self._range_offsets[slot] + idx - start

    def iter_frames(self):
        info = self.info
        total = 0
        with self.path.open("rb") as handle:
            handle.seek(info.data_offset)
            if info.compression == 0:
                for _ in range(info.frames):
                    frame = handle.read(info.channels)
                    if len(frame) != info.channels:
                        raise ValueError("Truncated FSEQ frame data")
                    yield frame
                return

            if not info.blocks:
                raise ValueError("Compressed FSEQ has no valid block index")
            for block_number, (first_frame, size) in enumerate(info.blocks):
                if first_frame != total:
                    raise ValueError(
                        f"Noncontiguous FSEQ compressed block frames: {first_frame} != {total}"
                    )
                compressed = handle.read(size)
                if len(compressed) != size:
                    raise ValueError("Truncated FSEQ compressed block")
                if info.compression == 2:
                    try:
                        data = zlib.decompress(compressed)
                    except zlib.error:
                        # Certain historical xLights/FPP encoders kept a
                        # raw first block despite selecting zlib compression.
                        next_first = (
                            info.blocks[block_number + 1][0]
                            if block_number + 1 < len(info.blocks)
                            else info.frames
                        )
                        expected_bytes = (next_first - first_frame) * info.channels
                        if block_number != 0 or len(compressed) != expected_bytes:
                            raise ValueError("Invalid FSEQ zlib data; raw fallback not safe")
                        data = compressed
                else:
                    try:
                        import zstandard
                    except ImportError as exc:
                        raise RuntimeError(
                            "FSEQ Zstandard blocks require pip install zstandard"
                        ) from exc
                    # xLights FSEQ may omit original frame-content size.
                    reader = zstandard.ZstdDecompressor().stream_reader(
                        __import__("io").BytesIO(compressed)
                    )
                    with reader:
                        data = reader.read()
                if len(data) % info.channels:
                    raise ValueError("FSEQ block length is not divisible by channel count")
                for pos in range(0, len(data), info.channels):
                    if total >= info.frames:
                        raise ValueError("FSEQ compressed data contains extra frames")
                    yield data[pos:pos + info.channels]
                    total += 1
            if total != info.frames:
                raise ValueError(f"FSEQ declared {info.frames} frames but decoded {total}")


@dataclass(frozen=True)
class Pixel:
    one_based_channel: int
    x: float
    y: float
    kind: str = "rgb"


def pixels_from_csv(path: Path) -> list[Pixel]:
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    result = []
    for row in rows:
        kind = (row.get("kind") or "rgb").strip().lower()
        if kind not in {"rgb", "grb", "brg", "bgr", "rbg", "gbr", "red", "green", "white"}:
            raise ValueError(f"Unsupported pixel kind {kind}")
        result.append(Pixel(
            int(row["channel"]), float(row["x"]), float(row["y"]), kind
        ))
    if not result or any(p.one_based_channel < 1 for p in result):
        raise ValueError("Pixel CSV requires positive 1-based channel,x,y,kind values")
    return result


def pixels_from_layout(path: Path) -> list[Pixel]:
    from core.model_parser import parse_layout
    layout = parse_layout(Path(path))
    pixels = []
    for model in layout.models.values():
        if model.is_submodel or model.start_channel is None:
            continue
        text = model.string_type.lower()
        if "single color red" in text:
            kind = "red"
        elif "single color green" in text:
            kind = "green"
        elif "single color white" in text or "single color intensity" in text:
            kind = "white"
        elif model.is_rgb_capable():
            kind = "rgb"
        else:
            continue
        for point in model.virtual_pixel_map():
            base = model.start_channel + point.index * (3 if kind == "rgb" else 1)
            pixels.append(Pixel(base, point.x, point.y, kind))
    if not pixels:
        raise ValueError("No addressable nodes found in xLights layout")
    return pixels


def render_fseq_preview(fseq_path: Path, output: Path, *, pixel_map: Path | None = None,
                        layout: Path | None = None, audio: Path | None = None,
                        width: int = 1280, height: int = 720, max_seconds: float = 0.0):
    if not pixel_map and not layout:
        raise ValueError("Provide --pixel-map (exact coordinates) or --layout (approximate geometry)")
    if pixel_map and layout:
        raise ValueError("Choose one geometry source; do not mix mappings")
    if width < 64 or height < 64:
        raise ValueError("Video dimensions must be at least 64x64")
    try:
        import imageio.v2 as imageio
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Install imageio, imageio-ffmpeg and Pillow to render previews") from exc
    reader = FseqReader(fseq_path)
    nodes = pixels_from_csv(pixel_map) if pixel_map else pixels_from_layout(layout)
    addresses = []
    for node in nodes:
        offsets = tuple(reader.offset_for_channel(node.one_based_channel + index)
                        for index in range(3 if len(node.kind) == 3 and
                                            set(node.kind) == {"r", "g", "b"} else 1))
        if any(item is None for item in offsets):
            continue
        addresses.append((node, offsets))
    if not addresses:
        raise ValueError("No layout nodes have channel addresses in this FSEQ")
    min_x = min(node.x for node, _offsets in addresses)
    max_x = max(node.x for node, _offsets in addresses)
    min_y = min(node.y for node, _offsets in addresses)
    max_y = max(node.y for node, _offsets in addresses)
    sx = (width - 64) / max(1, max_x - min_x)
    sy = (height - 64) / max(1, max_y - min_y)
    scale = min(sx, sy)
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    mapped = [(int(width / 2 + (node.x - center_x) * scale),
               int(height / 2 - (node.y - center_y) * scale),
               node.kind, offsets) for node, offsets in addresses]
    fps = 1000.0 / reader.info.step_ms
    stop_at = reader.info.frames if max_seconds <= 0 else min(
        reader.info.frames, math.ceil(max_seconds * fps)
    )
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output path must end with .mp4")
    output.parent.mkdir(parents=True, exist_ok=True)
    silent = output.with_name(output.stem + ".silent.mp4")
    frames_written, bright_nodes = 0, 0
    writer = imageio.get_writer(
        str(silent), fps=fps, codec="libx264", pixelformat="yuv420p",
        ffmpeg_log_level="error", macro_block_size=1
    )
    try:
        for frame in reader.iter_frames():
            if frames_written >= stop_at:
                break
            image = Image.new("RGB", (width, height), (3, 8, 17))
            draw = ImageDraw.Draw(image)
            for x, y, kind, offsets in mapped:
                if len(kind) == 3 and set(kind) == {"r", "g", "b"}:
                    # kind labels the physical order of consecutive FSEQ bytes.
                    by_component = {letter: frame[offsets[i]] for i, letter in enumerate(kind)}
                    color = tuple(by_component[channel] for channel in "rgb")
                else:
                    intensity = frame[offsets[0]]
                    color = {
                        "red": (intensity, 0, 0),
                        "green": (0, intensity, 0),
                        "white": (intensity, intensity, intensity),
                    }[kind]
                if max(color) == 0:
                    continue
                bright_nodes += 1
                draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)
            writer.append_data(image)
            frames_written += 1
    finally:
        writer.close()
    if frames_written == 0:
        silent.unlink(missing_ok=True)
        raise ValueError("No video frames rendered from FSEQ")
    if audio:
        import imageio_ffmpeg
        if not Path(audio).is_file():
            raise FileNotFoundError(audio)
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(silent),
            "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-shortest", str(output)
        ]
        subprocess.run(command, check=True, capture_output=True)
        silent.unlink(missing_ok=True)
    else:
        silent.replace(output)
    report = {
        "fseq": str(fseq_path), "video": str(output), "frames": frames_written,
        "frame_step_ms": reader.info.step_ms, "channel_count": reader.info.channels,
        "mapped_nodes": len(mapped), "bright_node_samples": bright_nodes,
        "geometry": "explicit" if pixel_map else "approximate from xLights model outlines",
        "source": "FSEQ channel data (not XSQ effect simulation)",
        "native_xlights_origin_verified_by_this_tool": False,
        "geometry_coordinates_explicit": bool(pixel_map),
        "physical_coordinate_accuracy_verified": False,
    }
    output.with_suffix(".pixel_preview.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fseq", type=Path)
    p.add_argument("--output", type=Path, required=True)
    geometry = p.add_mutually_exclusive_group(required=True)
    geometry.add_argument("--layout", type=Path)
    geometry.add_argument("--pixel-map", type=Path)
    p.add_argument("--audio", type=Path)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--max-seconds", type=float, default=0)
    a = p.parse_args()
    print(json.dumps(render_fseq_preview(
        a.fseq, a.output, pixel_map=a.pixel_map, layout=a.layout, audio=a.audio,
        width=a.width, height=a.height, max_seconds=a.max_seconds
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
