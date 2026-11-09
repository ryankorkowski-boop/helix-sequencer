"""Real Starred Drive sampler through Helix Prime, six native xLights layouts and a distinct engine style."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw
from core.audio_run_cache import AudioRunCache
from core import effect_engine as engine
from models.showcase_flavors import FLAVORS, build_flavor
from tools.build_review_sampler import build as build_sampler
from tools.run_showcase_audio_batch import model_routes
from tools.showcase_audio_native import prepare_template, native_music_xsq
from tools.showcase_audio_preview import NativeSongView
from tools.fseq_pixel_preview import FseqReader
from tools.build_helpers.ultimate_showcase_preview import _font

SOURCES = (
    ("North Pole Overdrive", "1KyuJp3K9oP8k1YjCp7ot_4FJRg31sS2K", "d4a22b3b8982ea0e71aebc2ee0c7235cae2e77965b73764274cfbd89f64e54e5"),
    ("Ghost In The Grid", "1YtuMHP_qXuDvHDqYeDQ-uLRN3qVwdcTN", "201418cf9e011af8c1c8a8d517df7769d89383dee9b6a0c106c246c1d86ce2d2"),
    ("Glass Under Skin", "1PjQ4REDQw3XxrsGuMdnD6uq436qpU17h", "1918810704b9c103d9273745d761a49f365fe9d6a626aaf997c682871bdefd53"),
)
STYLES = {
    "musical": dict(audio_reactive_intensity=1.1, spatial_awareness=.40, chase_style="wave", max_layers_per_prop=2),
    "cinematic": dict(audio_reactive_intensity=1.6, spatial_awareness=.85, chase_style="radial_out", max_layers_per_prop=3),
    "kinetic": dict(audio_reactive_intensity=1.9, spatial_awareness=.95, chase_style="left_to_right", max_layers_per_prop=3),
}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def cmd(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def download_sources(root):
    import gdown
    folder = root / "sources"
    folder.mkdir(parents=True, exist_ok=True)
    config = []
    for title, file_id, expected in SOURCES:
        path = folder / (title + ".mp3")
        if not path.is_file() or digest(path) != expected:
            if path.exists():
                path.unlink()
            if not gdown.download(id=file_id, output=str(path), quiet=False):
                raise RuntimeError("Original Starred Drive source unavailable: " + title)
        if digest(path) != expected:
            raise ValueError("Starred source SHA256 failed: " + title)
        cmd(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"], stdout=subprocess.DEVNULL)
        config.append(dict(title=title, drive_id=file_id, local_path=str(path.resolve()), sha256=expected))
    config_path = root / "source_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return config_path

def prepare(root):
    source_config = download_sources(root)
    sampler_folder = root / "sampler"
    if sampler_folder.exists():
        shutil.rmtree(sampler_folder)
    provenance = build_sampler(source_config, sampler_folder, seconds=12)
    audio = sampler_folder / provenance["audio"]
    if provenance["duration_seconds"] != 36:
        raise ValueError("Expected exactly 36 seconds of verified Starred music")
    return audio, provenance

def tune(show, garden, style):
    settings = dict(
        layout_file=show / "xlights_rgbeffects.xml",
        template_guidance=False, workspace_history_enabled=False,
        learning_memory_enabled=False, matrix_intelligence=False,
        polish_enabled=False, variant_count=1, birdsong_enabled=False,
        birdsong_auto=False, audio_reactive_profile="showcase",
        model_overrides=model_routes(garden),
    )
    settings.update(STYLES[style])
    return engine.RuntimeTuning(**settings)

def native_run(root, audio, style, xlights):
    cache = AudioRunCache(digest(audio))
    proof = []
    for f in FLAVORS:
        garden = build_flavor(f.key)
        show = root / "shows" / garden.slug
        show.mkdir(parents=True, exist_ok=True)
        template = prepare_template(garden, show)
        media = show / audio.name
        shutil.copyfile(audio, media)
        if digest(media) != digest(audio):
            raise ValueError("Sampler was modified")
        raw = show / "sampler.prime_raw.xsq"
        native = show / (garden.slug + "_Starred.xsq")
        with (show / "helix_engine.log").open("w") as stream, redirect_stdout(stream):
            engine.run_variant(engine.VARIANTS["v27.3"], template, media, raw, engine.base.UserProfile(), tuning=tune(show, garden, style), analysis_cache=cache)
        native_info = native_music_xsq(raw, native, garden, media, 36)
        render_cmd = [str(xlights), "--headless", "-q", "-s", str(show.resolve()), "-od", str(show.resolve()), str(native.resolve())]
        if shutil.which("xvfb-run"):
            render_cmd = ["xvfb-run", "-a", *render_cmd]
        with (show / "native_xlights.log").open("w") as log:
            cmd(render_cmd, stdout=log, stderr=subprocess.STDOUT, timeout=1200, env={**os.environ, "XL_NO_GPU_COMPUTE": "1", "LIBGL_ALWAYS_SOFTWARE": "1"})
        fseq = native.with_suffix(".fseq")
        reader = FseqReader(fseq)
        if reader.info.step_ms != 50 or reader.info.frames != 720:
            raise ValueError("Native FSEQ duration/cadence mismatch: " + f.key)
        proof.append(dict(style=style, layout=f.title, key=f.key, xsq=str(native), fseq=str(fseq),
                          xsq_sha256=digest(native), fseq_sha256=digest(fseq),
                          layout_sha256=digest(show / "xlights_rgbeffects.xml"),
                          source_audio_sha256=digest(audio), native_effects=native_info["native_effects"],
                          frame_count=reader.info.frames, frame_ms=reader.info.step_ms))
        print("NATIVE_OK", style, f.title, native_info["native_effects"], flush=True)
    return proof, cache.hits

def compose(root, audio, proof, style):
    gardens = [build_flavor(p["key"]) for p in proof]
    readers = [FseqReader(Path(p["fseq"])) for p in proof]
    iterators = [r.iter_frames() for r in readers]
    views = [NativeSongView(g, audio.stem, 640, 360, halo_scale=2) for g in gardens]
    result = root / ("Helix_Starred_" + style + "_Six_Advanced_Layouts.mp4")
    command = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "1920x1080", "-r", "20", "-i", "-", "-i", str(audio),
               "-map", "0:v:0", "-map", "1:a:0", "-t", "36",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-threads", "2",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", str(result)]
    pipe = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for index in range(720):
            picture = Image.new("RGB", (1920, 1080), "#07101c")
            label = ImageDraw.Draw(picture)
            label.text((25, 30), "HELIX PRIME v27.3 | STARRED ORIGINAL AUDIO | " + style.upper(), fill="#eefaff", font=_font(26))
            for j, (r, frames, v, g) in enumerate(zip(readers, iterators, views, gardens, strict=True)):
                packed = np.frombuffer(next(frames), np.uint8)
                values = np.zeros(max(m.start - 1 + m.channels for m in g.models), np.uint8)
                if r.info.ranges:
                    offset = 0
                    for start, count in r.info.ranges:
                        values[start:start + count] = packed[offset:offset + count]
                        offset += count
                else:
                    values[:len(packed)] = packed
                x, y = (j % 3) * 640, 95 + (j // 3) * 430
                picture.paste(v.frame(values), (x, y))
                label.text((x + 18, y + 367), g.title, fill="#d4ebfd", font=_font(19))
            label.text((25, 1025), "Genuine native xLights FSEQ pixels projected to review camera; NOT native xLights MP4 export", fill="#aac3d8", font=_font(17))
            pipe.stdin.write(picture.tobytes())
            if index % 120 == 0:
                print("ENCODING", style, index, flush=True)
    except BaseException:
        pipe.terminate()
        raise
    finally:
        pipe.stdin.close()
    if pipe.wait() != 0:
        raise RuntimeError("MP4 video encoder failed")
    cmd(["ffmpeg", "-v", "error", "-xerror", "-i", str(result), "-f", "null", "-"], stdout=subprocess.DEVNULL)
    metadata = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(result)]))
    video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    sound = next(s for s in metadata["streams"] if s["codec_type"] == "audio")
    if (video["width"], video["height"]) != (1920, 1080) or sound["codec_name"] != "aac":
        raise ValueError("Final MP4 failed codec/dimension checks")
    return dict(mp4=result.name, mp4_sha256=digest(result), duration_seconds=float(metadata["format"]["duration"]),
                width=1920, height=1080, fps=20, decoded=True, original_audio_sha256=digest(audio),
                media_type="actual native xLights FSEQ projected review video", approval="UNAPPROVED")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", choices=STYLES, required=True)
    parser.add_argument("--xlights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    audio, provenance = prepare(root)
    proof, hits = native_run(root, audio, args.style, args.xlights.resolve())
    movie = compose(root, audio, proof, args.style)
    manifest = dict(schema="helix.starred_advanced_styles.v1", source_commit=os.environ.get("GITHUB_SHA"),
                    style=args.style, tuning=STYLES[args.style], source_folder="Starred",
                    source_audio_provenance=provenance, source_audio_sha256=digest(audio),
                    engine="actual Helix Prime v27.3", cache_hits=hits,
                    native_xsq_fseq=proof, video=movie, owner_approval="PENDING",
                    exclusion_note="Pixel sculpture layouts only; canonical six-snowman band and dual vocals not validated in these videos")
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(movie, indent=2), flush=True)

if __name__ == "__main__":
    main()
