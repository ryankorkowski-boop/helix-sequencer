from __future__ import annotations

import argparse
import math
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from core.lazy_imports import LazyModule

imageio = LazyModule("imageio.v2")
imageio_ffmpeg = LazyModule("imageio_ffmpeg")
np = LazyModule("numpy")
Image = LazyModule("PIL.Image")
ImageDraw = LazyModule("PIL.ImageDraw")
ImageFont = LazyModule("PIL.ImageFont")

V3 = "HX_SNOWMAN_DRUMMER_V3_"
LAYOUT = {
    "HIT_KICK": (640, 565),
    "HIT_SNARE": (520, 450),
    "HIT_HIHAT": (405, 390),
    "HIT_LEFT_TOM": (565, 350),
    "HIT_RIGHT_TOM": (720, 350),
    "HIT_LEFT_CRASH": (355, 245),
    "HIT_RIGHT_CRASH": (925, 245),
    "HIT_BOTH_CRASH": (640, 190),
    "DOWNBEAT_IMPACT": (640, 420),
}
LABELS = {
    "HIT_KICK": "KICK",
    "HIT_SNARE": "SNARE",
    "HIT_HIHAT": "HI-HAT",
    "HIT_LEFT_TOM": "LEFT TOM",
    "HIT_RIGHT_TOM": "RIGHT TOM",
    "HIT_LEFT_CRASH": "LEFT CRASH",
    "HIT_RIGHT_CRASH": "RIGHT CRASH",
    "HIT_BOTH_CRASH": "BOTH CRASH",
    "DOWNBEAT_IMPACT": "DOWNBEAT",
}


def _ms(v: str | None) -> float:
    try:
        return float(v or 0) / 1000.0
    except ValueError:
        return 0.0


def _intensity(settings: str | None) -> float:
    if not settings:
        return 0.75
    m = re.search(r"Start=([0-9]+)", settings)
    return max(0.05, min(1.0, float(m.group(1)) / 100.0)) if m else 0.75


def parse_effects(path: Path):
    root = ET.parse(path).getroot()
    out = []
    elements = root.find("ElementEffects")
    if elements is None:
        return out
    for element in elements.findall("Element"):
        if element.attrib.get("type") != "model":
            continue
        model = element.attrib.get("name", "")
        if not model.startswith(V3):
            continue
        for layer in element.findall("EffectLayer"):
            for node in layer.findall("Effect"):
                start, end = _ms(node.attrib.get("startTime")), _ms(node.attrib.get("endTime"))
                if end <= start:
                    continue
                out.append((model, node.attrib.get("name", "Effect"), start, end, _intensity(node.attrib.get("settings"))))
    return sorted(out, key=lambda x: (x[2], x[0]))


def key_for(model: str) -> str:
    return model.removeprefix(V3)


def amount(effect, t: float) -> float:
    _, _, start, end, intensity = effect
    if not (start <= t < end):
        return 0.0
    p = (t - start) / max(0.001, end - start)
    return max(0.0, min(1.0, math.sin(math.pi * p) * intensity))


def draw_hit(draw, key: str, x: int, y: int, a: float, frame: int):
    pulse = 0.8 + 0.2 * math.sin(frame * 0.3)
    a *= pulse
    r = int(22 + 48 * a)
    if "KICK" in key:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 80, 55), outline=(255,255,255), width=3)
        draw.ellipse((x-12, y-12, x+12, y+12), fill=(255,255,255))
    elif "SNARE" in key:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 225, 75), outline=(255,255,255), width=3)
        draw.line((x-r, y, x+r, y), fill=(255,255,255), width=3)
    elif "HIHAT" in key:
        draw.ellipse((x-r, y-r//2, x+r, y+r//2), fill=(75,220,255), outline=(255,255,255), width=3)
    elif "TOM" in key:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(175,115,255), outline=(255,255,255), width=3)
        draw.ellipse((x-r//2, y-r//2, x+r//2, y+r//2), outline=(255,255,255), width=2)
    elif "CRASH" in key:
        pts = []
        for i in range(16):
            ang = i * math.pi / 8
            rr = r if i % 2 == 0 else int(r * .55)
            pts.append((x + int(math.cos(ang)*rr), y + int(math.sin(ang)*rr*.65)))
        draw.polygon(pts, fill=(255,175,55), outline=(255,255,255))
    else:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255,90,180), outline=(255,255,255), width=3)


def mux(video: Path, audio: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        temp = Path(tmp.name)
    try:
        subprocess.run([ffmpeg, "-y", "-i", str(video), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(temp)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        video.write_bytes(temp.read_bytes())
    finally:
        temp.unlink(missing_ok=True)


def render(xsq: Path, audio: Path | None, width: int, height: int, fps: int) -> Path:
    effects = parse_effects(xsq)
    duration = max([e[3] for e in effects] + [1.0])
    out = xsq.with_name(xsq.stem + "_drummer_v3.mp4")
    writer = imageio.get_writer(out, fps=fps, codec="libx264", ffmpeg_log_level="error", pixelformat="yuv420p", macro_block_size=None, output_params=["-preset","veryfast","-crf","20","-movflags","+faststart"])
    font = ImageFont.load_default()
    try:
        for frame in range(max(1, int(math.ceil(duration * fps)))):
            t = frame / fps
            image = Image.new("RGB", (width, height), (6, 12, 22))
            draw = ImageDraw.Draw(image)
            for gx in range(0, width, 80): draw.line((gx, 0, gx, height), fill=(15,27,43))
            for gy in range(0, height, 80): draw.line((0, gy, width, gy), fill=(15,27,43))
            draw.rounded_rectangle((25,20,width-25,115), radius=16, fill=(10,18,31), outline=(120,170,220))
            draw.text((45,38), "HELIX — DRUMMER V3 ACTUAL SUBMODEL PREVIEW", font=font, fill=(245,248,255))
            draw.text((45,62), f"{t:05.2f}s / {duration:05.2f}s   |   {len(effects)} authored V3 effects", font=font, fill=(180,215,240))
            draw.text((45,86), "Positions correspond to the physical drum-kit roles, not generic model slots.", font=font, fill=(160,205,255))

            # Faint physical kit silhouette.
            draw.ellipse((585,500,695,610), outline=(45,65,88), width=3)  # kick
            draw.ellipse((475,405,565,475), outline=(45,65,88), width=3)  # snare
            draw.ellipse((520,305,610,375), outline=(45,65,88), width=3)
            draw.ellipse((675,305,765,375), outline=(45,65,88), width=3)
            for key,(x,y) in LAYOUT.items():
                active = [e for e in effects if key_for(e[0]) == key and amount(e,t) > 0]
                base_r = 25 if "CRASH" not in key else 30
                draw.ellipse((x-base_r,y-base_r,x+base_r,y+base_r), fill=(20,34,52), outline=(65,95,125), width=2)
                for e in active[:3]: draw_hit(draw,key,x,y,amount(e,t),frame)
                draw.text((x-45,y+42), LABELS[key], font=font, fill=(225,235,245))
                draw.text((x-92,y+59), V3+key, font=font, fill=(115,150,185))

            active = [e for e in effects if amount(e,t) > 0]
            active_names = ", ".join(LABELS.get(key_for(e[0]), key_for(e[0])) for e in active[:6]) or "REST"
            active_targets = ", ".join(e[0] for e in active[:3]) or "none"
            draw.rounded_rectangle((28,height-150,width-28,height-82), radius=15, fill=(10,18,31), outline=(120,170,220))
            draw.text((48,height-132), f"ACTIVE: {active_names}", font=font, fill=(245,248,255))
            draw.text((48,height-108), f"TARGETS: {active_targets}", font=font, fill=(180,220,255))
            writer.append_data(np.asarray(image,dtype=np.uint8))
    finally:
        writer.close()
    if audio is not None: mux(out,audio)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    p=argparse.ArgumentParser()
    p.add_argument("xsq", type=Path)
    p.add_argument("--audio", type=Path)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--fps", type=int, default=24)
    a=p.parse_args(argv)
    print(render(a.xsq,a.audio,a.width,a.height,a.fps))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
