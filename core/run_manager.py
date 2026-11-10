from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

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

    def record_warning(self, warning: str) -> None:
        self.warnings.append(warning)
        self._write_manifest()

    def record_error(self, error: str) -> None:
        self.errors.append(error)
        self._write_manifest()

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
        if self._manager is not None:
            self._manager._write_manifest(self)


class RunManager:
    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self.context: RunContext | None = None
        self.run_id: str | None = None
        self.run_dir: Path | None = None
        self.manifest_path: Path | None = None
        self.command_path: Path | None = None
        self.log_path: Path | None = None
        self.artifacts: list[RunArtifact] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.success: bool = False
        self.error_summary: str | None = None

    def start(
        self,
        *,
        command: Sequence[str] | str | None = None,
        require_existing: bool = True,
    ) -> RunContext:
        validation_errors = self.config.validate_inputs(require_existing=require_existing)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        run_id = _build_run_id(self.config.profile)
        run_dir = _next_run_dir(self.config.output_root / "beta", run_id)
        run_dir.mkdir(parents=True, exist_ok=False)

        command_list = self._command(command)
        command_path = run_dir / "command.txt"
        command_path.write_text(_format_command(command, command_list) + "\n", encoding="utf-8")
        log_path = run_dir / "helix.log"
        log_path.write_text("", encoding="utf-8")

        ctx = RunContext(
            config=self.config,
            run_id=run_dir.name,
            run_dir=run_dir,
            manifest_path=run_dir / "run_manifest.json",
            command_path=command_path,
            log_path=log_path,
            command=command_list,
            started_at=_now_iso(),
            _manager=self,
        )
        self.context = ctx
        self._sync_from_context(ctx)
        self._write_manifest(ctx)
        return ctx

    def record_artifact(self, kind: str, path: Path | str) -> RunArtifact:
        return self._require_context().record_artifact(kind, path)

    def record_warning(self, warning: str) -> None:
        self._require_context().record_warning(warning)

    def record_error(self, error: str) -> None:
        self._require_context().record_error(error)

    def finalize(self, success: bool, error_summary: str | None = None) -> None:
        self._require_context().finalize(success=success, error_summary=error_summary)

    def _require_context(self) -> RunContext:
        if self.context is None:
            return self.start(require_existing=False)
        return self.context

    def _command(self, command: Sequence[str] | str | None) -> list[str]:
        if command is None:
            return ["main.py", *self.config.to_engine_args()]
        if isinstance(command, str):
            return [command]
        return [str(part) for part in command]

    def _sync_from_context(self, ctx: RunContext) -> None:
        self.run_id = ctx.run_id
        self.run_dir = ctx.run_dir
        self.manifest_path = ctx.manifest_path
        self.command_path = ctx.command_path
        self.log_path = ctx.log_path
        self.artifacts = ctx.artifacts
        self.warnings = ctx.warnings
        self.errors = ctx.errors
        self.success = ctx.success
        self.error_summary = ctx.error_summary

    def _write_manifest(self, ctx: RunContext) -> None:
        self._sync_from_context(ctx)
        ctx.manifest_path.write_text(json.dumps(_manifest_data(ctx), indent=2), encoding="utf-8")


def _manifest_data(ctx: RunContext) -> dict[str, object]:
    config = ctx.config
    return {
        "schema": MANIFEST_SCHEMA,
        "app": APP_NAME,
        "run_id": ctx.run_id,
        "profile": config.profile,
        "started_at": ctx.started_at,
        "finished_at": ctx.finished_at,
        "status": ctx.status,
        "audio_path": _path_value(config.audio_path),
        "template_path": _path_value(config.template_path),
        "layout_path": _path_value(config.layout_path),
        "output_root": str(config.output_root),
        "run_dir": str(ctx.run_dir),
        "command": list(ctx.command),
        "artifacts": [
            {"kind": artifact.kind, "path": artifact.path, "exists": artifact.exists}
            for artifact in ctx.artifacts
        ],
        "warnings": list(ctx.warnings),
        "errors": list(ctx.errors),
        "success": ctx.success,
        "error_summary": ctx.error_summary,
        "git_commit": _git_commit(),
    }


def _path_value(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_run_id(profile: str) -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{_slug(profile)}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-._")
    return slug or "run"


def _next_run_dir(parent: Path, run_id: str) -> Path:
    candidate = parent / run_id
    if not candidate.exists():
        return candidate
    counter = 2
    while True:
        candidate = parent / f"{run_id}-{counter}"
        if not candidate.exists():
            return candidate
        counter += 1


def _format_command(command: Sequence[str] | str | None, command_list: list[str]) -> str:
    if isinstance(command, str):
        return command
    return " ".join(command_list)


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None
