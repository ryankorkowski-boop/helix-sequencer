from __future__ import annotations

import argparse
from typing import Iterable

from core import engine_profiles
from core.effects_orchestrator_bridge import run_effects_orchestration


def _effect_engine():
    from core import effect_engine

    return effect_engine


def available_profiles() -> list[engine_profiles.EngineProfile]:
    return engine_profiles.available_profiles()


def available_versions() -> list[str]:
    return [profile.version for profile in available_profiles()]


def _orchestration_enabled(engine_args: list[str] | None) -> bool:
    args = engine_args or []
    if "--no-effects-orchestrator" in args:
        return False
    return True


def _clean_engine_args(engine_args: list[str] | None) -> list[str] | None:
    if engine_args is None:
        return None
    return [arg for arg in engine_args if arg != "--no-effects-orchestrator"]


def run_profile(profile_id: str | None, engine_args: list[str] | None = None) -> None:
    profile = engine_profiles.resolve_profile(profile_id)
    if _orchestration_enabled(engine_args):
        report = run_effects_orchestration(engine_args)
        if report.invoked:
            print(f"effects_orchestrator: invoked passes={len(report.passes)} report={report.report_path}")
        else:
            print(f"effects_orchestrator: unavailable error={report.error}")
    _effect_engine().main_for(profile.version, _clean_engine_args(engine_args))


def run_version(version: str, engine_args: list[str] | None = None) -> None:
    run_profile(version, engine_args)


def build_sequence_set(profiles: Iterable[str | None], engine_args: list[str] | None = None) -> None:
    for profile_id in profiles:
        run_profile(profile_id, engine_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Modular entrypoint for the xLights sequencing pipeline.")
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
        "engine_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to the selected effect engine. Use --no-effects-orchestrator to skip the canonical effects orchestrator.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles or args.list_versions:
        for profile in available_profiles():
            print(f"{profile.profile_id}: {profile.title} [{profile.version}]")
        return 0

    profiles = args.profiles or [engine_profiles.ACTIVE_PROFILE_ID]
    engine_args = list(args.engine_args)
    if engine_args[:1] == ["--"]:
        engine_args = engine_args[1:]
    build_sequence_set(profiles, engine_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
