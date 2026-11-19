from types import SimpleNamespace

from core.snowman_band import build_snowman_band_plan
from core.self_improving_scoring import score_sequence_with_storytelling_gate


def test_production_band_plan_exposes_source_gate():
    import inspect
    signature = inspect.signature(build_snowman_band_plan)
    assert signature.parameters["require_keyboard_source_ownership"].default is False
    assert signature.parameters["keyboard_ownership_threshold"].default == .7


def test_scoring_gate_fails_without_measured_storytelling():
    _, accepted, evidence = score_sequence_with_storytelling_gate({})
    assert not accepted
    assert evidence["section_differentiation"] is None


def test_scoring_gate_accepts_complete_high_quality_evidence():
    names = ("section_differentiation", "phrase_fidelity", "instrument_ownership",
             "meaningful_silence", "theme_recurrence")
    payload = {"musical_storytelling_evidence": {name: .9 for name in names}}
    _, accepted, evidence = score_sequence_with_storytelling_gate(payload)
    assert accepted
    assert evidence["theme_recurrence"] == .9
