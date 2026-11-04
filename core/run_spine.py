from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _split_flag_value(arg: str) -> tuple[str, str | None]:
    if not arg.startswith("--") or "=" not in arg:
        return arg, None
    key, value = arg.split("=", 1)
    return key, value


@dataclass
class RunConfig:
    profile: str = "master"
    audio_path: Path | None = None
    template_path: Path | None = None
    layout_path: Path | None = None
    output_root: Path = field(default_factory=lambda: Path("outputs"))
    variants: int = 1
    enable_orchestrator: bool = True
    promote_orchestrated_template: bool = False
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
            raw = args[idx]
            arg, inline_value = _split_flag_value(raw)
            nxt = inline_value if inline_value is not None else (args[idx + 1] if idx + 1 < len(args) else None)
            consumed = 1 if inline_value is not None else 2
            if arg in {"--template", "--template-path", "--template_path"} and nxt is not None:
                config.template_path = Path(nxt); idx += consumed
            elif arg in {"--audio", "--audio-path", "--audio_path"} and nxt is not None:
                config.audio_path = Path(nxt); idx += consumed
            elif arg in {"--layout-file", "--layout", "--layout-path", "--layout_path"} and nxt is not None:
                config.layout_path = Path(nxt); idx += consumed
            elif arg in {"--output-dir", "--output-root", "--output_root"} and nxt is not None:
                config.output_root = Path(nxt); idx += consumed
            elif arg == "--variants" and nxt is not None:
                try: config.variants = int(nxt)
                except ValueError:
                    extra.append(raw)
                    if inline_value is None:
                        extra.append(nxt)
                idx += consumed
            elif arg == "--learning-memory":
                config.enable_learning_memory = True; idx += 1
            elif arg == "--no-learning-memory":
                config.enable_learning_memory = False; idx += 1
            elif arg == "--power-metadata-file" and nxt is not None:
                config.power_metadata_path = Path(nxt); idx += 2
            elif arg == "--autosize-controllers":
                config.autosize_controllers = True; idx += 1
            elif arg in {"--no-autosize-controllers", "--no_autosize_controllers"}:
                config.autosize_controllers = False; idx += 1
            elif arg in {"--controller-padding", "--controller_padding"} and nxt is not None:
                try: config.controller_padding = int(nxt)
                except ValueError:
                    extra.append(raw)
                    if inline_value is None:
                        extra.append(nxt)
                idx += consumed
            elif arg in {"--no-effects-orchestrator", "--disable-orchestrator"}:
                config.enable_orchestrator = False; idx += 1
            elif arg in {"--no-orchestrator-template-promotion", "--no-promote-orchestrated-template"}:
                config.promote_orchestrated_template = False; idx += 1
            elif arg == "--promote-orchestrated-template":
                config.promote_orchestrated_template = True; idx += 1
            else:
                extra.append(raw); idx += 1
        config.extra_engine_args = tuple(extra)
        return config

    def to_engine_args(self) -> list[str]:
        args: list[str] = []
        if self.template_path is not None: args.extend(["--template", str(self.template_path)])
        if self.audio_path is not None: args.extend(["--audio", str(self.audio_path)])
        if self.layout_path is not None: args.extend(["--layout-file", str(self.layout_path)])
        if self.output_root != Path("outputs"): args.extend(["--output-dir", str(self.output_root)])
        if self.variants != 1: args.extend(["--variants", str(self.variants)])
        args.append("--learning-memory" if self.enable_learning_memory else "--no-learning-memory")
        if self.power_metadata_path is not None: args.extend(["--power-metadata-file", str(self.power_metadata_path)])
        if self.autosize_controllers: args.append("--autosize-controllers")
        if self.controller_padding != 50: args.extend(["--controller-padding", str(self.controller_padding)])
        if not self.enable_orchestrator: args.append("--no-effects-orchestrator")
        if self.promote_orchestrated_template:
            args.append("--promote-orchestrated-template")
        else:
            args.append("--no-orchestrator-template-promotion")
        args.extend(self.extra_engine_args)
        return args

    def validate_inputs(self, require_existing: bool = True) -> list[str]:
        issues: list[str] = []
        sources = [
            ("audio", "audio_path", self.audio_path),
            ("template", "template_path", self.template_path),
            ("layout", "layout_path", self.layout_path),
        ]
        if require_existing:
            for label, field_name, path in sources:
                if path is None:
                    issues.append(f"{field_name} is required ({label} path is required)")
                elif not path.exists():
                    issues.append(f"{field_name} does not exist ({label} path does not exist): {path}")
            if self.power_metadata_path is not None and not self.power_metadata_path.exists():
                issues.append(f"power metadata path does not exist: {self.power_metadata_path}")
        if self.variants < 1: issues.append("variants must be at least 1")
        if self.controller_padding < 0: issues.append("controller_padding must be non-negative")
        output = self.output_root.resolve()
        for _label, field_name, path in sources:
            if path is None: continue
            resolved = path.resolve()
            if output == resolved:
                issues.append(f"output_root must not be the same path as {field_name}: {path}")
                issues.append(f"output_root would overwrite {field_name}: {path}")
            elif output == resolved.parent:
                issues.append(f"output_root would overlap {field_name}: {path}")
        return issues
