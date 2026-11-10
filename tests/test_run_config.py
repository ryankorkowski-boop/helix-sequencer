from pathlib import Path

from core.run_config import RunConfig


def test_run_config_accepts_canonical_issue_79_flags(tmp_path):
    audio = tmp_path / "song.wav"
    template = tmp_path / "template.xsq"
    layout = tmp_path / "xlights_rgbeffects.xml"
    power = tmp_path / "power.json"
    for path in (audio, template, layout, power):
        path.write_text("ok", encoding="utf-8")

    config = RunConfig.from_engine_args(
        "master",
        [
            "--audio",
            str(audio),
            "--template",
            str(template),
            "--layout-file",
            str(layout),
            "--output-dir",
            str(tmp_path / "runs"),
            "--variants",
            "3",
            "--no-effects-orchestrator",
            "--no-orchestrator-template-promotion",
            "--learning-memory",
            "--power-metadata-file",
            str(power),
            "--autosize-controllers",
            "--controller-padding",
            "64",
            "--future-flag",
        ],
    )

    assert config.profile == "master"
    assert config.audio_path == audio
    assert config.template_path == template
    assert config.layout_path == layout
    assert config.output_root == tmp_path / "runs"
    assert config.variants == 3
    assert config.enable_orchestrator is False
    assert config.promote_orchestrated_template is False
    assert config.enable_learning_memory is True
    assert config.power_metadata_path == power
    assert config.autosize_controllers is True
    assert config.controller_padding == 64
    assert config.extra_engine_args == ("--future-flag",)
    assert config.validate_inputs() == []


def test_run_config_preserves_legacy_underscore_flags_and_round_trips():
    config = RunConfig.from_engine_args(
        "preview",
        [
            "--audio_path",
            "song.wav",
            "--template_path",
            "template.xsq",
            "--layout_path",
            "layout.xml",
            "--output_root",
            "out",
            "--controller_padding",
            "75",
            "--no_autosize_controllers",
        ],
    )

    args = config.to_engine_args()

    assert config.audio_path == Path("song.wav")
    assert config.template_path == Path("template.xsq")
    assert config.layout_path == Path("layout.xml")
    assert "--audio" in args
    assert "--template" in args
    assert "--layout-file" in args
    assert "--output-dir" in args
    assert "--controller-padding" in args
    assert "--autosize-controllers" not in args


def test_run_config_validation_reports_missing_inputs_and_bad_values(tmp_path):
    config = RunConfig(
        audio_path=tmp_path / "missing.wav",
        template_path=tmp_path / "missing.xsq",
        variants=0,
        controller_padding=-1,
    )

    errors = config.validate_inputs()

    assert "variants must be at least 1" in errors
    assert "controller_padding must be non-negative" in errors
    assert any("audio_path does not exist" in error for error in errors)
    assert any("template_path does not exist" in error for error in errors)
    assert any("layout_path is required" in error for error in errors)
    assert config.validate_inputs(require_existing=False) == [
        "variants must be at least 1",
        "controller_padding must be non-negative",
    ]


def test_run_config_validation_reports_dangerous_output_overlap(tmp_path):
    audio = tmp_path / "song.wav"
    template = tmp_path / "template.xsq"
    layout = tmp_path / "xlights_rgbeffects.xml"
    for path in (audio, template, layout):
        path.write_text("ok", encoding="utf-8")

    config = RunConfig(
        audio_path=audio,
        template_path=template,
        layout_path=layout,
        output_root=template,
    )

    errors = config.validate_inputs()

    assert any("output_root must not be the same path as template_path" in error for error in errors)
    assert any("output_root would overwrite template_path" in error for error in errors)
