from __future__ import annotations

import argparse
from typing import Iterable

from core import effect_engine


def available_versions() -> list[str]:
    return sorted(effect_engine.VARIANTS.keys())


def run_version(version: str, engine_args: list[str] | None = None) -> None:
    if version not in effect_engine.VARIANTS:
        raise KeyError(f"Unknown version: {version}")
    effect_engine.main_for(version, engine_args)


def build_sequence_set(versions: Iterable[str], engine_args: list[str] | None = None) -> None:
    for version in versions:
        run_version(version, engine_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Modular entrypoint for the xLights sequencing pipeline.")
    parser.add_argument("--list-versions", action="store_true", help="List available engine versions and exit.")
    parser.add_argument(
        "--version-id",
        action="append",
        dest="versions",
        help="One or more effect engine versions to run. Repeat the flag to run several versions.",
    )
    parser.add_argument(
        "engine_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to the selected effect engine.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_versions:
        for version in available_versions():
            style = effect_engine.VARIANTS[version]
            print(f"{version}: {style.title} [{style.family}]")
        return 0

    versions = args.versions or ["v27.3"]
    engine_args = list(args.engine_args)
    if engine_args[:1] == ["--"]:
        engine_args = engine_args[1:]
    build_sequence_set(versions, engine_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
