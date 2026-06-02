from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.run_config import RunConfig
from core.run_manager import MANIFEST_SCHEMA, RunManager


def test_run_config_from_engine_args_parses_core_flags(tmp_path: Path) -> None:
    template = tmp_path / "template.xsq"
    audio = tmp_path / "song.wav"
    layout = tmp_path / "xlights_rgbeffects.xml"
    output = tmp_path / "out"
    power = tmp_path / "power.json"
    args = [
        "--template",
        str(template),
        "--audio",
        str(audio),
        "--layout-file",
        str(layout),
        "--output-dir",
        str(output),
        "--variants",
        "4",
        "--learning-memory",
        "--power-metadata-file",
        str(power),
        "--autosize-controllers",
        "--controller-padding",
        "75",
        "--no-effects-orchestrator",
        "--no-orchestrator-template-promotion",
        "--no-prompt",
    ]

    config = RunConfig.from_engine_args("master", args)

    assert config.profile == "master"
    assert config.template_path == template
    assert config.audio_path == audio
    assert config.layout_path == layout
    assert config.output_root == output
    assert config.variants == 4
    assert config.enable_learning_memory is True
    assert config.power_metadata_path == power
    assert config.autosize_controllers is True
    assert config.controller_padding == 75
    assert config.enable_orchestrator is False
    assert config.promote_orchestrated_template is False
    assert config.extra_engine_args == ("--no-prompt",)


def test_run_config_from_engine_args_parses_no_learning_memory(tmp_path: Path) -> None:
    config = RunConfig.from_engine_args(
        "master",
        ["--template", str(tmp_path / "template.xsq"), "--no-learning-memory"],
    )

    assert config.enable_learning_memory is False


def test_run_config_to_engine_args_round_trips_core_paths(tmp_path: Path) -> None:
    config = RunConfig(
        profile="master",
        audio_path=tmp_path / "song.wav",
        template_path=tmp_path / "template.xsq",
        layout_path=tmp_path / "layout.xml",
        output_root=tmp_path / "outputs",
        variants=2,
        enable_learning_memory=True,
        power_metadata_path=tmp_path / "power.json",
        autosize_controllers=True,
        controller_padding=80,
        extra_engine_args=("--no-prompt",),
    )

    args = config.to_engine_args()

    assert args[args.index("--template") + 1] == str(config.template_path)
    assert args[args.index("--audio") + 1] == str(config.audio_path)
    assert args[args.index("--layout-file") + 1] == str(config.layout_path)
    assert args[args.index("--output-dir") + 1] == str(config.output_root)
    assert args[args.index("--variants") + 1] == "2"
    assert args[args.index("--power-metadata-file") + 1] == str(config.power_metadata_path)
    assert "--autosize-controllers" in args
    assert args[args.index("--controller-padding") + 1] == "80"
    assert "--learning-memory" in args
    assert "--no-prompt" in args


def test_run_config_validate_inputs_catches_missing_sources(tmp_path: Path) -> None:
    config = RunConfig(
        audio_path=tmp_path / "missing.wav",
        template_path=tmp_path / "missing.xsq",
        layout_path=tmp_path / "missing.xml",
        output_root=tmp_path / "outputs",
    )

    errors = config.validate_inputs()

    assert any("audio path does not exist" in error for error in errors)
    assert any("template path does not exist" in error for error in errors)
    assert any("layout path does not exist" in error for error in errors)


def test_run_config_validate_inputs_catches_invalid_variants_and_padding(tmp_path: Path) -> None:
    config = RunConfig(output_root=tmp_path / "outputs", variants=0, controller_padding=-1)

    errors = config.validate_inputs()

    assert any("variants must be at least 1" in error for error in errors)
    assert any("controller_padding must be non-negative" in error for error in errors)


@pytest.mark.parametrize("source_name", ["song.wav", "template.xsq", "layout.xml"])
def test_run_config_validate_inputs_catches_dangerous_output_roots(tmp_path: Path, source_name: str) -> None:
    source = tmp_path / source_name
    source.write_text("source", encoding="utf-8")
    kwargs = {
        "audio_path": tmp_path / "safe.wav",
        "template_path": tmp_path / "safe.xsq",
        "layout_path": tmp_path / "safe.xml",
    }
    for path in kwargs.values():
        path.write_text("safe", encoding="utf-8")
    if source_name.endswith(".wav"):
        kwargs["audio_path"] = source
    elif source_name.endswith(".xsq"):
        kwargs["template_path"] = source
    else:
        kwargs["layout_path"] = source

    file_config = RunConfig(output_root=source, **kwargs)
    parent_config = RunConfig(output_root=source.parent, **kwargs)

    assert file_config.validate_inputs()
    assert parent_config.validate_inputs()


def test_run_manager_creates_run_files_and_started_manifest(tmp_path: Path) -> None:
    template = tmp_path / "template.xsq"
    audio = tmp_path / "song.wav"
    layout = tmp_path / "layout.xml"
    for path in (template, audio, layout):
        path.write_text("source", encoding="utf-8")
    config = RunConfig(
        profile="master",
        audio_path=audio,
        template_path=template,
        layout_path=layout,
        output_root=tmp_path / "outputs",
    )

    ctx = RunManager(config).start(command=["python", "main.py"])
    manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))

    assert ctx.run_dir.exists()
    assert ctx.command_path.exists()
    assert ctx.manifest_path.exists()
    assert ctx.log_path.exists()
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["profile"] == "master"
    assert manifest["status"] == "started"
    assert manifest["started_at"]
    assert manifest["finished_at"] is None
    assert manifest["audio_path"] == str(audio)
    assert manifest["template_path"] == str(template)
    assert manifest["layout_path"] == str(layout)
    assert manifest["output_root"] == str(config.output_root)
    assert manifest["run_dir"] == str(ctx.run_dir)
    assert manifest["inputs"]["audio"] == str(audio)
    assert manifest["inputs"]["template"] == str(template)
    assert manifest["inputs"]["layout"] == str(layout)
    assert manifest["outputs"]["output_root"] == str(config.output_root)
    assert manifest["outputs"]["run_dir"] == str(ctx.run_dir)


def test_run_manager_records_artifacts_and_success(tmp_path: Path) -> None:
    config = RunConfig(output_root=tmp_path / "outputs")

    with RunManager(config).start(command="python main.py") as ctx:
        artifact = ctx.run_dir / "sequence.xsq"
        artifact.write_text("<xsequence />", encoding="utf-8")
        ctx.record_artifact("xsq", artifact)
        ctx.finalize(success=True)

    manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "success"
    assert manifest["success"] is True
    assert manifest["artifacts"] == [{"kind": "xsq", "path": str(artifact), "exists": True}]


def test_run_manager_finalizes_failure_with_error_summary(tmp_path: Path) -> None:
    config = RunConfig(output_root=tmp_path / "outputs")
    ctx = RunManager(config).start(command=["python", "main.py"])

    ctx.finalize(success=False, error_summary="engine failed")

    manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["success"] is False
    assert manifest["error_summary"] == "engine failed"
    assert "engine failed" in manifest["errors"]


def test_run_manager_does_not_overwrite_source_files(tmp_path: Path) -> None:
    template = tmp_path / "template.xsq"
    audio = tmp_path / "song.wav"
    layout = tmp_path / "layout.xml"
    originals = {
        template: "template source",
        audio: "audio source",
        layout: "layout source",
    }
    for path, content in originals.items():
        path.write_text(content, encoding="utf-8")
    config = RunConfig(
        audio_path=audio,
        template_path=template,
        layout_path=layout,
        output_root=tmp_path / "outputs",
    )

    with RunManager(config).start(command=["python", "main.py"]) as ctx:
        ctx.finalize(success=True)

    for path, content in originals.items():
        assert path.read_text(encoding="utf-8") == content
