from types import SimpleNamespace

from core.engine_activation_audit import build_engine_activation_audit, write_engine_activation_audit


def test_disabled_android_style_run_does_not_claim_orchestrator_execution():
    audit = build_engine_activation_audit(
        ["--no-effects-orchestrator", "--no-matrix-intelligence", "--no-birdsong"],
        completed=True,
    )
    assert audit["engines"]["nine_pass_orchestrator"]["status"] == "disabled"
    assert audit["engines"]["matrix_intelligence"]["invoked"] is None
    assert audit["engines"]["birdsong"]["exported_effects_verified"] is False


def test_invoked_sidecar_not_mistaken_for_promotion_or_export():
    report = SimpleNamespace(invoked=True, xsq_written=True, error=None)
    audit = build_engine_activation_audit(["--audio", "song.wav"], report, completed=True)
    orch = audit["engines"]["nine_pass_orchestrator"]
    assert orch["invoked"] is True
    assert orch["sidecar_xsq_written"] is True
    assert orch["promoted_to_renderer"] is False
    assert orch["exported_effects_verified"] is False


def test_explicit_promotion_and_failed_orchestration():
    report = SimpleNamespace(invoked=True, xsq_written=True, error=None)
    audit = build_engine_activation_audit(["--promote-orchestrated-template"], report)
    assert audit["engines"]["nine_pass_orchestrator"]["promoted_to_renderer"]
    audit = build_engine_activation_audit(
        ["--promote-orchestrated-template", "--no-orchestrator-template-promotion"], report
    )
    assert not audit["engines"]["nine_pass_orchestrator"]["promoted_to_renderer"]
    failed = build_engine_activation_audit([], SimpleNamespace(invoked=False, error="missing audio"))
    assert failed["engines"]["nine_pass_orchestrator"]["status"] == "failed_or_unavailable"


def test_write_report(tmp_path):
    path = tmp_path / "output" / "engine_activation_audit.json"
    write_engine_activation_audit(path, build_engine_activation_audit([]))
    assert '"schema": "helix.engine_activation_audit.v1"' in path.read_text()
