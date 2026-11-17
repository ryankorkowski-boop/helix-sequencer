from types import SimpleNamespace

from core.orchestration_xsq_reconciliation import reconcile_orchestration_xsq


def test_sidecar_alone_is_not_final_output(tmp_path):
    sidecar = tmp_path / "song.orchestrated.xsq"
    sidecar.write_text('<xsequence><Effect source="HelixOrchestrator"/></xsequence>', encoding="utf-8")
    result = reconcile_orchestration_xsq(
        SimpleNamespace(orchestrated_xsq_path=str(sidecar)), [sidecar],
        promotion_requested=True,
    )
    assert result["sidecar_tagged_effects"] == 1
    assert result["final_candidate_paths"] == []
    assert result["tagged_provenance_in_final_candidate"] is False
    assert result["native_fseq_verified"] is False


def test_changed_non_sidecar_xsq_can_contain_orchestration_tags(tmp_path):
    sidecar = tmp_path / "song.orchestrated.xsq"
    final = tmp_path / "song.xsq"
    sidecar.write_text('<xsequence><Effect source="HelixOrchestrator"/></xsequence>', encoding="utf-8")
    final.write_text('<xsequence><Effect source="HelixOrchestrator"/><Effect name="On"/></xsequence>', encoding="utf-8")
    result = reconcile_orchestration_xsq(
        SimpleNamespace(orchestrated_xsq_path=str(sidecar)), [sidecar, final],
        promotion_requested=True,
    )
    assert result["final_candidate_paths"] == [str(final)]
    assert result["final_candidate_tagged_effects"] == 1
    assert result["tagged_provenance_in_final_candidate"] is True
    assert result["native_fseq_verified"] is False


def test_invalid_final_xsq_never_counts_as_verified(tmp_path):
    final = tmp_path / "broken.xsq"
    final.write_text('<xsequence><Effect source="HelixOrchestrator">', encoding="utf-8")
    result = reconcile_orchestration_xsq(None, [final], promotion_requested=False)
    assert result["parsed_final_candidate_count"] == 0
    assert result["final_candidate_tagged_effects"] is None
    assert result["tagged_provenance_in_final_candidate"] is False
