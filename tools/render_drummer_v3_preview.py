from __future__ import annotations

import argparse
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TARGETS = {
    "HX_SNOWMAN_DRUMMER_HIT_KICK": "KICK",
    "HX_SNOWMAN_DRUMMER_HIT_SNARE": "SNARE",
    "HX_SNOWMAN_DRUMMER_HIT_HI_HAT": "HI-HAT / PEDAL",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT": "TOM L",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT": "TOM R",
    "HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR": "FLOOR TOM",
    "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT": "CRASH L",
    "HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT": "CRASH R",
}

POSE_NAMES = {
    "kick_hit": "KICK",
    "snare_hit": "SNARE",
    "hi_hat_pulse": "HI-HAT / PEDAL",
    "left_tom_hit": "TOM L",
    "right_tom_hit": "TOM R",
    "floor_tom_hit": "FLOOR TOM",
    "left_crash": "CRASH L",
    "right_crash": "CRASH R",
    "downbeat_impact": "FULL KIT",
}


def parse_effects(xsq: Path) -> list[tuple[int, int, str, str]]:
    root = ET.parse(xsq).getroot()
    out: list[tuple[int, int, str, str]] = []
    for element in root.findall("./ElementEffects/Element"):
        name = element.get("name", "")
        if name not in TARGETS:
            continue
        for layer in element.findall("EffectLayer"):
            for fx in layer.findall("Effect"):
                pose = fx.get("sourcePose", "")
                out.append((
                    int(float(fx.get("startTime", "0"))),
                    int(float(fx.get("endTime", "0"))),
                    name,
                    pose,
                ))
    return sorted(out)


def draw_drummer(width: int, height: int, active: dict[str, float], t_ms: int, duration_ms: int, font) -> Image.Image:
    im = Image.new("RGB", (width, height), (7, 10, 18))
    d = ImageDraw.Draw(im)

    # Stage.
    d.rectangle((0, int(height * .72), width, height), fill=(12, 17, 28))
    for x in range(0, width, 48):
        d.line((x, int(height * .72), x + 170, height), fill=(30, 42, 60), width=1)

    cx, cy = width // 2, int(height * .38)

    def glow_box(box, intensity, label):
        intensity = max(0.0, min(1.0, intensity))
        if intensity > .02:
            glow = int(70 + 185 * intensity)
            for pad in (18, 10, 4):
                b = tuple(int(v) for v in (box[0]-pad, box[1]-pad, box[2]+pad, box[3]+pad))
                d.ellipse(b, outline=(255, 90, 90), width=max(2, pad // 4))
        d.ellipse(box, fill=(45 + int(150*intensity), 50 + int(90*intensity), 65 + int(80*intensity)), outline=(215, 225, 235), width=2)
        tw = d.textbbox((0,0), label, font=font)[2]
        d.text(((box[0]+box[2]-tw)/2, box[3]+5), label, font=font, fill=(235,240,248))

    # Snowman body.
    d.ellipse((cx-65, cy-55, cx+65, cy+75), fill=(225,230,238), outline=(150,160,175), width=3)
    d.ellipse((cx-46, cy-112, cx+46, cy-20), fill=(235,240,246), outline=(150,160,175), width=3)
    d.rectangle((cx-38, cy-128, cx+38, cy-112), fill=(30,35,45))
    d.rectangle((cx-25, cy-142, cx+25, cy-127), fill=(40,45,55))
    d.line((cx-42, cy-34, cx+42, cy-34), fill=(45,90,125), width=5)

    # Drum kit geometry: every illuminated object corresponds to a real XSQ target.
    kick = (cx-65, cy+65, cx+65, cy+125)
    snare = (cx-145, cy+35, cx-80, cy+78)
    tom_l = (cx-82, cy-5, cx-28, cy+36)
    tom_r = (cx-20, cy-8, cx+34, cy+34)
    floor_tom = (cx+82, cy+30, cx+150, cy+88)
    hi_hat = (cx-190, cy-10, cx-140, cy)
    crash_l = (cx-215, cy-95, cx-145, cy-75)
    crash_r = (cx+145, cy-95, cx+215, cy-75)

    kick_on = active.get("HX_SNOWMAN_DRUMMER_HIT_KICK", 0)
    snare_on = active.get("HX_SNOWMAN_DRUMMER_HIT_SNARE", 0)
    hihat_on = active.get("HX_SNOWMAN_DRUMMER_HIT_HI_HAT", 0)
    tom_l_on = active.get("HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT", 0)
    tom_r_on = active.get("HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT", 0)
    floor_on = active.get("HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR", 0)
    crash_l_on = active.get("HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT", 0)
    crash_r_on = active.get("HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT", 0)

    glow_box(kick, kick_on, "KICK")
    glow_box(snare, snare_on, "SNARE")
    glow_box(tom_l, tom_l_on, "TOM L")
    glow_box(tom_r, tom_r_on, "TOM R")
    glow_box(floor_tom, floor_on, "FLOOR")
    glow_box(hi_hat, hihat_on, "HI-HAT")
    glow_box(crash_l, crash_l_on, "CRASH L")
    glow_box(crash_r, crash_r_on, "CRASH R")

    # Hi-hat is foot/pedal-driven: no stick reaches the hi-hat.
    pedal_y = cy + 112
    d.line((cx-164, cy+2, cx-164, pedal_y), fill=(130,145,165), width=3)
    d.line((cx-178, pedal_y, cx-145, pedal_y), fill=(255, 245 if hihat_on else 180, 120 if hihat_on else 150), width=5)
    if hihat_on > .02:
        d.ellipse((cx-181, pedal_y-5, cx-142, pedal_y+5), outline=(255,230,130), width=3)

    # Kick has no stick. Snare/toms/cymbals carry the active arm/stick.
    left_hit = max(snare_on, tom_l_on, crash_l_on)
    right_hit = max(tom_r_on, floor_on, crash_r_on)
    left_target = (cx-125, cy-35-int(25*left_hit)) if crash_l_on >= max(snare_on, tom_l_on) else ((cx-55, cy+13) if tom_l_on >= snare_on else (cx-112, cy+52))
    right_target = (cx+125, cy-35-int(25*right_hit)) if crash_r_on >= max(tom_r_on, floor_on) else ((cx+116, cy+57) if floor_on >= tom_r_on else (cx+8, cy+10))
    d.line((cx-30, cy+5, left_target[0], left_target[1]), fill=(255,230,170), width=5)
    d.line((cx+30, cy+5, right_target[0], right_target[1]), fill=(255,230,170), width=5)

    active_names = [TARGETS[k] for k,v in active.items() if v > .02 and k in TARGETS]
    pose_names = []
    for name, pose in sorted(((k,p) for s,e,k,p in []), key=lambda x:x[0]):
        pose_names.append(POSE_NAMES.get(pose, pose))

    d.rounded_rectangle((24, 20, width-24, 108), radius=14, fill=(8,12,20), outline=(95,115,145), width=2)
    d.text((42, 36), "HELIX — REAL DRUMMER TARGETS", font=font, fill=(245,248,255))
    d.text((42, 62), "ACTIVE: " + (", ".join(active_names) if active_names else "idle"), font=font, fill=(255,190,160))
    d.text((42, 84), f"{t_ms/1000:.2f}s / {duration_ms/1000:.2f}s", font=font, fill=(185,205,230))

    # Target legend.
    d.text((24, height-42), "XSQ target → composite: kick(no stick) • hi-hat(pedal) • 3 toms • snare/cymbals+arms/sticks", font=font, fill=(165,190,220))
    return im



def _audio_duration_ms(audio: Path) -> int:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.run(
        [ff, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio)],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        try:
            data = json.loads(proc.stdout)
            duration = float(data["format"]["duration"])
            if duration > 0:
                return int(round(duration * 1000.0))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    probe = subprocess.run([ff, "-i", str(audio)], capture_output=True, text=True)
    marker = "Duration: "
    for line in probe.stderr.splitlines():
        if marker in line:
            value = line.split(marker, 1)[1].split(",", 1)[0].strip()
            h, m, s = value.split(":")
            return int(round((int(h) * 3600 + int(m) * 60 + float(s)) * 1000.0))
    raise RuntimeError(f"Unable to determine audio duration for {audio}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq", type=Path)
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--duration", type=float, default=0.0, help="Optional debug cap in seconds; default renders the entire audio.")
    args = ap.parse_args()

    effects = parse_effects(args.xsq)
    if not effects:
        raise SystemExit("FAIL: no real HX_SNOWMAN_DRUMMER submodel effects found")

    audio_duration_ms = _audio_duration_ms(args.audio)
    effect_end_ms = max(e[1] for e in effects)
    if effect_end_ms < int(audio_duration_ms * 0.95):
        raise SystemExit(
            f"FAIL: drummer XSQ ends at {effect_end_ms} ms, but repo audio is {audio_duration_ms} ms; "
            "refusing to render a partial performance"
        )
    duration_ms = audio_duration_ms if args.duration <= 0 else min(int(args.duration * 1000), audio_duration_ms)
    if args.duration <= 0:
        print(f"FULL-SONG MODE: audio_duration_ms={audio_duration_ms} effect_end_ms={effect_end_ms}")
    out = args.output
    silent = out.with_suffix(".silent.mp4")
    font = ImageFont.load_default()
    writer = imageio.get_writer(silent, fps=args.fps, codec="libx264", quality=8, macro_block_size=None)

    try:
        for i in range(int(duration_ms / 1000 * args.fps)):
            t = int(i * 1000 / args.fps)
            active = {name: 0.0 for name in TARGETS}
            for start, end, name, _pose in effects:
                if start <= t < end:
                    active[name] = max(active[name], 1.0)
            frame = draw_drummer(960, 540, active, t, duration_ms, font)
            writer.append_data(np.asarray(frame))
    finally:
        writer.close()

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-i", str(silent), "-i", str(args.audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-4000:])
    silent.unlink(missing_ok=True)

    if not out.exists() or out.stat().st_size < 10000:
        raise SystemExit("FAIL: drummer MP4 missing/empty")
    print(f"PASS: real drummer MP4 targets={len(TARGETS)} effects={len(effects)} duration_ms={duration_ms} audio_duration_ms={audio_duration_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
