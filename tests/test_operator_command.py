from pathlib import Path

from core.operator_command import build_operator_command, newest_canonical_xsq, operator_run_notes
from core.run_config import RunConfig


def _command(**overrides: object) -> list[str]:
    values = dict(
        python="python",
        main_py="main.py",
        profile="master",
        template="template.xsq",
        audio="song.mp3",
        layout="layout.xml",
        output_dir="outputs",
        variants=4,
        vendor_bar=True,
        matrix=True,
        polish=True,
        shortlist=True,
        workspace_history=True,
        birdsong=False,
        birdsong_profile="canopy",
        birdsong_intensity=1.2,
        birdsong_min_confidence=0.45,
        birdsong_auto=False,
    )
    values.update(overrides)
    return build_operator_command(**values)


def test_default_gui_command_matches_engine_forced_vendor_bar() -> None:
    cmd = _command()

    assert "--vendor-bar" in cmd
    assert "--polish" in cmd
    assert "--auto-shortlist" in cmd
    assert "--workspace-history" in cmd
    assert "--matrix-intelligence" in cmd
    assert "--learn-from-my-xsqs" not in cmd
    assert "--birdsong" not in cmd


def test_matrix_off_passes_explicit_disable() -> None:
    cmd = _command(matrix=False)

    assert "--no-matrix-intelligence" in cmd
    assert "--matrix-intelligence" not in cmd


def test_vendor_bar_off_honors_polish_shortlist_and_history() -> None:
    cmd = _command(vendor_bar=False, polish=False, shortlist=False, workspace_history=False)

    assert "--vendor-bar" not in cmd
    assert "--no-polish" in cmd
    assert "--auto-shortlist" not in cmd
    assert "--no-workspace-history" in cmd


def test_vendor_bar_still_sends_forced_quality_flags_if_boxes_are_off() -> None:
    cmd = _command(vendor_bar=True, polish=False, shortlist=False, workspace_history=False)

    assert "--polish" in cmd
    assert "--auto-shortlist" in cmd
    assert "--workspace-history" in cmd
    assert "--no-polish" not in cmd


def test_run_notes_name_the_canonical_xsq() -> None:
    notes = " ".join(operator_run_notes(audio="song.mp3", vendor_bar=True))

    assert "song.orchestrated.xsq" in notes
    assert "not the audio sequence" in notes
    assert "Vendor bar forces" in notes


def test_newest_canonical_xsq_skips_orchestrated_sidecar(tmp_path: Path) -> None:
    import os

    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"")
    older = tmp_path / "song,v27.3.xsq"
    newer = tmp_path / "song,v27.3 (1).xsq"
    sidecar = tmp_path / "song.orchestrated.xsq"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")
    sidecar.write_text("side", encoding="utf-8")
    os.utime(older, (1, 1_700_000_000))
    os.utime(newer, (1, 1_700_000_100))
    os.utime(sidecar, (1, 1_700_000_200))

    assert newest_canonical_xsq(tmp_path, audio, "v27.3") == newer


def test_run_config_promotion_defaults_off_and_round_trips() -> None:
    config = RunConfig()

    assert config.promote_orchestrated_template is False
    args = config.to_engine_args()
    assert "--no-orchestrator-template-promotion" in args
    assert "--promote-orchestrated-template" not in args

    enabled = RunConfig(promote_orchestrated_template=True)
    assert "--promote-orchestrated-template" in enabled.to_engine_args()
