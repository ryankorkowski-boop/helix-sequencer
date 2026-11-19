from core.musical_quality_gate import evaluate_storytelling, storytelling_gate


def test_unknown_evidence_is_not_a_pass():
    passed, scores = storytelling_gate({})
    assert not passed
    assert all(value is None for value in scores.values())


def test_good_complete_evidence_passes():
    evidence = {name: .85 for name in evaluate_storytelling({})}
    assert storytelling_gate(evidence)[0]


def test_beat_accuracy_cannot_mask_repetitive_sections():
    evidence = {name: .9 for name in evaluate_storytelling({})}
    evidence["section_differentiation"] = .1
    assert not storytelling_gate(evidence)[0]


def test_invalid_values_do_not_pass():
    assert not storytelling_gate({"section_differentiation": 2.0})[0]


def test_partial_evidence_requires_explicit_opt_out():
    evidence = {"section_differentiation": .9}
    assert not storytelling_gate(evidence)[0]
    assert storytelling_gate(evidence, require_complete=False)[0]
