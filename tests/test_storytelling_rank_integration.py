from core.self_improving_scoring import rank_sequence_payloads
from core.musical_quality_gate import METRIC_NAMES


def test_legacy_ranking_has_no_storytelling_fields():
    ranked = rank_sequence_payloads([{"label": "baseline", "payload": {}}])
    assert len(ranked) == 1
    assert "storytelling_accepted" not in ranked[0]


def test_strict_storytelling_ranks_evidenced_candidate_first():
    evidence = {name: 0.9 for name in METRIC_NAMES}
    ranked = rank_sequence_payloads([
        {"label": "unknown", "payload": {}},
        {"label": "measured", "payload": {"musical_storytelling_evidence": evidence}},
    ], require_storytelling=True)
    assert [item["label"] for item in ranked] == ["measured", "unknown"]
    assert ranked[0]["storytelling_accepted"] is True
    assert ranked[1]["storytelling_accepted"] is False


def test_partial_storytelling_evidence_fails_closed():
    ranked = rank_sequence_payloads([
        {"label": "partial", "payload": {"musical_storytelling_evidence": {"phrase_fidelity": 1.0}}},
    ], require_storytelling=True)
    assert ranked[0]["storytelling_accepted"] is False
    assert ranked[0]["storytelling_metrics"]["meaningful_silence"] is None


def test_nonfinite_storytelling_evidence_fails_closed():
    from core.musical_quality_gate import evaluate_storytelling
    evidence = {name: 0.9 for name in METRIC_NAMES}
    evidence["phrase_fidelity"] = float("nan")
    assert evaluate_storytelling(evidence)["phrase_fidelity"] is None
    ranked = rank_sequence_payloads([
        {"label": "invalid", "payload": {"musical_storytelling_evidence": evidence}},
    ], require_storytelling=True)
    assert ranked[0]["storytelling_accepted"] is False


def test_nonfinite_gate_threshold_rejected():
    import pytest
    from core.musical_quality_gate import storytelling_gate
    for minimum in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="minimum"):
            storytelling_gate({}, minimum=minimum)
