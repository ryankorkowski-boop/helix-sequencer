from tools.style_engine import StyleDecision
from tools.style_to_effect_mapper import map_decision_to_effects


def test_mapping_creates_effect_records():
    decision = StyleDecision(
        start=0.0,
        duration=0.5,
        intent="pulse",
        effect="beat_pulse",
        targets=("MegaTree", "Arch_01"),
        palette=("red", "green"),
        intensity=0.8,
        motion="center_out",
        style="BeatDrive",
    )

    effects = map_decision_to_effects(decision)

    assert len(effects) == 2
    assert effects[0]["model"] == "MegaTree"
    assert effects[0]["effect"] == "beat_pulse"
    assert effects[0]["intent"] == "pulse"
    assert "palette" in effects[0]
