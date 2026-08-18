from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from core.lazy_imports import LazyModule
from tools.preview_renderer import parse_models, parse_sequence, build_leaf_intensity_matrix, choose_track, active_label, format_time

imageio = LazyModule("imageio.v2")
imageio_ffmpeg = LazyModule("imageio_ffmpeg")
np = LazyModule("numpy")
Image = LazyModule("PIL.Image")
ImageDraw = LazyModule("PIL.ImageDraw")
ImageFilter = LazyModule("PIL.ImageFilter")
ImageFont = LazyModule("PIL.ImageFont")

BAND = {
    "HX_SNOWMAN_DRUMMER": (170, 330, "drums"),
    "HX_SNOWMAN_BASSIST": (310, 305, "bass"),
    "HX_SNOWMAN_GUITARIST": (455, 310, "guitar"),
    "HX_SNOWMAN_SINGER": (590, 300, "lead"),
    "HX_SNOWMAN_SINGER_FEMALE": (730, 305, "vocal"),
    "HX_FLOOR_PIANO": (450, 455, "piano"),
}
COLORS = {
    "HX_SNOWMAN_DRUMMER": (255, 95, 95),
    "HX_SNOWMAN_BASSIST": (100, 220, 255),
    "HX_SNOWMAN_GUITARIST": (255, 190, 75),
    "HX_SNOWMAN_SINGER": (255, 245, 220),
    "HX_SNOWMAN_SINGER_FEMALE": (255, 125, 210),
    "HX_FLOOR_PIANO": (150, 190, 255),
}


class BandRenderer:
    def __init__(self, width=960, height=540):
        self.width = width
        self.height = height
        self.font = ImageFont.load_default()
        self._base = self._make_base()

    def _make_base(self):
        im = Image.new("RGBA", (self.width, self.height), (5, 9, 18, 255))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 350, self.width, 540), fill=(9, 14, 25, 255))
        for y in range(350, 540, 24):
            d.line((0, y, self.width, y), fill=(40, 55, 78, 80), width=1)
        for x in range(0, self.width, 48):
            d.line((x, 350, x + 180, 540), fill=(35, 48, 68, 45), width=1)
        d.line((80, 350, 880, 350), fill=(120, 150, 190, 90), width=2)
        d.line((80, 72, 880, 72), fill=(70, 90, 120, 170), width=5)
        for x in range(100, 881, 80):
            d.line((x, 72, x, 105), fill=(70, 90, 120, 150), width=3)
        return im

    def snowman(self, d, cx, cy, scale, bright, role, phase):
        glow = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        def C(f=1.0):
            return tuple(min(255, int(v * (0.35 + 0.65 * bright) * f)) for v in (235, 240, 248)) + (255,)
        r = max(10, int(24 * scale))
        body = max(14, int(32 * scale))
        head = max(10, int(22 * scale))
        sway = math.sin(phase) * 4 * scale * bright
        cx += sway
        if bright > 0.05:
            gd.ellipse((cx - r * 2.0, cy - head * 2.3, cx + r * 2.0, cy + body * 1.8), fill=COLORS.get(role, (160, 190, 255)) + (45,))
        d.ellipse((cx - body, cy - body, cx + body, cy + body), fill=C(0.9))
        d.ellipse((cx - head, cy - head * 2.0, cx + head, cy), fill=C(1.0))
        d.rectangle((cx - head * 0.8, cy - head * 2.55, cx + head * 0.8, cy - head * 2.15), fill=(30, 35, 45, 255))
        d.rectangle((cx - head * 0.45, cy - head * 2.95, cx + head * 0.45, cy - head * 2.5), fill=(45, 50, 65, 255))
        d.line((cx - head, cy - head * 0.15, cx + head, cy - head * 0.15), fill=(40, 90, 130, 255), width=max(2, int(4 * scale)))
        for yy in (0.35, 0.7):
            d.ellipse((cx - 3 * scale, cy + body * yy, cx + 3 * scale, cy + body * yy + 6 * scale), fill=(30, 35, 45, 255))
        arm_y = cy - body * 0.35
        hand_y = cy - body * 0.9
        d.line((cx - body * 0.75, arm_y, cx - body * 1.45, hand_y), fill=C(0.85), width=max(2, int(4 * scale)))
        d.line((cx + body * 0.75, arm_y, cx + body * 1.45, hand_y), fill=C(0.85), width=max(2, int(4 * scale)))
        if role == "HX_SNOWMAN_DRUMMER": self.drums(d, cx, cy, scale, bright, phase)
        elif role == "HX_SNOWMAN_BASSIST": self.instrument(d, cx + 10 * scale, cy - 5 * scale, scale, bright, True)
        elif role == "HX_SNOWMAN_GUITARIST": self.instrument(d, cx + 10 * scale, cy - 8 * scale, scale, bright, False)
        elif role in ("HX_SNOWMAN_SINGER", "HX_SNOWMAN_SINGER_FEMALE"): self.mic(d, cx, cy, scale, bright)
        self._frame_glow = glow.filter(ImageFilter.GaussianBlur(radius=10))

    def drums(self, d, cx, cy, s, b, p):
        base = cy + 30 * s
        w = 55 * s
        h = 28 * s
        col = COLORS["HX_SNOWMAN_DRUMMER"]
        d.ellipse((cx - w, base - h, cx + w, base + h), fill=(45, 50, 62, 255), outline=col + (255,), width=max(2, int(3 * s)))
        d.ellipse((cx - w * .38, base - h * .5, cx + w * .38, base + h * .5), fill=(20, 25, 35, 255), outline=(220, 225, 235, 255), width=max(1, int(2 * s)))
        d.ellipse((cx - 65 * s, base - 20 * s, cx - 35 * s, base + 4 * s), fill=(35, 40, 52, 255), outline=(210, 215, 225, 255), width=max(2, int(3 * s)))
        d.ellipse((cx + 35 * s, base - 20 * s, cx + 65 * s, base + 4 * s), fill=(35, 40, 52, 255), outline=(210, 215, 225, 255), width=max(2, int(3 * s)))
        hit = math.sin(p * 3) > 0.2 and b > .3
        arm = 32 * s * (1.35 if hit else 1.0)
        d.line((cx - 18 * s, cy - 18 * s, cx - 42 * s, cy - 18 * s - arm * .35), fill=(255, 230, 170, 255), width=max(2, int(4 * s)))
        d.line((cx + 18 * s, cy - 18 * s, cx + 42 * s, cy - 18 * s - arm * .35), fill=(255, 230, 170, 255), width=max(2, int(4 * s)))
        d.ellipse((cx - 85 * s, base - 48 * s, cx - 58 * s, base - 42 * s), fill=(190, 200, 215, 255))
        d.ellipse((cx + 58 * s, base - 52 * s, cx + 85 * s, base - 46 * s), fill=(190, 200, 215, 255))

    def instrument(self, d, cx, cy, s, b, bass):
        col = COLORS["HX_SNOWMAN_BASSIST" if bass else "HX_SNOWMAN_GUITARIST"]
        d.line((cx - 5 * s, cy + 12 * s, cx + 38 * s, cy - 55 * s), fill=col + (255,), width=max(3, int(7 * s)))
        d.ellipse((cx - 30 * s, cy - 5 * s, cx + 10 * s, cy + 35 * s), fill=(40, 45, 55, 255), outline=col + (255,), width=max(2, int(3 * s)))
        count = 4 if bass else 6
        for i in range(count):
            xx = cx + 31 * s + i * 2 * s
            d.line((xx, cy - 54 * s, xx, cy + 14 * s), fill=(220, 225, 235, 255), width=max(1, int(1.5 * s)))
        d.ellipse((cx - 3 * s, cy + 2 * s, cx + 7 * s, cy + 12 * s), fill=col + (255,))

    def mic(self, d, cx, cy, s, b):
        col = (255, 125, 210) if cx > 650 else (245, 245, 250)
        d.line((cx + 18 * s, cy - 8 * s, cx + 18 * s, cy + 55 * s), fill=(180, 185, 195, 255), width=max(2, int(3 * s)))
        d.line((cx + 18 * s, cy + 55 * s, cx - 18 * s, cy + 55 * s), fill=(180, 185, 195, 255), width=max(2, int(3 * s)))
        d.ellipse((cx + 5 * s, cy - 25 * s, cx + 27 * s, cy - 4 * s), fill=col + (255,), outline=(255, 255, 255, 255), width=1)
        if b > .45:
            d.ellipse((cx + 10 * s, cy - 20 * s, cx + 22 * s, cy - 8 * s), fill=(255, 255, 255, 180))

    def piano(self, d, x, y, s, b):
        d.rounded_rectangle((x - 100 * s, y - 20 * s, x + 100 * s, y + 30 * s), radius=8, fill=(25, 30, 42, 255), outline=COLORS["HX_FLOOR_PIANO"] + (255,), width=max(2, int(3 * s)))
        for i in range(17):
            xx = x - 90 * s + i * 11 * s
            d.line((xx, y - 17 * s, xx, y + 25 * s), fill=(205, 210, 220, 220), width=1)
        for i in range(11):
            xx = x - 84 * s + i * 16 * s
            d.rectangle((xx, y - 17 * s, xx + 8 * s, y + 2 * s), fill=(15, 18, 25, 255))
        if b > .1:
            for hand_x in (x - 55 * s, x + 45 * s):
                d.ellipse((hand_x - 7 * s, y - 45 * s, hand_x + 7 * s, y - 31 * s), fill=(245, 245, 250, 255))
                d.line((hand_x, y - 31 * s, hand_x + 10 * math.sin(b * 8) * s, y - 12 * s), fill=(245, 245, 250, 255), width=max(2, int(3 * s)))

    def render(self, active, t_ms, duration, overlays, title):
        base = self._base.copy()
        self.piano(ImageDraw.Draw(base), 450, 455, 1.0, float(active.get("HX_FLOOR_PIANO", 0)))
        for name, (x, y, role) in BAND.items():
            if role == "piano":
                continue
            self.snowman(ImageDraw.Draw(base), x, y, 1.0, float(active.get(name, 0.0)), name, t_ms / 250.0)
            base.alpha_composite(self._frame_glow)
        d = ImageDraw.Draw(base)
        d.rounded_rectangle((25, 18, 400, 105), radius=15, fill=(7, 11, 19, 225), outline=(180, 205, 235, 80))
        d.text((42, 35), title[:48], font=self.font, fill=(245, 248, 255, 255))
        d.text((42, 58), f"time {format_time(t_ms)} / {format_time(duration)}", font=self.font, fill=(190, 210, 235, 255))
        d.text((42, 80), f"active performers {sum(v > .02 for v in active.values())}", font=self.font, fill=(165, 210, 250, 255))
        d.rounded_rectangle((610, 18, 935, 125), radius=15, fill=(7, 11, 19, 225), outline=(180, 205, 235, 80))
        yy = 35
        for k in ("song part", "piano", "sweep", "drop"):
            if overlays.get(k):
                d.text((628, yy), f"{k}: {overlays[k][:34]}", font=self.font, fill=(245, 248, 255, 255))
                yy += 22
        d.text((35, 490), "HELIXVILLE 4 • SIX-PIECE SNOWMAN BAND", font=self.font, fill=(170, 205, 235, 255))
        left, top, right, bottom = 34, 507, 926, 524
        d.rectangle((left, top, right, bottom), fill=(30, 40, 55, 255))
        prog = 0 if duration <= 0 else max(0, min(1, t_ms / duration))
        d.rectangle((left, top, left + int((right - left) * prog), bottom), fill=(70, 175, 255, 255))
        return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--audio", required=False)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--height", type=int, default=540)
    args = ap.parse_args()
    layout = parse_models(Path(args.layout))
    seq = parse_sequence(Path(args.xsq))
    names, intensity = build_leaf_intensity_matrix(layout, seq, args.fps)
    idx = {n: i for i, n in enumerate(names)}
    tracks = {k: choose_track(seq, v) for k, v in (("song part", "song parts"), ("piano", "piano"), ("sweep", "sweeps"), ("drop", "drops"))}
    out = Path(args.xsq).with_name(Path(args.xsq).stem + ".mp4")
    tmp = out.with_suffix(".silent.mp4")
    renderer = BandRenderer(args.width, args.height)
    writer = imageio.get_writer(tmp, fps=args.fps, codec="libx264", quality=7, ffmpeg_log_level="error", pixelformat="yuv420p", macro_block_size=None)
    try:
        for fi in range(intensity.shape[1]):
            t = int(round(fi * 1000 / args.fps))
            active = {name: float(intensity[idx[name], fi]) for name in BAND if name in idx}
            overlays = {k: active_label(v, t) for k, v in tracks.items()}
            frame = renderer.render(active, t, seq.duration_ms, overlays, Path(args.xsq).name)
            writer.append_data(np.asarray(frame.convert("RGB"), dtype=np.uint8))
    finally:
        writer.close()
    if out.exists():
        out.unlink()
    if args.audio and Path(args.audio).exists():
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ff, "-y", "-i", str(tmp), "-i", str(args.audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tmp.unlink(missing_ok=True)
    else:
        tmp.replace(out)
    print(out)


if __name__ == "__main__":
    main()
