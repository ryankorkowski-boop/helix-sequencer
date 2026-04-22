from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from core import engine_profiles


def _effect_engine():
    from core import effect_engine

    return effect_engine


def available_profiles() -> list[engine_profiles.EngineProfile]:
    return engine_profiles.available_profiles()


def available_versions() -> list[str]:
    return [profile.version for profile in available_profiles()]


def run_profile(profile_id: str | None, engine_args: list[str] | None = None) -> None:
    profile = engine_profiles.resolve_profile(profile_id)
    _effect_engine().main_for(profile.version, engine_args)


def run_version(version: str, engine_args: list[str] | None = None) -> None:
    run_profile(version, engine_args)


def build_sequence_set(profiles: Iterable[str | None], engine_args: list[str] | None = None) -> None:
    for profile_id in profiles:
        run_profile(profile_id, engine_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-click Dream Sequence Weaver entrypoint for show-ready xLights sequencing.",
        epilog=(
            "Examples:\n"
            "  python main.py --profile master -- --template template.xsq --audio song.wav --no-prompt --polish --variants 3 --auto-shortlist\n"
            "  python main.py --profile v27.3 -- --template template.xsq --audio song.wav --learn-from-my-xsqs"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list-profiles", action="store_true", help="List active sequencing profiles and exit.")
    parser.add_argument("--list-versions", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Sequencing profile to run. Defaults to the active master profile.",
    )
    parser.add_argument("--version-id", action="append", dest="profiles", help=argparse.SUPPRESS)
    parser.add_argument(
        "--birdsong-mode",
        action="store_true",
        help="Run Birdsong Engine Mode analysis/export (no XSQ write) for one audio file.",
    )
    parser.add_argument("--birdsong-audio", help="Audio file path for Birdsong Engine Mode.")
    parser.add_argument(
        "--birdsong-output-dir",
        help="Optional output directory for Birdsong exports. Defaults to outputs/birdsong.",
    )
    parser.add_argument("--birdsong-no-preview", action="store_true", help="Skip Birdsong HTML preview export.")
    parser.add_argument("--birdsong-no-ply", action="store_true", help="Skip Birdsong PLY trajectory export.")
    parser.add_argument("--birdsong-use-umap", action="store_true", help="Use UMAP if installed for 3D reduction.")
    parser.add_argument(
        "--birdsong-use-basic-pitch",
        action="store_true",
        help="Use Spotify Basic Pitch if installed for pitch contour extraction.",
    )
    parser.add_argument(
        "engine_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to the selected effect engine, including polish, variant, shortlist, and learning flags.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles or args.list_versions:
        for profile in available_profiles():
            print(f"{profile.profile_id}: {profile.title} [{profile.version}]")
        return 0

    if args.birdsong_mode:
        from core import birdsong_mode
        from xlights import xsq_writer as base

        requested = args.birdsong_audio
        if requested:
            audio_path = Path(requested).resolve()
            if not audio_path.exists():
                raise SystemExit(f"Birdsong audio file not found: {requested}")
        else:
            discovered = base.list_audio_files(Path(".").resolve())
            if not discovered:
                raise SystemExit("Birdsong mode needs an audio file. Use --birdsong-audio path/to/song.wav")
            audio_path = discovered[0].resolve()
        output_dir = (
            Path(args.birdsong_output_dir).resolve()
            if args.birdsong_output_dir
            else (Path(".").resolve() / "outputs" / "birdsong")
        )
        result = birdsong_mode.run_birdsong_mode(
            audio_path=audio_path,
            output_dir=output_dir,
            preview=not bool(args.birdsong_no_preview),
            export_ply=not bool(args.birdsong_no_ply),
            use_umap=bool(args.birdsong_use_umap),
            use_basic_pitch=bool(args.birdsong_use_basic_pitch),
            log_fn=print,
        )
        print(f"Birdsong analysis complete: {result.audio_path.name}")
        print(f"- JSON: {result.json_path}")
        print(f"- CSV: {result.csv_path}")
        print(f"- Mapping: {result.mapping_json_path}")
        if result.ply_path is not None:
            print(f"- PLY: {result.ply_path}")
        if result.preview_html_path is not None:
            print(f"- Preview: {result.preview_html_path}")
        return 0

    profiles = args.profiles or [engine_profiles.ACTIVE_PROFILE_ID]
    engine_args = list(args.engine_args)
    if engine_args[:1] == ["--"]:
        engine_args = engine_args[1:]
    build_sequence_set(profiles, engine_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
