from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_helixville4_full_band_layout import build_full_band_layout
from tools.export_helixville4_band_xmodels import export_band_xmodels

DEFAULT_OUTPUT_DIR = ROOT / "test_runs" / "helixville4_full_band_lightsouttheme_120s"
DEFAULT_AUDIO = ROOT / "LightsOutTheme.mp3"
DEFAULT_TEMPLATE = ROOT / "template.xsq"
DEFAULT_LAYOUT_SOURCE = ROOT / "xlights_rgbeffects.xml"
TARGET_DURATION_SECONDS = 120


def _run(command: list[str], *, dry_run: bool = False) -> None:
    print(" ".join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=ROOT, check=True)


def _trimmed_audio_path(output_dir: Path) -> Path:
    return output_dir / "LightsOutTheme_120s.mp3"


def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg  # type: ignore

        return str(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return "ffmpeg"


def trim_audio_to_120s(audio: Path, output_dir: Path) -> Path:
    target = _trimmed_audio_path(output_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not audio.exists():
        raise FileNotFoundError(f"Audio file not found: {audio}")

    command = [
        _ffmpeg_exe(),
        "-y",
        "-i",
        str(audio),
        "-t",
        str(TARGET_DURATION_SECONDS),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(target),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        shutil.copyfile(audio, target)
    return target


def build_sequence_command(
    *,
    profile: str,
    audio: Path,
    layout: Path,
    template: Path,
    output_dir: Path,
    variants: int,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "core.sequence_builder",
        "--profile",
        profile,
        "--",
        "--template",
        str(template),
        "--audio",
        str(audio),
        "--layout-file",
        str(layout),
        "--single",
        "--output-dir",
        str(output_dir),
        "--variants",
        str(variants),
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-matrix-intelligence",
        "--audio-reactive-profile",
        "showcase",
        "--flash-guard",
        "0.95",
        "--spatial-awareness",
        "0.8",
        "--chase-style",
        "top_to_bottom",
        "--polyphony",
        "4",
        "--keyboard-mix",
        "0.58",
        "--max-layers-per-prop",
        "2",
    ]


def _variant_sequences(output_dir: Path, audio: Path, profile: str) -> list[str]:
    primary = output_dir / f"{audio.stem},{profile}.xsq"
    generated = sorted(path for path in output_dir.glob(f"{audio.stem},{profile}*.xsq") if path.is_file())
    if primary.exists() and primary not in generated:
        generated.insert(0, primary)
    return [str(path) for path in generated]


def _friendly_variant_name(audio: Path, profile: str, index: int) -> str:
    profile_token = profile.replace(".", "_").replace("-", "_")
    return f"{audio.stem}_{profile_token}_variant_{index}.xsq"


def _write_friendly_sequence_copies(output_dir: Path, audio: Path, profile: str) -> list[str]:
    primary = output_dir / f"{audio.stem},{profile}.xsq"
    originals = [primary]
    originals.extend(sorted(output_dir.glob(f"{audio.stem},{profile}.alt*.xsq")))
    copied: list[str] = []
    for index, source in enumerate([path for path in originals if path.exists()], start=1):
        target = output_dir / _friendly_variant_name(audio, profile, index)
        shutil.copy2(source, target)
        copied.append(str(target))
    return copied


def run_full_band_lightsouttheme_120s(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    audio: Path = DEFAULT_AUDIO,
    template: Path = DEFAULT_TEMPLATE,
    source_layout: Path | None = DEFAULT_LAYOUT_SOURCE,
    profile: str = "v27.3",
    variants: int = 3,
    dry_run: bool = False,
) -> dict[str, object]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    layout_payload = build_full_band_layout(output_dir, source_layout=source_layout)
    layout = output_dir / "xlights_rgbeffects.xml"
    export_payload = export_band_xmodels(output_dir / "band_xmodel_exports")
    audio_120s = trim_audio_to_120s(audio.resolve(), output_dir)
    sequence_command = build_sequence_command(
        profile=profile,
        audio=audio_120s,
        layout=layout,
        template=template.resolve(),
        output_dir=output_dir,
        variants=variants,
    )

    friendly_sequences: list[str] = []
    if not dry_run:
        _run(sequence_command)
        friendly_sequences = _write_friendly_sequence_copies(output_dir, audio_120s, profile)

    payload: dict[str, object] = {
        "schema": "helixville4.full_band_lightsouttheme_120s.v1",
        "status": "commands_completed" if not dry_run else "dry_run",
        "duration_seconds_target": TARGET_DURATION_SECONDS,
        "audio": str(audio_120s),
        "layout": str(layout),
        "profile": profile,
        "source_layout": str(source_layout.resolve()) if source_layout is not None else "",
        "variant_count_requested": variants,
        "variant_sequences": _variant_sequences(output_dir, audio_120s, profile),
        "xlights_friendly_variant_sequences": friendly_sequences,
        "approved_full_band_export": layout_payload.get("approved_full_band_export", {}),
        "band_xmodel_export": export_payload,
        "commands": {
            "sequence": sequence_command,
        },
        "notes": [
            "The generated layout uses approved Helixville4 full snowman band custom models.",
            "The layout is copied from the source xlights_rgbeffects.xml before band patching so non-band models are preserved.",
            "Sequence target xmodels are exported beside the run for active *_BODY and *_INSTRUMENT rows.",
            "LightsOutTheme is trimmed to a stable 120-second MP3 before sequence generation.",
        ],
    }
    report = output_dir / "full_band_lightsouttheme_120s.run.json"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Helixville4 full-band 120-second LightsOutTheme variant generation.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--source-layout", type=Path, default=DEFAULT_LAYOUT_SOURCE)
    parser.add_argument("--profile", default="v27.3")
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_full_band_lightsouttheme_120s(
        output_dir=args.output_dir,
        audio=args.audio,
        template=args.template,
        source_layout=args.source_layout,
        profile=args.profile,
        variants=args.variants,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
