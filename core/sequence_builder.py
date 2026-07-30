from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Iterable

from core import engine_profiles
from core.effects_orchestration_bridge import EffectsOrchestrationRunReport, run_effects_orchestration
from core.prime_beat_grid import prime_beat_grid_args
from core.run_config import RunConfig
from core.run_manager import RunContext, RunManager

NO_EFFECTS_ORCHESTRATOR_FLAG = "--no-effects-orchestrator"
PROMOTE_ORCHESTRATOR_TEMPLATE_FLAG = "--promote-orchestrated-template"
NO_ORCHESTRATOR_TEMPLATE_PROMOTION_FLAG = "--no-orchestrator-template-promotion"
BEAT_GRID_FLAGS = {
    "--snap-grid",
    "--snap-bpm",
    "--snap-offset-ms",
    "--snap-mode",
    "--snap-max-shift-ms",
    "--no-snap",
}
BEAT_GRID_VALUE_FLAGS = BEAT_GRID_FLAGS - {"--no-snap"}
ORCHESTRATOR_ONLY_FLAGS = {
    NO_EFFECTS_ORCHESTRATOR_FLAG,
    PROMOTE_ORCHESTRATOR_TEMPLATE_FLAG,
    NO_ORCHESTRATOR_TEMPLATE_PROMOTION_FLAG,
}
_ARTIFACT_KIND_BY_SUFFIX = {
    ".xsq": "xsq",
    ".fseq": "fseq",
    ".report.json": "report",
    ".sequence_notes.txt": "sequence_notes",
    ".chronoflow.json": "chronoflow_json",
    ".chronoflow.html": "chronoflow_html",
    ".snowman_band.json": "snowman_band_json",
    "placement_plan.json": "placement_plan",
    "xlights_effect_contract.json": "xlights_effect_contract",
}


def _effect_engine():
    from core import effect_engine_beat_grid

    return effect_engine_beat_grid


def available_profiles() -> list[engine_profiles.EngineProfile]:
    return engine_profiles.available_profiles()


def available_versions() -> list[str]:
    return [profile.version for profile in available_profiles()]


def _orchestration_enabled(engine_args: list[str] | None) -> bool:
    args = engine_args or []
    return NO_EFFECTS_ORCHESTRATOR_FLAG not in args


def _orchestrator_template_promotion_enabled(engine_args: list[str] | None) -> bool:
    args = engine_args or []
    if NO_EFFECTS_ORCHESTRATOR_FLAG in args or NO_ORCHESTRATOR_TEMPLATE_PROMOTION_FLAG in args:
        return False
    return PROMOTE_ORCHESTRATOR_TEMPLATE_FLAG in args


def _clean_engine_args(engine_args: list[str] | None) -> list[str] | None:
    if engine_args is None:
        return None
    return [arg for arg in engine_args if arg not in ORCHESTRATOR_ONLY_FLAGS]


def _strip_beat_grid_args(engine_args: list[str] | None) -> list[str] | None:
    if engine_args is None:
        return None
    out: list[str] = []
    idx = 0
    while idx < len(engine_args):
        arg = engine_args[idx]
        if arg in BEAT_GRID_VALUE_FLAGS:
            idx += 2
            continue
        if arg == "--no-snap":
            idx += 1
            continue
        out.append(arg)
        idx += 1
    return out


def _has_explicit_beat_grid_args(engine_args: list[str] | None) -> bool:
    return any(arg in BEAT_GRID_FLAGS for arg in (engine_args or []))


def _apply_prime_beat_grid_defaults(profile_id_or_version: str | None, engine_args: list[str] | None) -> list[str] | None:
    args = list(engine_args or [])
    if _has_explicit_beat_grid_args(args):
        return args
    defaults = prime_beat_grid_args(profile_id_or_version=profile_id_or_version, engine_args=args, output_root=Path("."))
    return defaults + args if defaults else args


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
    """Optionally feed orchestrated planning back into the canonical renderer path.

    The orchestrator writes an inspected `*.orchestrated.xsq` from the user-provided
    template when possible. Promotion is intentionally explicit so the orchestrator
    can remain on by default for reports/contracts while broad test runs and normal
    sidecar users are not surprised by a generated template replacing their input.
    """
    cleaned = _clean_engine_args(engine_args)
    if not _orchestrator_template_promotion_enabled(engine_args):
        return cleaned
    if report is None or not report.invoked or not report.xsq_written or not report.orchestrated_xsq_path:
        return cleaned
    promoted_template = Path(report.orchestrated_xsq_path).as_posix()
    return _set_or_replace_arg(list(cleaned or []), "--template", promoted_template)


def _record_orchestration_artifacts(ctx: RunContext, report: EffectsOrchestrationRunReport | None) -> None:
    if report is None:
        return
    artifact_paths = (
        ("effects_orchestration_report", getattr(report, "report_path", None)),
        ("placement_plan", getattr(report, "placement_plan_path", None)),
        ("effect_contract", getattr(report, "effect_contract_path", None)),
        ("orchestrated_xsq", getattr(report, "orchestrated_xsq_path", None)),
        ("xsq_render_report", getattr(report, "xsq_render_report_path", None)),
    )
    for kind, path in artifact_paths:
        if path:
            ctx.record_artifact(kind, Path(path))
    if getattr(report, "error", None):
        ctx.record_warning(f"effects_orchestrator: {report.error}")


def _artifact_search_roots(config: RunConfig, version: str) -> list[Path]:
    roots = [config.output_root]
    if config.output_root == Path("outputs"):
        family = version.split(".", 1)[0]
        if family:
            roots.append(Path(family))
    return _unique_paths(roots)


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _snapshot_known_artifacts(roots: Iterable[Path]) -> dict[Path, tuple[int, int]]:
    snapshot: dict[Path, tuple[int, int]] = {}
    for artifact in _known_artifact_paths(roots):
        try:
            stat = artifact.stat()
        except OSError:
            continue
        snapshot[artifact.resolve(strict=False)] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def _record_changed_artifacts(
    ctx: RunContext,
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
) -> None:
    for artifact in _known_artifact_paths(roots):
        resolved = artifact.resolve(strict=False)
        try:
            stat = artifact.stat()
        except OSError:
            continue
        if before.get(resolved) == (stat.st_mtime_ns, stat.st_size):
            continue
        ctx.record_artifact(_artifact_kind(artifact), artifact)


def _known_artifact_paths(roots: Iterable[Path]) -> list[Path]:
    paths: list[Path] = []
    for root in _unique_paths(roots):
        if not root.exists():
            continue
        paths.extend(path for path in root.rglob("*") if path.is_file() and _is_known_artifact(path))
    return sorted(paths, key=lambda path: str(path))


def _is_known_artifact(path: Path) -> bool:
    name = path.name
    return any(name.endswith(suffix) for suffix in _ARTIFACT_KIND_BY_SUFFIX)


def _artifact_kind(path: Path) -> str:
    name = path.name
    for suffix, kind in sorted(_ARTIFACT_KIND_BY_SUFFIX.items(), key=lambda item: len(item[0]), reverse=True):
        if name.endswith(suffix):
            return kind
    return "artifact"


def _run_birdsong_hook(config: RunConfig, engine_args: list[str] | None, ctx: RunContext) -> None:
    """Guarded, minimal birdsong post-run adapter.

    This implementation is intentionally conservative: it runs only when the
    engine args include an explicit birdsong-enabling flag ("--enable-birdsong").
    It synthesizes a short demo feature-frame sequence if real per-frame audio
    features aren't available, builds a birdsong plan using the Issue #2
    runtime, writes a manifest into the run output, and records the manifest
    as an artifact in the run context.
    """
    args = list(engine_args or [])
    enabled = any(a in ("--enable-birdsong", "--birdsong", "--birdsong-enabled") for a in args)
    if not enabled:
        return

    try:
        from core import birdsong_issue2_runtime as birdsong
        from core import feature_state
    except Exception as exc:  # pragma: no cover - defensive
        ctx.record_warning(f"birdsong: import failed: {exc}")
        return

    # Try to discover model names from provided template; fall back to a small default set.
    template_path: Path | None = None
    for idx, a in enumerate(args):
        if a == "--template" and idx + 1 < len(args):
            template_path = Path(args[idx + 1])
            break

    model_names: list[str] = []
    if template_path is not None and template_path.exists():
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(template_path)
            root = tree.getroot()
            # Collect any element with a name attribute (models/elements)
            seen: set[str] = set()
            for el in root.iter():
                name = el.get("name")
                if name:
                    key = name.strip()
                    if key and key not in seen:
                        seen.add(key)
                        model_names.append(key)
        except Exception:
            model_names = []

    if not model_names:
        # Conservative default pool to allow birdsong to place some demo rows.
        model_names = [
            "Helix_Birdsong_Group",
            "Mega Tree",
            "Left Tree",
            "Right Tree",
            "Center Arch",
        ]

    # Build a short synthetic feature sequence (20s @ 10 fps -> 200 frames) as a demo.
    duration_seconds = 20.0
    fps = 10.0
    steps = max(1, int(duration_seconds * fps))
    import math

    energy = [max(0.0, min(1.0, 0.25 + 0.6 * (0.5 + 0.5 * math.sin(2 * math.pi * (i / max(1, steps)) * 3)))) for i in range(steps)]
    centroid = [4000.0 + 2000.0 * math.sin(2 * math.pi * (i / max(1, steps)) * 1.2) for i in range(steps)]

    features = {
        "energy": energy,
        "centroid": centroid,
        "tempo": 120.0,
    }

    frames = feature_state.build_feature_state_sequence(features, fps=fps)
    if not frames:
        ctx.record_warning("birdsong: no feature frames could be built for demo")
        return

    cfg = birdsong.BirdsongRuntimeConfig(enabled=True)
    plan = birdsong.plan_birdsong_runtime(frames, model_names, config=cfg)

    # Write manifest in the configured output root
    try:
        out_root = Path(config.output_root or Path("outputs"))
    except Exception:
        out_root = Path("outputs")
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / "birdsong_runtime_manifest.json"
    try:
        birdsong.write_birdsong_runtime_manifest(manifest_path, frames, model_names, config=cfg)
        ctx.record_artifact("birdsong_runtime_manifest", manifest_path)
        # Record a short run note
        motifs = list(plan.decision_report.motifs) if plan and plan.decision_report else []
        ctx.record_warning(f"birdsong: generated rows={len(plan.rows)} phrases={len(plan.phrase_snapshots)} motifs={motifs}")
    except Exception as exc:  # pragma: no cover - defensive
        ctx.record_warning(f"birdsong: failed to write manifest: {exc}")


def _artifact_search_roots(config: RunConfig, version: str) -> list[Path]:
    roots = [config.output_root]
    if config.output_root == Path("outputs"):
        family = version.split(".", 1)[0]
        if family:
            roots.append(Path(family))
    return _unique_paths(roots)


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _snapshot_known_artifacts(roots: Iterable[Path]) -> dict[Path, tuple[int, int]]:
    snapshot: dict[Path, tuple[int, int]] = {}
    for artifact in _known_artifact_paths(roots):
        try:
            stat = artifact.stat()
        except OSError:
            continue
        snapshot[artifact.resolve(strict=False)] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def _record_changed_artifacts(
    ctx: RunContext,
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
) -> None:
    for artifact in _known_artifact_paths(roots):
        resolved = artifact.resolve(strict=False)
        try:
            stat = artifact.stat()
        except OSError:
            continue
        if before.get(resolved) == (stat.st_mtime_ns, stat.st_size):
            continue
        ctx.record_artifact(_artifact_kind(artifact), artifact)


def _known_artifact_paths(roots: Iterable[Path]) -> list[Path]:
    paths: list[Path] = []
    for root in _unique_paths(roots):
        if not root.exists():
            continue
        paths.extend(path for path in root.rglob("*") if path.is_file() and _is_known_artifact(path))
    return sorted(paths, key=lambda path: str(path))


def _is_known_artifact(path: Path) -> bool:
    name = path.name
    return any(name.endswith(suffix) for suffix in _ARTIFACT_KIND_BY_SUFFIX)


def _artifact_kind(path: Path) -> str:
    name = path.name
    for suffix, kind in sorted(_ARTIFACT_KIND_BY_SUFFIX.items(), key=lambda item: len(item[0]), reverse=True):
        if name.endswith(suffix):
            return kind
    return "artifact"


def run_profile(profile_id: str | None, engine_args: list[str] | None = None) -> None:
    """Run a sequencing profile with integrated run tracking."""
    try:
        profile = engine_profiles.resolve_profile(profile_id)
    except (KeyError, ValueError) as e:
        print(f"ERROR: Invalid profile '{profile_id}': {e}", file=sys.stderr)
        raise SystemExit(1)

    raw_engine_args = list(engine_args or [])
    has_explicit_beat_grid_args = _has_explicit_beat_grid_args(raw_engine_args)
    engine_args = _apply_prime_beat_grid_defaults(profile.version, raw_engine_args)
    resolved_profile_id = getattr(profile, "profile_id", profile_id or engine_profiles.ACTIVE_PROFILE_ID)

    try:
        config = RunConfig.from_engine_args(resolved_profile_id, engine_args or [])
    except (ValueError, TypeError) as e:
        print(f"ERROR: Invalid arguments: {e}", file=sys.stderr)
        print("Use --help for usage information.", file=sys.stderr)
        raise SystemExit(1)

    command = ["main.py", "--profile", resolved_profile_id, "--", *(engine_args or [])]
    try:
        ctx = RunManager(config).start(command=command, require_existing=False)
    except (OSError, IOError, ValueError) as e:
        print(f"ERROR: Failed to initialize run directory: {e}", file=sys.stderr)
        raise SystemExit(1)

    try:
        report: EffectsOrchestrationRunReport | None = None
        if _orchestration_enabled(engine_args):
            report = run_effects_orchestration(engine_args)
            if report.invoked:
                print(f"effects_orchestrator: invoked passes={len(report.passes)} report={report.report_path}")
            else:
                print(f"effects_orchestrator: unavailable error={report.error}")
            _record_orchestration_artifacts(ctx, report)

        effective_engine_args = _promote_orchestrated_template(engine_args, report)
        if not has_explicit_beat_grid_args:
            effective_engine_args = _strip_beat_grid_args(effective_engine_args)
        if report is not None and report.invoked and report.xsq_written and effective_engine_args != _clean_engine_args(engine_args):
            print(f"effects_orchestrator: promoted template={report.orchestrated_xsq_path}")

        artifact_roots = _artifact_search_roots(config, profile.version)
        artifact_snapshot = _snapshot_known_artifacts(artifact_roots)
        try:
            _effect_engine().main_for(profile.version, effective_engine_args)
            # Optional birdsong post-run hook (guarded by explicit engine flag)
            try:
                _run_birdsong_hook(config, engine_args, ctx)
            except Exception as exc:  # pragma: no cover - safe guard
                print(f"birdsong: post-run hook failed: {exc}", file=sys.stderr)
        finally:
            _record_changed_artifacts(ctx, artifact_roots, artifact_snapshot)
            ctx.record_artifact("configured_output_root", config.output_root)

        ctx.finalize(success=True)
        print(f"SUCCESS: Run completed. Manifest: {ctx.manifest_path}", file=sys.stderr)

    except KeyboardInterrupt:
        error_summary = "Run interrupted by user (Ctrl+C)"
        print(f"\nINTERRUPTED: {error_summary}", file=sys.stderr)
        ctx.finalize(success=False, error_summary=error_summary)
        raise SystemExit(130)

    except Exception as e:
        error_summary = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_summary}", file=sys.stderr)
        print(f"Manifest saved to: {ctx.manifest_path}", file=sys.stderr)
        ctx.finalize(success=False, error_summary=error_summary)
        raise SystemExit(1)


def run_version(version: str, engine_args: list[str] | None = None) -> None:
    """Run a specific version profile."""
    run_profile(version, engine_args)


def build_sequence_set(profiles: Iterable[str | None], engine_args: list[str] | None = None) -> None:
    """Build sequences for multiple profiles."""
    for profile_id in profiles:
        run_profile(profile_id, engine_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Helix Sequencer: Automated audio-to-light sequencing for xLights.",
        epilog=(
            "Engine arguments (after --): Passed directly to the effect engine.\n"
            "  --no-effects-orchestrator: Skip orchestration pass.\n"
            "  --promote-orchestrated-template: Use orchestrator output as input template.\n"
            "  --no-orchestrator-template-promotion: Force sidecar-only behavior.\n"
            "  --snap-grid 16: Snap timing to sixteenth-note grid.\n"
            "  --no-snap: Disable Prime BeatGrid timing alignment."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit.",
    )
    parser.add_argument(
        "--list-versions",
        action="store_true",
        help=argparse.SUPPRESS,  # Hidden for backwards compatibility
    )
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Profile to run (can specify multiple times). Defaults to active master profile.",
    )
    parser.add_argument(
        "--version-id",
        action="append",
        dest="profiles",
        help=argparse.SUPPRESS,  # Hidden for backwards compatibility
    )
    parser.add_argument(
        "engine_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the effect engine (after --).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entrypoint with comprehensive error handling."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles or args.list_versions:
        for profile in available_profiles():
            print(f"{profile.version}\t{profile.title}\t{profile.description}")
        return 0

    profiles = args.profiles or [None]
    engine_args = list(args.engine_args or [])
    if engine_args and engine_args[0] == "--":
        engine_args = engine_args[1:]

    build_sequence_set(profiles, engine_args)
    return 0
