"""Regression guard: the orchestration sidecar must not silently replace production XSQs.

The present graph uses five synthetic seed sections, so promotion remains opt-in
until a separately validated, song-derived choreography source is available.
"""
from pathlib import Path
from types import SimpleNamespace

from core.run_config import RunConfig
from core.sequence_builder import (
    _orchestrator_template_promotion_enabled,
    _promote_orchestrated_template,
)


def _successful_report():
    return SimpleNamespace(
        invoked=True,
        xsq_written=True,
        orchestrated_xsq_path="output/song.orchestrated.xsq",
    )


def test_default_config_does_not_promote_fixed_seed_orchestration():
    config = RunConfig()
    assert config.enable_orchestrator is True
    assert config.promote_orchestrated_template is False
    args = config.to_engine_args()
    assert "--no-orchestrator-template-promotion" in args
    assert "--promote-orchestrated-template" not in args
    assert _orchestrator_template_promotion_enabled(args) is False


def test_explicit_opt_in_round_trips_into_builder_flag():
    config = RunConfig(promote_orchestrated_template=True)
    args = config.to_engine_args()
    assert "--promote-orchestrated-template" in args
    assert "--no-orchestrator-template-promotion" not in args
    assert _orchestrator_template_promotion_enabled(args) is True
    parsed = RunConfig.from_engine_args("master", args)
    assert parsed.promote_orchestrated_template is True
    assert "--promote-orchestrated-template" in parsed.to_engine_args()


def test_parsed_unflagged_cli_defaults_to_sidecar_only():
    config = RunConfig.from_engine_args("master", ["--audio", "song.wav", "--template", "original.xsq"])
    assert config.promote_orchestrated_template is False
    assert _promote_orchestrated_template(config.to_engine_args(), _successful_report()) == config.to_engine_args()


def test_explicit_promotion_replaces_template_and_removes_internal_flag():
    args = ["--audio", "song.wav", "--template", "original.xsq", "--promote-orchestrated-template"]
    effective = _promote_orchestrated_template(args, _successful_report())
    assert effective == ["--audio", "song.wav", "--template", Path("output/song.orchestrated.xsq").as_posix()]


def test_explicit_promotion_does_not_promote_unwritten_xsq():
    args = ["--template", "original.xsq", "--promote-orchestrated-template"]
    unrendered = SimpleNamespace(invoked=True, xsq_written=False, orchestrated_xsq_path=None)
    assert _promote_orchestrated_template(args, unrendered) == ["--template", "original.xsq"]


def test_disable_orchestrator_takes_precedence_over_promotion():
    args = [
        "--template", "original.xsq",
        "--promote-orchestrated-template",
        "--no-effects-orchestrator",
    ]
    assert _orchestrator_template_promotion_enabled(args) is False
    assert _promote_orchestrated_template(args, _successful_report()) == ["--template", "original.xsq"]
