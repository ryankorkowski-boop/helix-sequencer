from core.source_ownership import SourceOwnership, resolve_owner
import pytest


def test_detected_preferred_over_estimated():
    actual = SourceOwnership("guitarist", .9, "detected", "stem:guitar")
    guess = SourceOwnership("keyboardist", .95, "estimated")
    assert resolve_owner(actual, guess) == actual


def test_unknown_pitch_does_not_animate_keyboard():
    assert resolve_owner(None).performer is None


def test_low_confidence_suppressed():
    assert not resolve_owner(SourceOwnership("keyboardist", .3, "detected")).permitted()


def test_valid_estimate_can_route():
    assert resolve_owner(None, SourceOwnership("bassist", .8, "estimated")).performer == "bassist"


def test_fallback_cannot_claim_identity():
    with pytest.raises(ValueError):
        SourceOwnership("keyboardist", .8, "fallback")


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        SourceOwnership("guitarist", 1.1, "detected")


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), float("-inf"), -0.01, 1.01])
def test_resolver_rejects_invalid_thresholds(threshold):
    detected = SourceOwnership("keyboardist", 0.9, "detected")
    with pytest.raises(ValueError, match="threshold"):
        resolve_owner(detected, threshold=threshold)


def test_resolver_preserves_valid_threshold_boundaries():
    detected = SourceOwnership("keyboardist", 0.9, "detected")
    assert resolve_owner(detected, threshold=0.0) == detected
    assert resolve_owner(detected, threshold=1.0).performer is None
