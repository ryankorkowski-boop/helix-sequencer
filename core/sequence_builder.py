from __future__ import annotations

import argparse
from typing import Iterable

from core import engine_profiles
from core.effects_orchestrator_bridge import EffectsOrchestrationRunReport, run_effects_orchestration
from core.run_config import RunConfig
from core.run_manager import RunManager

NO_EFFECTS_ORCHESTRATOR_FLAG = "--no-effects-orchestrator"
NO_ORCHESTRATOR_TEMPLATE_PROMOTION_FLAG = "--no-orchestrator-template-promotion"
ORCHESTRATOR_ONLY_FLAGS = {
    NO_EFFECTS_ORCHESTRATOR_FLAG,
    NO_ORCHESTRATOR_TEMPLATE_PROMOTION_FLAG,
}


def _effect_engine():
    from core import effect_engine

    return effect_engine


def available_profiles() -> list[engine_profiles.EngineProfile]:
    return engine_profiles.available_profiles()


def available_versions() -> list[str]:
    return [profile.version for profile in available_profiles()]


def _orchestration_enabled(engine_args: list[str] | None) -> bool:
    args = engine_args or []
    return NO_EFFECTS_ORCHESTRATOR_FLAG not in args


def _orchestrator_template_promotion_enabled(engine_args: list[str] | None) -> bool:
    args = engine_args or []
    if NO_EFFECTS_ORCHESTRATOR_FLAG in args:
        return False
    return NO_ORCHESTRATOR_TEMPLATE_PROMOTION_FLAG not in args


def _clean_engine_args(engine_args: list[str] | None) -> list[str] | None:
    if engine_args is None:
        return None
    return [arg for arg in engine_args if arg not in ORCHESTRATOR_ONLY_FLAGS]


def _set_or_replace_arg(args: list[str], flag: str, value: str) -> list[str]:
    out: list[str] = []
    replaced = False
    idx = 0
    while idx < len(args):
        item = args[idx]
        if item == flag:
            out.extend([flag, value])
            replaced = True
            idx += 2
            continue
        out.append(item)
        idx += 1
    if not replaced:
        out.extend([flag, value])
    return out


def _promote_orchestrated_template(
    engine_args: list[str] | None,
    report: EffectsOrchestrationRunReport | None,
) -> list[str] | None:
    """Feed orchestrated planning back into the canonical renderer path.

    The orchestrator writes an inspected `*.orchestrated.xsq` from the user-provided
    template when possible. Passing that file as the next template means the normal
    effect engine builds on top of the orchestrated native rows instead of leaving
    them as a detached sidecar artifact.
    """
    cleaned = _clean_engine_args(engine_args)
    if not _orchestrator_template_promotion_enabled(engine_args):
        return cleaned
    if report is None or not report.invoked or not report.xsq_written or not report.orchestrated_xsq_path:
        return cleaned
    promoted_template = str(report.orchestrated_xsq_path)
    return _set_or_replace_arg(list(cleaned or []), "--template", promoted_template)


def _record_orchestration_artifacts(ctx, report: EffectsOrchestrationRunReport | None) -> None:
    if report is None:
        return
    artifacts = (
        ("effects_orchestration_report", getattr(report, "report_path", None)),
        ("placement_plan", getattr(report, "placement_plan_path", None)),
        ("effect_contract", getattr(report, "effect_contract_path", None)),
        ("orchestrated_xsq", getattr(report, "orchestrated_xsq_path", None)),
        ("xsq_render_report", getattr(report, "xsq_render_report_path", None)),
    )
    for kind, path in artifacts:
        if path:
            ctx.record_artifact(kind, path)


def run_profile(profile_id: str | None, engine_args: list[str] | None = None) -> None:
    profile = engine_profiles.resolve_profile(profile_id)
    original_engine_args = list(engine_args or [])
    resolved_profile_id = getattr(profile, "profile_id", profile_id or engine_profiles.ACTIVE_PROFILE_ID)
    run_config = RunConfig.from_engine_args(resolved_profile_id, original_engine_args)
    command = ["main.py", "--profile", resolved_profile_id, "--", *original_engine_args]
    with RunManager(run_config).start(command=command, require_existing=False) as ctx:
        report: EffectsOrchestrationRunReport | None = None
        if _orchestration_enabled(engine_args):
            report = run_effects_orchestration(engine_args)
            if report.invoked:
                print(f"effects_orchestrator: invoked passes={len(report.passes)} report={report.report_path}")
            else:
                print(f"effects_orchestrator: unavailable error={report.error}")
        _record_orchestration_artifacts(ctx, report)
        effective_engine_args = _promote_orchestrated_template(engine_args, report)
        if report is not None and report.invoked and report.xsq_written and effective_engine_args != _clean_engine_args(engine_args):
            print(f"effects_orchestrator: promoted template={report.orchestrated_xsq_path}")
        _effect_engine().main_for(profile.version, effective_engine_args)
        ctx.record_artifact("configured_output_root", run_config.output_root)



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
        help=(
            "Arguments passed directly to the selected effect engine. "
            "Use --no-effects-orchestrator to skip the canonical effects orchestrator, "
            "or --no-orchestrator-template-promotion to keep the orchestrated XSQ as a sidecar only."
        ),
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
