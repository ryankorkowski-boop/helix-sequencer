from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    profile: str = "master"
    audio_path: Path | None = None
    template_path: Path | None = None
    layout_path: Path | None = None
    output_root: Path = Path("outputs")
    variants: int = 1
    enable_orchestrator: bool = True
    promote_orchestrated_template: bool = True
    enable_learning_memory: bool = False
    power_metadata_path: Path | None = None
    autosize_controllers: bool = False
    controller_padding: int = 50
    extra_engine_args: tuple[str, ...] = ()

    @classmethod
    def from_engine_args(cls, profile: str, engine_args: list[str]) -> "RunConfig":
        audio_path: Path | None = None
        template_path: Path | None = None
        layout_path: Path | None = None
        output_root = Path("outputs")
        variants = 1
        enable_orchestrator = True
        promote_orchestrated_template = True
        enable_learning_memory = False
        power_metadata_path: Path | None = None
        autosize_controllers = False
        controller_padding = 50
        extra: list[str] = []

        args = list(engine_args)
        index = 0
        while index < len(args):
            arg = args[index]

            def value_after(flag: str) -> str | None:
                if arg.startswith(f"{flag}="):
                    return arg.split("=", 1)[1]
                if arg == flag and index + 1 < len(args):
                    return args[index + 1]
                return None

            consumed = 1
            if (value := value_after("--template")) is not None:
                template_path = Path(value)
                consumed = 1 if arg.startswith("--template=") else 2
            elif (value := value_after("--layout-file")) is not None:
                layout_path = Path(value)
                consumed = 1 if arg.startswith("--layout-file=") else 2
            elif (value := value_after("--output-dir")) is not None:
                output_root = Path(value)
                consumed = 1 if arg.startswith("--output-dir=") else 2
            elif (value := value_after("--variants")) is not None:
                try:
                    variants = int(value)
                except ValueError:
                    variants = 1
                consumed = 1 if arg.startswith("--variants=") else 2
            elif (value := value_after("--power-metadata-file")) is not None:
                power_metadata_path = Path(value)
                consumed = 1 if arg.startswith("--power-metadata-file=") else 2
            elif (value := value_after("--controller-padding")) is not None:
                try:
                    controller_padding = int(value)
                except ValueError:
                    controller_padding = -1
                consumed = 1 if arg.startswith("--controller-padding=") else 2
            elif arg == "--audio" or arg.startswith("--audio="):
                if arg.startswith("--audio="):
                    value = arg.split("=", 1)[1]
                    audio_path = Path(value) if value else None
                    consumed = 1
                else:
                    audio_values: list[str] = []
                    cursor = index + 1
                    while cursor < len(args) and not args[cursor].startswith("--"):
                        audio_values.append(args[cursor])
                        cursor += 1
                    if audio_values:
                        audio_path = Path(audio_values[0])
                    consumed = 1 + len(audio_values)
            elif arg == "--learning-memory":
                enable_learning_memory = True
            elif arg == "--no-learning-memory":
                enable_learning_memory = False
            elif arg == "--autosize-controllers":
                autosize_controllers = True
            elif arg in {"--no-effects-orchestrator", "--no-orchestrator"}:
                enable_orchestrator = False
            elif arg in {"--no-orchestrator-template-promotion", "--no-promote-orchestrated-template"}:
                promote_orchestrated_template = False
            else:
                extra.append(arg)

            index += consumed

        return cls(
            profile=profile,
            audio_path=audio_path,
            template_path=template_path,
            layout_path=layout_path,
            output_root=output_root,
            variants=variants,
            enable_orchestrator=enable_orchestrator,
            promote_orchestrated_template=promote_orchestrated_template,
            enable_learning_memory=enable_learning_memory,
            power_metadata_path=power_metadata_path,
            autosize_controllers=autosize_controllers,
            controller_padding=controller_padding,
            extra_engine_args=tuple(extra),
        )

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
        args.extend(["--variants", str(self.variants)])
        if self.power_metadata_path is not None:
            args.extend(["--power-metadata-file", str(self.power_metadata_path)])
        if self.autosize_controllers:
            args.append("--autosize-controllers")
        args.extend(["--controller-padding", str(self.controller_padding)])
        args.append("--learning-memory" if self.enable_learning_memory else "--no-learning-memory")
        if not self.enable_orchestrator:
            args.append("--no-effects-orchestrator")
        if not self.promote_orchestrated_template:
            args.append("--no-orchestrator-template-promotion")
        args.extend(self.extra_engine_args)
        return args

    def validate_inputs(self, require_existing: bool = True) -> list[str]:
        errors: list[str] = []
        output_root = _safe_resolve(self.output_root)
        if self.variants < 1:
            errors.append(f"variants must be at least 1: {self.variants}")
        if self.controller_padding < 0:
            errors.append(f"controller_padding must be non-negative: {self.controller_padding}")
        sources = (
            ("audio", self.audio_path),
            ("template", self.template_path),
            ("layout", self.layout_path),
        )

        for label, source in sources:
            if source is None:
                continue
            source_path = _safe_resolve(source)
            if require_existing and not source.exists():
                errors.append(f"{label} path does not exist: {source}")
            if output_root == source_path:
                errors.append(f"output_root must not equal {label} path: {source}")
            if output_root == source_path.parent:
                errors.append(f"output_root must not be the {label} source folder: {source_path.parent}")
            if _is_relative_to(output_root, source_path):
                errors.append(f"output_root must not be inside the {label} file path: {source}")

        return errors


def _safe_resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
