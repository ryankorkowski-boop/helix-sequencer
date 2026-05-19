from __future__ import annotations

from core.birdsong_v2_gate import (
    BirdsongV2GateConfig,
    describe_birdsong_v2_gate,
    should_enable_birdsong_v2,
)


def test_birdsong_v2_gate_defaults_off() -> None:
    config = BirdsongV2GateConfig()

    assert should_enable_birdsong_v2(config) is False
    assert describe_birdsong_v2_gate(config) == "disabled"


def test_birdsong_v2_gate_explicit_enable_wins() -> None:
    config = BirdsongV2GateConfig(
        enabled=True,
        auto=False,
        confidence=0.0,
        min_confidence=1.0,
    )

    assert should_enable_birdsong_v2(config) is True
    assert describe_birdsong_v2_gate(config) == "explicit"


def test_birdsong_v2_gate_auto_requires_threshold() -> None:
    below = BirdsongV2GateConfig(auto=True, confidence=0.44, min_confidence=0.45)
    at_threshold = BirdsongV2GateConfig(auto=True, confidence=0.45, min_confidence=0.45)
    above = BirdsongV2GateConfig(auto=True, confidence=0.90, min_confidence=0.45)

    assert should_enable_birdsong_v2(below) is False
    assert should_enable_birdsong_v2(at_threshold) is True
    assert should_enable_birdsong_v2(above) is True
    assert describe_birdsong_v2_gate(below) == "auto_below_threshold"
    assert describe_birdsong_v2_gate(at_threshold) == "auto_confident"


def test_birdsong_v2_gate_rejects_non_finite_confidence() -> None:
    config = BirdsongV2GateConfig(auto=True, confidence=float("nan"), min_confidence=0.45)

    assert should_enable_birdsong_v2(config) is False
    assert describe_birdsong_v2_gate(config) == "auto_below_threshold"


def test_birdsong_v2_gate_does_not_accept_legacy_birdsong_flags_by_name() -> None:
    field_names = set(BirdsongV2GateConfig.__dataclass_fields__)

    assert "birdsong_enabled" not in field_names
    assert "birdsong_auto" not in field_names
    assert field_names == {"enabled", "auto", "confidence", "min_confidence"}
