from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunConfig:
    profile: str = "master"
    audio_path: Path | None = None
    template_path: Path | None = None
    layout_path: Path | None = None
    output_root: Path = field(default_factory=lambda: Path("outputs"))
    variants: int = 1
    enable_orchestrator: bool = True
    promote_orchestrated_template: bool = True
    enable_learning_memory: bool = False
    power_metadata_path: Path | None = None
    autosize_controllers: bool = False
    controller_padding: int = 50
    extra_engine_args: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_engine_args(cls, profile: str, engine_args: list[str]) -> "RunConfig":
        config = cls(profile=profile or "master")
        extra: list[str] = []
        args = list(engine_args or [])
        idx = 0
        while idx < len(args):
            arg = args[idx]
            nxt = args[idx + 1] if idx + 1 < len(args) else None
            if arg == "--template" and nxt is not None:
                config.template_path = Path(nxt)
                idx += 2
            elif arg == "--audio" and nxt is not None:
                config.audio_path = Path(nxt)
                idx += 2
            elif arg == "--layout-file" and nxt is not None:
                config.layout_path = Path(nxt)
                idx += 2
            elif arg == "--output-dir" and nxt is not None:
                config.output_root = Path(nxt)
                idx += 2
            elif arg == "--variants" and nxt is not None:
                try:
                    config.variants = int(nxt)
                except ValueError:
                    extra.extend([arg, nxt])
                idx += 2
            elif arg == "--learning-memory":
                config.enable_learning_memory = True
                idx += 1
            elif arg == "--no-learning-memory":
                config.enable_learning_memory = False
                idx += 1
            elif arg == "--power-metadata-file" and nxt is not None:
                config.power_metadata_path = Path(nxt)
                idx += 2
            elif arg == "--autosize-controllers":
                config.autosize_controllers = True
                idx += 1
            elif arg == "--controller-padding" and nxt is not None:
                try:
                    config.controller_padding = int(nxt)
                except ValueError:
                    extra.extend([arg, nxt])
                idx += 2
            elif arg == "--no-effects-orchestrator":
                config.enable_orchestrator = False
                idx += 1
            elif arg == "--no-orchestrator-template-promotion":
                config.promote_orchestrated_template = False
                idx += 1
            elif arg == "--promote-orchestrated-template":
                config.promote_orchestrated_template = True
                idx += 1
            else:
                extra.append(arg)
                idx += 1
        config.extra_engine_args = tuple(extra)
        return config

    def to_engine_args(self) -> list[str]:
        args: list[str] = []
        if self.template_path is not None:
            args.extend(["--template", str(self.template_path)])
        if self.audio_path is not None:
            args.extend(["--audio", str(self.audio_path)])
        if self.layout_path is not None:
            args.extend(["--layout-file", str(self.layout_path)])
        if self.output_root != Path("outputs"):
            args.extend(["--output-dir", str(self.output_root)])
        if self.variants != 1:
            args.extend(["--variants", str(self.variants)])
        args.append("--learning-memory" if self.enable_learning_memory else "--no-learning-memory")
        if self.power_metadata_path is not None:
            args.extend(["--power-metadata-file", str(self.power_metadata_path)])
        if self.autosize_controllers:
            args.append("--autosize-controllers")
        if self.controller_padding != 50:
            args.extend(["--controller-padding", str(self.controller_padding)])
        if not self.enable_orchestrator:
            args.append("--no-effects-orchestrator")
        if not self.promote_orchestrated_template:
            args.append("--no-orchestrator-template-promotion")
        args.extend(self.extra_engine_args)
        return args

    def validate_inputs(self, require_existing: bool = True) -> list[str]:
        issues: list[str] = []
        if require_existing:
            required = [("audio", self.audio_path), ("template", self.template_path), ("layout", self.layout_path)]
            for label, path in required:
                if path is None:
                    issues.append(f"missing {label} path")
                elif not path.exists():
                    issues.append(f"{label} path not found: {path}")
        if self.variants < 1:
            issues.append("variants must be positive")
        if self.controller_padding < 0:
            issues.append("controller padding must not be negative")
        output = self.output_root.resolve()
        for label, path in [("audio", self.audio_path), ("template", self.template_path), ("layout", self.layout_path)]:
            if path is not None and output == path.resolve():
                issues.append(f"output path matches {label} source: {path}")
        return issues
