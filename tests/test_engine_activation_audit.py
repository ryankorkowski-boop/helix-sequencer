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


def test_failure_audit_retains_error_without_claiming_completion():
    audit = build_engine_activation_audit(
        ["--no-effects-orchestrator"], completed=False, failed="RuntimeError: render failed"
    )
    assert audit["run_completed"] is False
    assert audit["run_error"] == "RuntimeError: render failed"
    assert audit["engines"]["nine_pass_orchestrator"]["status"] == "disabled"


def test_interrupt_audit_is_not_success():
    audit = build_engine_activation_audit([], completed=False, failed="interrupted")
    assert audit["run_completed"] is False
    assert audit["run_error"] == "interrupted"


def test_cli_audit_is_written_under_unique_run_directory(tmp_path):
    from types import SimpleNamespace
    from core.sequence_builder import _record_engine_activation_audit

    run_dir = tmp_path / "beta" / "run-001"
    run_dir.mkdir(parents=True)
    class FakeContext:
        def __init__(self):
            self.run_dir = run_dir
            self.artifacts = []
            self.warnings = []
        def record_artifact(self, kind, path):
            self.artifacts.append((kind, path))
        def record_warning(self, warning):
            self.warnings.append(warning)

    ctx = FakeContext()
    _record_engine_activation_audit(
        ctx, SimpleNamespace(output_root=tmp_path), [], None,
        completed=False, failed="render failed",
    )
    audit_path = run_dir / "engine_activation_audit.json"
    assert audit_path.is_file()
    assert not (tmp_path / "engine_activation_audit.json").exists()
    assert ctx.artifacts == [("engine_activation_audit", audit_path)]
    assert not ctx.warnings


def test_synthetic_birdsong_hook_not_mistaken_for_real_song_output():
    audit = build_engine_activation_audit(["--enable-birdsong"])
    hook = audit["engines"]["birdsong_post_run_hook"]
    assert hook["requested"] is True
    assert hook["status"] == "synthetic_diagnostic_hook_requested"
    assert hook["real_audio_analysis_verified"] is False
    assert hook["exported_effects_verified"] is False


def test_seed_only_orchestration_cannot_be_claimed_as_song_structure():
    report = SimpleNamespace(
        invoked=True, xsq_written=True, input_intents=5, final_intents=7,
        placement_count=10, effect_contract_placement_count=8,
        xsq_effect_count=6, placement_source="fallback_candidates", error=None,
    )
    orch = build_engine_activation_audit(["--audio", "song.wav"], report)["engines"]["nine_pass_orchestrator"]
    assert orch["synthetic_seed_only"] is True
    assert orch["source_sections_validated"] is False
    assert orch["placement_candidates"] == 10
    assert orch["effect_contract_placements"] == 8
    assert orch["orchestrated_sidecar_effects"] == 6
    assert orch["exported_effects_verified"] is False


def test_source_sections_are_only_validated_after_successful_invocation():
    args = ["--orchestration-sections-json", "sections.json"]
    failed = build_engine_activation_audit(args, SimpleNamespace(invoked=False))
    assert failed["engines"]["nine_pass_orchestrator"]["source_sections_validated"] is False
    success = build_engine_activation_audit(args, SimpleNamespace(invoked=True, xsq_written=False))
    orch = success["engines"]["nine_pass_orchestrator"]
    assert orch["source_sections_validated"] is True
    assert orch["synthetic_seed_only"] is False
    assert orch["orchestrated_sidecar_effects"] is None
