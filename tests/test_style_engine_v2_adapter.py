from core.choreography_intent import (
    ContrastStrategy,
    DominanceStrategy,
    MotionVocabulary,
    PaletteFamily,
)
from core.style_engine_v2_adapter import StyleDecisionAdapter



def test_spatial_helix_mapping():
    decision = {
        "start": 12.0,
        "duration": 4.0,
        "section": "chorus",
        "event_type": "drop",
        "style": "SpatialHelix",
        "effect": "helix_spiral_sweep",
        "targets": "megatree",
        "dominant_prop": "mega_tree",
    }

    intent = StyleDecisionAdapter.to_choreography_intent(decision)

    assert intent.style == "SpatialHelix"
    assert intent.palette_family == PaletteFamily.SPATIAL_HELIX
    assert intent.dominance_strategy == DominanceStrategy.ORBITAL
    assert intent.contrast_strategy == ContrastStrategy.DARK_PRE_DROP
    assert MotionVocabulary.HELIX_SPIRAL in intent.motion_vocabulary
    assert MotionVocabulary.ORBITAL in intent.motion_vocabulary



def test_cinematic_sweep_mapping():
    decision = {
        "start": 5.0,
        "duration": 3.0,
        "section": "bridge",
        "event_type": "build",
        "style": "CinematicSweep",
        "effect": "trailer_hit_burst",
    }

    intent = StyleDecisionAdapter.to_choreography_intent(decision)

    assert intent.palette_family == PaletteFamily.CINEMATIC_BLUE_GOLD
    assert intent.contrast_strategy == ContrastStrategy.DARK_PRE_DROP
    assert MotionVocabulary.IMPACT in intent.motion_vocabulary
    assert MotionVocabulary.BLOOM in intent.motion_vocabulary
    assert intent.escalation_phase == 2



def test_classic_christmas_mapping():
    decision = {
        "start": 0.0,
        "duration": 6.0,
        "section": "verse",
        "event_type": "texture",
        "style": "ClassicChristmas",
        "effect": "gold_white_sparkle",
    }

    intent = StyleDecisionAdapter.to_choreography_intent(decision)

    assert intent.palette_family == PaletteFamily.CLASSIC_CHRISTMAS
    assert intent.motion_vocabulary == (MotionVocabulary.SHIMMER,)



def test_unknown_effect_falls_back_to_texture_motion():
    decision = {
        "start": 1.0,
        "duration": 1.0,
        "section": "intro",
        "event_type": "texture",
        "style": "PartyMode",
        "effect": "totally_unknown_effect",
    }

    intent = StyleDecisionAdapter.to_choreography_intent(decision)

    assert intent.motion_vocabulary == (MotionVocabulary.TEXTURE,)



def test_adapter_produces_valid_intent():
    decision = {
        "start": 20.0,
        "duration": 8.0,
        "section": "chorus",
        "event_type": "hit",
        "style": "BeatDrive",
        "effect": "party_strobe_burst",
        "targets": "whole_house",
    }

    intent = StyleDecisionAdapter.to_choreography_intent(decision)

    result = intent.validate()

    assert result.valid is True
