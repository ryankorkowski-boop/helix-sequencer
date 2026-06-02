from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from core import engine_profiles
from core.run_config import RunConfig


MANIFEST_SCHEMA = "helix.run_manifest.v1"
APP_NAME = "Helix Sequencer"


@dataclass(frozen=True)
class RunArtifact:
    kind: str
    path: str
    exists: bool


@dataclass
class RunContext:
    config: RunConfig
    run_id: str
    run_dir: Path
    manifest_path: Path
    command_path: Path
    log_path: Path
    artifacts: list[RunArtifact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str | None = None
    status: str = "started"
    success: bool = False
    error_summary: str | None = None
    _manager: "RunManager | None" = field(default=None, repr=False, compare=False)
    _finalized: bool = field(default=False, repr=False, compare=False)

    def __enter__(self) -> "RunContext":
        return self

    def __exit__(self, exc_type: object, exc: BaseException | None, traceback: object) -> None:
        if self._finalized:
            return
        if exc is None:
            self.finalize(success=True)
        else:
            self.finalize(success=False, error_summary=str(exc))

    def record_artifact(self, kind: str, path: str | Path) -> RunArtifact:
        artifact_path = Path(path)
        artifact = RunArtifact(kind=kind, path=str(artifact_path), exists=artifact_path.exists())
        self.artifacts.append(artifact)
        self._write_manifest()
        return artifact

    def finalize(self, *, success: bool, error_summary: str | None = None) -> None:
        self.finished_at = _now_iso()
        self.success = success
        self.status = "success" if success else "failed"
        self.error_summary = error_summary
        if error_summary:
            self.errors.append(error_summary)
        self._finalized = True
        self._write_manifest()

    def _write_manifest(self) -> None:
        if self._manager is None:
            return
        self._manager._write_manifest(self)


class RunManager:
    def __init__(self, config: RunConfig) -> None:
        self.config = config

    def start(
        self,
        *,
        command: Sequence[str] | str,
        require_existing: bool = True,
    ) -> RunContext:
        warnings = self.config.validate_inputs(require_existing=require_existing)
        if warnings:
            raise ValueError("; ".join(warnings))

        output_root = self.config.output_root
        run_id = _build_run_id(self.config.profile)
        run_dir = _next_run_dir(output_root / "beta", run_id)
        run_dir.mkdir(parents=True, exist_ok=False)

        command_list = [command] if isinstance(command, str) else [str(part) for part in command]
        command_path = run_dir / "command.txt"
        command_path.write_text(" ".join(command_list) + "\n", encoding="utf-8")
        log_path = run_dir / "helix.log"
        log_path.write_text("", encoding="utf-8")

        ctx = RunContext(
            config=self.config,
            run_id=run_dir.name,
            run_dir=run_dir,
            manifest_path=run_dir / "run_manifest.json",
            command_path=command_path,
            log_path=log_path,
            warnings=warnings,
            command=command_list,
            started_at=_now_iso(),
            _manager=self,
        )
        self._write_manifest(ctx)
        return ctx

    def _write_manifest(self, ctx: RunContext) -> None:
        ctx.manifest_path.write_text(
            json.dumps(_manifest_payload(ctx), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _manifest_payload(ctx: RunContext) -> dict[str, object]:
    profile = _profile_metadata(ctx.config.profile)
    return {
        "schema": MANIFEST_SCHEMA,
        "app": APP_NAME,
        "run_id": ctx.run_id,
        "profile": ctx.config.profile,
        "engine_profile": profile.get("profile_id"),
        "engine_version": profile.get("version"),
        "started_at": ctx.started_at,
        "finished_at": ctx.finished_at,
        "timestamps": {
            "started_at": ctx.started_at,
            "finished_at": ctx.finished_at,
        },
        "status": ctx.status,
        "audio_path": _path_or_none(ctx.config.audio_path),
        "template_path": _path_or_none(ctx.config.template_path),
        "layout_path": _path_or_none(ctx.config.layout_path),
        "power_metadata_path": _path_or_none(ctx.config.power_metadata_path),
        "inputs": {
            "audio": _path_or_none(ctx.config.audio_path),
            "template": _path_or_none(ctx.config.template_path),
            "layout": _path_or_none(ctx.config.layout_path),
            "power_metadata": _path_or_none(ctx.config.power_metadata_path),
        },
        "outputs": {
            "output_root": str(ctx.config.output_root),
            "run_dir": str(ctx.run_dir),
            "manifest": str(ctx.manifest_path),
            "command": str(ctx.command_path),
            "log": str(ctx.log_path),
        },
        "output_root": str(ctx.config.output_root),
        "run_dir": str(ctx.run_dir),
        "command": ctx.command,
        "artifacts": [artifact.__dict__ for artifact in ctx.artifacts],
        "warnings": ctx.warnings,
        "errors": ctx.errors,
        "success": ctx.success,
        "error_summary": ctx.error_summary,
        "git_commit": _git_commit(),
    }


def _profile_metadata(profile_id: str) -> dict[str, str | None]:
    try:
        profile = engine_profiles.resolve_profile(profile_id)
    except Exception:
        return {"profile_id": profile_id, "version": None}
    return {
        "profile_id": getattr(profile, "profile_id", profile_id),
        "version": getattr(profile, "version", None),
    }


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _build_run_id(profile: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_profile = re.sub(r"[^A-Za-z0-9_.-]+", "-", profile).strip("-") or "run"
    return f"{stamp}-{safe_profile}"


def _next_run_dir(parent: Path, run_id: str) -> Path:
    candidate = parent / run_id
    counter = 2
    while candidate.exists():
        candidate = parent / f"{run_id}-{counter}"
        counter += 1
    return candidate


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return None
    commit = result.stdout.strip()
    if result.returncode != 0:
        return None
    return commit or None
