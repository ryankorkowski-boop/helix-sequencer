from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from core.lazy_imports import optional_import


def _infer_audio_stem(xsq_path: Path) -> str:
    return xsq_path.stem.replace(",", "_")


def _trim_effects(root: ET.Element, start_ms: int, end_ms: int) -> int:
    kept = 0
    effects_root = root.find("./ElementEffects")
    if effects_root is None:
        return kept
    for element in list(effects_root.findall("Element")):
        layer_has_effects = False
        for layer in list(element.findall("EffectLayer")):
            kept_effects: list[ET.Element] = []
            for effect in list(layer.findall("Effect")):
                old_start = int(float(effect.attrib.get("startTime", "0") or 0))
                old_end = int(float(effect.attrib.get("endTime", "0") or 0))
                if old_end <= start_ms or old_start >= end_ms:
                    layer.remove(effect)
                    continue
                new_start = max(0, old_start - start_ms)
                new_end = min(end_ms - start_ms, old_end - start_ms)
                if new_end <= new_start:
                    new_end = min(end_ms - start_ms, new_start + 1)
                effect.attrib["startTime"] = str(int(new_start))
                effect.attrib["endTime"] = str(int(new_end))
                kept_effects.append(effect)
                kept += 1
            if not kept_effects:
                element.remove(layer)
                continue
            layer_has_effects = True
        if not layer_has_effects:
            effects_root.remove(element)
    return kept


def _update_head(root: ET.Element, *, title_suffix: str, duration_ms: int, media_name: str | None) -> None:
    song_node = root.find("./head/song")
    if song_node is not None and song_node.text:
        song_node.text = f"{song_node.text} {title_suffix}".strip()
    comment_node = root.find("./head/comment")
    if comment_node is not None:
        comment_node.text = f"Showcase clip {title_suffix}".strip()
    media_node = root.find("./head/mediaFile")
    if media_node is not None and media_name:
        media_node.text = media_name
    duration_node = root.find("./head/sequenceDuration")
    if duration_node is not None:
        duration_node.text = f"{duration_ms / 1000.0:.3f}"


def _ffmpeg_exe() -> str | None:
    imageio_ffmpeg = optional_import("imageio_ffmpeg")
    if imageio_ffmpeg is None:
        return None
    try:
        return str(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None


def trim_audio(audio_path: Path, out_path: Path, *, start_s: float, duration_s: float) -> None:
    ffmpeg = _ffmpeg_exe()
    if ffmpeg is None:
        raise RuntimeError("imageio_ffmpeg is required to create the showcase clip audio.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        f"{start_s:.3f}",
        "-i",
        str(audio_path),
        "-t",
        f"{duration_s:.3f}",
        "-c:a",
        "pcm_s16le",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_showcase_clip(
    *,
    xsq_path: Path,
    out_dir: Path,
    start_s: float,
    duration_s: float = 20.0,
    audio_path: Path | None = None,
) -> tuple[Path, Path | None]:
    tree = ET.parse(xsq_path)
    root = tree.getroot()
    start_ms = int(round(start_s * 1000.0))
    duration_ms = int(round(duration_s * 1000.0))
    end_ms = start_ms + duration_ms

    out_dir.mkdir(parents=True, exist_ok=True)
    clip_tag = f"showcase_{int(round(start_s)):03d}s_{int(round(duration_s)):02d}s"
    audio_out: Path | None = None
    if audio_path is not None and audio_path.exists():
        audio_out = out_dir / f"{_infer_audio_stem(xsq_path)}.{clip_tag}.wav"
        trim_audio(audio_path, audio_out, start_s=start_s, duration_s=duration_s)

    _trim_effects(root, start_ms, end_ms)
    _update_head(root, title_suffix=clip_tag, duration_ms=duration_ms, media_name=(audio_out.name if audio_out else None))

    out_path = out_dir / f"{xsq_path.stem}.{clip_tag}.xsq"
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path, audio_out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a short showcase XSQ clip from a full sequence.")
    parser.add_argument("xsq", help="Source XSQ file")
    parser.add_argument("--audio", help="Matching source audio file to trim alongside the XSQ")
    parser.add_argument("--start", type=float, required=True, help="Clip start in seconds")
    parser.add_argument("--duration", type=float, default=20.0, help="Clip duration in seconds")
    parser.add_argument("--output-dir", default="outputs/showcase_clips", help="Directory for the generated clip")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    xsq_path = (root / args.xsq).resolve() if not Path(args.xsq).is_absolute() else Path(args.xsq)
    audio_path = None
    if args.audio:
        audio_path = (root / args.audio).resolve() if not Path(args.audio).is_absolute() else Path(args.audio)
    out_dir = (root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    out_xsq, out_audio = build_showcase_clip(
        xsq_path=xsq_path,
        out_dir=out_dir,
        start_s=float(args.start),
        duration_s=float(args.duration),
        audio_path=audio_path,
    )
    print(f"Created showcase clip: {out_xsq}", flush=True)
    if out_audio is not None:
        print(f"Created showcase audio: {out_audio}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
