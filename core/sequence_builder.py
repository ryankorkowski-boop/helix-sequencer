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
LOR_SOURCE_FLAG = "--helix-lor-source-lms"
PREVIEW_MP4_FLAG = "--helix-preview-mp4"
PREVIEW_SECONDS_FLAG = "--helix-preview-seconds"
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


def _apply_neon_palettes_to_generated_sequences(
    engine_args: list[str] | None,
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    ctx: RunContext,
) -> None:
    """Colorize only new/changed XSQs from explicit --palette-mode neon runs.

    Leave user templates and all other modes untouched. Keep an uncolored
    sidecar of each original generated sequence to permit independent audits.
    This is a palette-only post-pass; engine effect decisions are unchanged.
    """
    args = list(engine_args or [])
    neon_requested = "--palette-mode=neon" in args or any(
        arg == "--palette-mode" and i + 1 < len(args) and args[i + 1] == "neon"
        for i, arg in enumerate(args)
    )
    if not neon_requested:
        return

    import os
    import shutil
    import tempfile
    from tools.xsq_palette_repair import repair_xsq
    selected_layout=next((Path(args[i+1]) for i,a in enumerate(args[:-1]) if a=="--layout-file"),None)
    for source in _generated_sequence_paths(roots,before,engine_args):

        with tempfile.NamedTemporaryFile(
            suffix=".xsq", prefix=".neon-palette-", dir=source.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        try:
            options={"layout_file":selected_layout} if selected_layout and selected_layout.is_file() else {}
            audit = repair_xsq(source, temporary, palette_mode="neon",**options)
            assigned = audit["changes"].get("palettes_assigned", 0)
            if not assigned:
                continue
            backup = source.with_name(source.stem + ".uncolored.xsq")
            shutil.copy2(source, backup)
            os.replace(temporary, source)
            ctx.record_artifact("xsq_uncolored_backup", backup)
            print(f"neon_palette: assigned={assigned} xsq={source}")
        finally:
            temporary.unlink(missing_ok=True)


def _validate_lor_generated_sequences(
    engine_args: list[str] | None,
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    ctx: RunContext,
) -> None:
    """Apply AC-only compatibility as a post-engine safeguard.

    Only files generated/changed in this run are processed; a source layout
    or user template is never rewritten. No LMS conversion code is needed.
    """
    if "--ac-lights-only" not in (engine_args or []):
        return
    import json
    import os
    import tempfile
    from tools.lor_compatibility import enforce_lor_xsq, inspect_lor_xsq

    args = list(engine_args or [])
    selected = next(
        (Path(args[i + 1]) for i, arg in enumerate(args[:-1]) if arg == "--layout-file"),
        None,
    )
    if selected is None or not selected.is_file():
        raise RuntimeError("LOR Compatible requires an existing --layout-file")
    template = next(
        (Path(args[i + 1]) for i, arg in enumerate(args[:-1]) if arg == "--template"),
        None,
    )
    protected = {template.resolve(strict=False)} if template else set()
    saved = 0
    for source in _known_artifact_paths(roots):
        if source.suffix.lower() != ".xsq" or ".orchestrated." in source.name:
            continue
        if source.resolve(strict=False) in protected:
            continue
        stat = source.stat()
        if before.get(source.resolve(strict=False)) == (stat.st_mtime_ns, stat.st_size):
            continue
        with tempfile.NamedTemporaryFile(
            suffix=".xsq", prefix=".lor-compat-", dir=source.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
        try:
            report = enforce_lor_xsq(source, temporary, selected)
            verification = inspect_lor_xsq(temporary, selected)
            if not verification["valid"]:
                raise ValueError(
                    "LOR output validation failed: "
                    + "; ".join(verification["issues"])
                )
            os.replace(temporary, source)
            path = source.with_suffix(".lor_compatibility.json")
            path.write_text(json.dumps({
                **report, "validation": verification, "xsq": str(source),
            }, indent=2) + "\n", encoding="utf-8")
            ctx.record_artifact("lor_compatibility_report", path)
            print(
                f"lor_compatible: {verification['effect_count']} native AC effects "
                f"on {report['used_single_color_models']} single-color models "
                f"(xLights XSQ; no LMS export) -> {source}",
                flush=True,
            )
            saved += 1
        finally:
            temporary.unlink(missing_ok=True)
    if not saved:
        raise RuntimeError(
            "LOR Compatible did not produce a validated new XSQ. "
            "Check template/layout names and the selected output folder."
        )


def _package_generated_xlights_show(
    engine_args: list[str] | None,
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    ctx: RunContext,
) -> None:
    """Place the used xLights layout next to every newly created XSQ.

    This follows xLights's show-folder contract, rather than assuming model
    definitions embedded inside XSQ. Never substitute the repo default for
    the user's chosen layout or overwrite an existing different layout.
    """
    from tools.show_context_bundle import package_audio_alongside, package_xlights_layout

    args = list(engine_args or [])
    layout = next(
        (Path(args[i + 1]) for i, arg in enumerate(args[:-1])
         if arg == "--layout-file"), None
    )
    if layout is None or not layout.is_file():
        print("show_context: no explicit layout supplied; no snapshot packaged", flush=True)
        return
    template = next(
        (Path(args[i + 1]) for i, arg in enumerate(args[:-1])
         if arg == "--template"), None
    )
    protected = {template.resolve(strict=False)} if template is not None else set()
    generated = []
    for path in _known_artifact_paths(roots):
        if path.suffix.lower() != ".xsq" or ".orchestrated." in path.name or ".uncolored." in path.name:
            continue
        resolved = path.resolve(strict=False)
        if resolved in protected:
            continue
        stat = path.stat()
        if before.get(resolved) == (stat.st_mtime_ns, stat.st_size):
            continue
        generated.append(path)
    for evidence in package_xlights_layout(generated, layout):
        ctx.record_artifact("xlights_show_context", Path(evidence["manifest"]))
        print(
            f"show_context: layout+configuration in {evidence['directory']}",
            flush=True,
        )
    audio = next(
        (Path(args[i + 1]) for i, a in enumerate(args[:-1])
         if a == "--audio"), None,
    )
    for media in package_audio_alongside(generated, audio):
        ctx.record_artifact("portable_show_audio", media)


def _generated_sequence_paths(
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    engine_args: list[str] | None,
) -> list[Path]:
    args = list(engine_args or [])
    template = next(
        (Path(args[i + 1]) for i, a in enumerate(args[:-1]) if a == "--template"),
        None,
    )
    protected = {template.resolve(strict=False)} if template else set()
    found = []
    for source in _known_artifact_paths(roots):
        if source.suffix.lower() != ".xsq":
            continue
        if ".uncolored." in source.name or ".orchestrated." in source.name:
            continue
        resolved = source.resolve(strict=False)
        if resolved in protected:
            continue
        stat = source.stat()
        if before.get(resolved) != (stat.st_mtime_ns, stat.st_size):
            found.append(source)
    return found


def _publish_native_lor_lms(
    source_lms: Path,
    workspace: Path,
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    engine_args: list[str],
    ctx: RunContext,
) -> None:
    import hashlib
    import json
    import shutil
    from tools.lor_lms_export_from_source import export_lms_from_xsq
    from tools.show_context_bundle import package_audio_alongside

    manifest = workspace / "lor_import_manifest.json"
    if not manifest.is_file():
        raise RuntimeError("Missing LOR import manifest")
    paths = _generated_sequence_paths(roots, before, engine_args)
    if not paths:
        raise RuntimeError("No Helix XSQ was generated for Light-O-Rama export")
    audio = next(
        (Path(engine_args[i + 1]) for i, a in enumerate(engine_args[:-1])
         if a == "--audio"), None,
    )
    for media in package_audio_alongside(paths, audio):
        ctx.record_artifact("portable_show_audio", media)
    for xsq in paths:
        target = xsq.with_suffix(".lms")
        if target.resolve() == source_lms.resolve():
            raise ValueError("Would overwrite the original LOR source LMS")
        report = export_lms_from_xsq(xsq, source_lms, target, manifest)
        # The layout snapshot is a backup of the user's real channel setup,
        # not a fabricated xLights layout that implies physical geometry.
        backup = xsq.parent / "helix_lor_source_layout.lms"
        if backup.resolve() != source_lms.resolve():
            if backup.exists() and hashlib.sha256(backup.read_bytes()).digest() != hashlib.sha256(source_lms.read_bytes()).digest():
                raise ValueError(f"Existing LOR source backup differs: {backup}")
            if not backup.exists():
                shutil.copy2(source_lms, backup)
        ctx.record_artifact("lor_source_layout", backup)
        ctx.record_artifact("lor_sequence", target)
        ctx.record_artifact("lor_lms_validation", target.with_suffix(".lms_validation.json"))
        print(
            f"lor_native: wrote {report['output_effects']} intensity/shimmer/twinkle "
            f"events to {target}; controller addresses taken from supplied LMS",
            flush=True,
        )


def _render_new_previews(
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    engine_args: list[str] | None,
    layout: Path,
    ctx: RunContext,
    *,
    lor_mode: bool = False,
    preview_seconds: float = 30.0,
) -> None:
    """Render MP4s automatically after sequencing with honest provenance.

    This uses Helix's per-model visualization (not a native xLights FSEQ nor
    LOR's actual hardware renderer). The resulting preview is useful for
    visual review and carries a machine-readable fidelity warning.
    """
    import json
    from tools.preview_renderer import parse_models, render_sequence_to_mp4

    paths = _generated_sequence_paths(roots, before, engine_args)
    if not paths:
        raise RuntimeError("Preview requested, but no new XSQ output was found")
    args = list(engine_args or [])
    audio = next(
        (Path(args[i + 1]) for i, a in enumerate(args[:-1]) if a == "--audio"),
        None,
    )
    parsed = parse_models(layout)
    for source in paths:
        preview = render_sequence_to_mp4(
            sequence_path=source,
            layout=parsed,
            audio_path=audio,
            fps=12,
            width=960,
            height=540,
            max_seconds=preview_seconds,
            use_palette_colors=not lor_mode,
        )
        label = {
            "schema": "helix.preview_provenance.v1",
            "preview": str(preview),
            "xsq": str(source),
            "source": "Helix simulated effect-level model preview",
            "max_preview_seconds": preview_seconds,
            "audio": str(audio) if audio else None,
            "native_xlights_render_verified": False,
            "native_lor_render_verified": False,
            "physical_geometry_verified": False,
            "geometry": "synthetic channel grid" if lor_mode else "approximate xLights layout",
            "note": "Actual pixel/AC controller behavior must be verified in the target sequencer.",
        }
        path = preview.with_suffix(".preview_provenance.json")
        path.write_text(json.dumps(label, indent=2) + "\n", encoding="utf-8")
        ctx.record_artifact("preview_mp4", preview)
        ctx.record_artifact("preview_provenance", path)
        print(f"preview_mp4: {preview} (simulated, not native rendering)", flush=True)


AC_ONLY_FLAG = "--helix-ac-on-only"
SHOWCASE_GATE_FLAG = "--helix-showcase-quality-gate"
SPATIAL_ACCENT_FLAG = "--helix-spatial-accent"


def _export_generated_ac_sequences(
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    layout_file: Path,
    ctx: RunContext,
) -> None:
    """Replace just-created XSQs with strictly validated AC-only XSQs.

    Raw engine sequences are retained in hidden audit storage; protected layouts,
    templates and existing user files are never changed.
    """
    import hashlib
    import os
    import shutil
    import tempfile
    from tools.ac_on_export import export_ac_on

    written = 0
    for source in _known_artifact_paths(roots):
        if source.suffix.lower() != ".xsq" or ".orchestrated." in source.name:
            continue
        if source.parent.name == ".helix_source_sequences":
            continue
        resolved = source.resolve(strict=False)
        stat = source.stat()
        if before.get(resolved) == (stat.st_mtime_ns, stat.st_size):
            continue
        with tempfile.NamedTemporaryFile(
            suffix=".xsq", prefix=".ac-on-", dir=source.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
        try:
            result = export_ac_on(source, layout_file, temporary)
            if not result["output_effects"]:
                raise RuntimeError(f"AC export was empty: {source}")
            # Temporary map/report were emitted alongside the temporary XSQ;
            # move them only when its XML validation succeeds.
            audit_dir = source.parent / ".helix_source_sequences"
            audit_dir.mkdir(exist_ok=True)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
            audit_path = audit_dir / f"{source.stem}.{digest}.raw_xsq"
            if not audit_path.exists():
                shutil.copy2(source, audit_path)
            os.replace(temporary, source)
            for suffix in (".ac_channel_map.csv", ".ac_validation.json"):
                old = temporary.with_suffix(suffix)
                new = source.with_suffix(suffix)
                os.replace(old, new)
                ctx.record_artifact("ac_export_evidence", new)
            ctx.record_artifact("ac_original_audit", audit_path)
            written += 1
            print(
                f"ac_on_only: {result['output_effects']} On effects on "
                f"{result['active_ac_channels']} single-color channels -> {source}",
                flush=True,
            )
        finally:
            temporary.unlink(missing_ok=True)
            for suffix in (".ac_channel_map.csv", ".ac_validation.json"):
                temporary.with_suffix(suffix).unlink(missing_ok=True)
    if written == 0:
        raise RuntimeError("AC-only mode produced no valid new XSQ; check the chosen layout/template")


def _add_new_spatial_accents(
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    layout: Path,
    ctx: RunContext,
) -> None:
    import json
    import os
    import tempfile
    from tools.spatial_choreography import add_spatial_accents

    for source in _known_artifact_paths(roots):
        if source.suffix != ".xsq" or ".uncolored." in source.name:
            continue
        stat = source.stat()
        if before.get(source.resolve(strict=False)) == (stat.st_mtime_ns, stat.st_size):
            continue
        with tempfile.NamedTemporaryFile(
            suffix=".xsq", prefix=".spatial-", dir=source.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
        try:
            report = add_spatial_accents(source, layout, temporary)
            if report.get("added", 0) > 0:
                os.replace(temporary, source)
                path = source.with_suffix(".spatial_accent_report.json")
                path.write_text(json.dumps(report, indent=2), encoding="utf-8")
                ctx.record_artifact("spatial_accent_report", path)
                print(f"spatial_accents: {report['added']} at {source}", flush=True)
        finally:
            temporary.unlink(missing_ok=True)


def _audit_new_showcase_sequences(
    roots: Iterable[Path],
    before: dict[Path, tuple[int, int]],
    ctx: RunContext,
    *,
    neon: bool = False,
    strict: bool = False,
) -> None:
    from tools.showcase_quality_audit import write_showcase_audit

    for source in _known_artifact_paths(roots):
        if source.suffix.lower() != ".xsq":
            continue
        if ".orchestrated." in source.name or ".uncolored." in source.name:
            continue
        resolved = source.resolve(strict=False)
        stat = source.stat()
        if before.get(resolved) == (stat.st_mtime_ns, stat.st_size):
            continue
        try:
            result = write_showcase_audit(source, neon_expected=neon, strict=strict)
        finally:
            report = source.with_suffix(".showcase_audit.json")
            if report.exists():
                ctx.record_artifact("showcase_quality_audit", report)
        print(
            f"showcase_quality: effects={result['effects']} "
            f"palette_dominance={result['dominant_palette_fraction']:.1%} "
            f"pass={result['quality_gate_pass']}",
            flush=True,
        )


def run_profile(profile_id: str | None, engine_args: list[str] | None = None) -> None:
    """Run a sequencing profile with integrated run tracking."""
    try:
        profile = engine_profiles.resolve_profile(profile_id)
    except (KeyError, ValueError) as e:
        print(f"ERROR: Invalid profile '{profile_id}': {e}", file=sys.stderr)
        raise SystemExit(1)

    raw_engine_args = list(engine_args or [])
    ac_only = AC_ONLY_FLAG in raw_engine_args
    spatial_accent = SPATIAL_ACCENT_FLAG in raw_engine_args
    strict_showcase = SHOWCASE_GATE_FLAG in raw_engine_args
    raw_engine_args = [a for a in raw_engine_args if a not in (AC_ONLY_FLAG, SPATIAL_ACCENT_FLAG, SHOWCASE_GATE_FLAG)]
    preview_requested = PREVIEW_MP4_FLAG in raw_engine_args
    raw_engine_args = [a for a in raw_engine_args if a != PREVIEW_MP4_FLAG]
    preview_seconds = 30.0
    if PREVIEW_SECONDS_FLAG in raw_engine_args:
        idx = raw_engine_args.index(PREVIEW_SECONDS_FLAG)
        if idx + 1 >= len(raw_engine_args):
            raise SystemExit("Missing --helix-preview-seconds value")
        try:
            preview_seconds = float(raw_engine_args[idx + 1])
        except ValueError as exc:
            raise SystemExit("Invalid preview duration") from exc
        if not 1.0 <= preview_seconds <= 600.0:
            raise SystemExit("Preview length must be 1 to 600 seconds")
        del raw_engine_args[idx:idx + 2]
    lor_source: Path | None = None
    workspace: Path | None = None
    if LOR_SOURCE_FLAG in raw_engine_args:
        index = raw_engine_args.index(LOR_SOURCE_FLAG)
        if index + 1 >= len(raw_engine_args):
            raise SystemExit("LOR Mode requires a source LMS path")
        lor_source = Path(raw_engine_args[index + 1]).resolve()
        del raw_engine_args[index:index + 2]
        from tools.lor_lms_import import prepare_lms_workspace
        output_root = next(
            (Path(raw_engine_args[i + 1]) for i, a in enumerate(raw_engine_args[:-1])
             if a == "--output-dir"), Path("outputs")
        )
        import tempfile
        workspace_root = output_root.resolve() / ".helix_lor_workspace"
        workspace_root.mkdir(parents=True,exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix="run-",dir=workspace_root))
        try:
            imported = prepare_lms_workspace(lor_source, workspace)
        except (OSError, ValueError, RuntimeError) as exc:
            raise SystemExit(f"LOR layout import failed: {exc}") from exc
        raw_engine_args = _set_or_replace_arg(raw_engine_args, "--template", imported["template"])
        raw_engine_args = _set_or_replace_arg(raw_engine_args, "--layout-file", imported["layout"])
        if "--ac-lights-only" not in raw_engine_args:
            raw_engine_args.append("--ac-lights-only")
    lor_compatible = "--ac-lights-only" in raw_engine_args
    if lor_compatible:
        # Avoid an RGB orchestration/template pass or RGB-only logic
        # reintroducing pixels in an explicitly legacy-AC sequence.
        if any(
            a == "--palette-mode=neon" or (
                a == "--palette-mode" and i + 1 < len(raw_engine_args)
                and raw_engine_args[i + 1] == "neon"
            ) for i, a in enumerate(raw_engine_args)
        ):
            raise SystemExit("LOR Compatible and neon RGB palette mode cannot be combined")
        for flag in (
            NO_EFFECTS_ORCHESTRATOR_FLAG, "--no-pixel-reactive",
            "--no-matrix-intelligence", "--no-birdsong",
            "--no-birdsong-auto",
        ):
            if flag not in raw_engine_args:
                raw_engine_args.append(flag)
    if ac_only:
        if lor_source is not None:
            raise SystemExit("RGW AC On-only is an xLights export option; use LOR mode directly")
        from tools.ac_on_export import inventory_layout
        layout_flag = next((raw_engine_args[i+1] for i,a in enumerate(raw_engine_args[:-1]) if a=="--layout-file"),None)
        if not layout_flag:
            raise SystemExit("AC-only mode requires a physical single-color layout")
        try:
            inventory_layout(Path(layout_flag))
        except (OSError,ValueError) as exc:
            raise SystemExit(f"AC-only preflight failed: {exc}") from exc
        if NO_EFFECTS_ORCHESTRATOR_FLAG not in raw_engine_args:
            raw_engine_args.append(NO_EFFECTS_ORCHESTRATOR_FLAG)
    if spatial_accent and (lor_compatible or ac_only):
        raise SystemExit("RGB spatial accents cannot be used in an AC/LOR output mode")
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
            if ac_only:
                _export_generated_ac_sequences(artifact_roots, artifact_snapshot, Path(layout_flag), ctx)
            elif lor_compatible:
                _validate_lor_generated_sequences(
                    engine_args, artifact_roots, artifact_snapshot, ctx
                )
            else:
                _apply_neon_palettes_to_generated_sequences(
                    engine_args, artifact_roots, artifact_snapshot, ctx
                )
            if not lor_compatible and not ac_only:
                if spatial_accent:
                    selected_layout = next((Path(engine_args[i+1]) for i,a in enumerate(engine_args[:-1]) if a=="--layout-file"),None)
                    if selected_layout is None:
                        raise RuntimeError("Spatial accents require an explicit layout")
                    _add_new_spatial_accents(artifact_roots,artifact_snapshot,selected_layout,ctx)
                neon = "--palette-mode=neon" in engine_args or any(a=="--palette-mode" and engine_args[i+1]=="neon" for i,a in enumerate(engine_args[:-1]))
                _audit_new_showcase_sequences(artifact_roots,artifact_snapshot,ctx,neon=neon,strict=strict_showcase)
            if lor_source is not None and workspace is not None:
                _publish_native_lor_lms(
                    lor_source, workspace, artifact_roots, artifact_snapshot,
                    engine_args, ctx
                )
            else:
                _package_generated_xlights_show(
                    engine_args, artifact_roots, artifact_snapshot, ctx
                )
            if preview_requested:
                args = list(engine_args or [])
                layout = next(
                    (Path(args[i + 1]) for i, a in enumerate(args[:-1])
                     if a == "--layout-file"), None
                )
                if layout is None:
                    raise RuntimeError("MP4 preview requested without a layout")
                _render_new_previews(
                    artifact_roots, artifact_snapshot, engine_args,
                    layout, ctx, lor_mode=lor_source is not None,
                    preview_seconds=preview_seconds,
                )
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
