from tools.style_engine import StyleDecision
from xlights.style_xsq_bridge import decisions_to_xsq_effect_rows, validate_xsq_effect_rows


def test_bridge_converts_decisions_to_rows():
    decision = StyleDecision(
        start=0.0,
        duration=1.0,
        intent="pulse",
        effect="beat_pulse",
        targets=("MegaTree",),
        palette=("red", "green"),
        intensity=0.8,
        motion="center_out",
        style="BeatDrive",
    )

    rows = decisions_to_xsq_effect_rows([decision])

    assert len(rows) == 1
    assert rows[0]["model"] == "MegaTree"
    assert rows[0]["effect"] == "beat_pulse"


def test_bridge_validation_passes_valid_rows():
    rows = [
        {
            "model": "MegaTree",
            "start": 0.0,
            "duration": 1.0,
            "effect": "beat_pulse",
            "palette": ["red", "green"],
            "intensity": 0.8,
            "motion": "center_out",
            "intent": "pulse",
        }
    ]

    validate_xsq_effect_rows(rows)


def test_bridge_validation_rejects_invalid_rows():
    invalid = [
        {
            "model": "",
            "start": -1.0,
            "duration": 0,
            "effect": "",
        }
    ]

    try:
        validate_xsq_effect_rows(invalid)
        assert False, "Expected validation failure"
    except ValueError:
        pass
