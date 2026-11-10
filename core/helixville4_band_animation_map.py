from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TriggerFamily = Literal["drums", "bass", "guitar", "lead_vocal", "harmony_vocal", "ensemble"]


@dataclass(frozen=True)
class AnimationTarget:
    state: str
    family: TriggerFamily
    primary_submodels: tuple[str, ...]
    support_submodels: tuple[str, ...] = ()
    intensity_source: str = "velocity"
    timing_source: str = "beat"
    sustain_behavior: str = "none"


HELIXVILLE4_BAND_ANIMATION_MAP: dict[str, tuple[AnimationTarget, ...]] = {
    "HX_SNOWMAN_DRUMMER": (
        AnimationTarget(
            state="kick_hit",
            family="drums",
            primary_submodels=("HX_SNOWMAN_DRUMMER_KICK", "HX_SNOWMAN_DRUMMER_KICK_RIM"),
            support_submodels=("HX_SNOWMAN_DRUMMER_PLATFORM",),
            timing_source="kick",
            sustain_behavior="short_impact_decay",
        ),
        AnimationTarget(
            state="snare_hit",
            family="drums",
            primary_submodels=("HX_SNOWMAN_DRUMMER_SNARE", "HX_SNOWMAN_DRUMMER_SNARE_RIM"),
            support_submodels=("HX_SNOWMAN_DRUMMER_LEFT_STICK", "HX_SNOWMAN_DRUMMER_RIGHT_STICK"),
            timing_source="snare",
            sustain_behavior="short_snap_decay",
        ),
        AnimationTarget(
            state="tom_fill",
            family="drums",
            primary_submodels=("HX_SNOWMAN_DRUMMER_TOM_LEFT", "HX_SNOWMAN_DRUMMER_TOM_RIGHT"),
            support_submodels=("HX_SNOWMAN_DRUMMER_LEFT_ARM", "HX_SNOWMAN_DRUMMER_RIGHT_ARM"),
            timing_source="fills",
            sustain_behavior="rolling_chase",
        ),
        AnimationTarget(
            state="cymbal_crash",
            family="drums",
            primary_submodels=("HX_SNOWMAN_DRUMMER_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT"),
            support_submodels=("HX_SNOWMAN_DRUMMER_STANDS",),
            timing_source="cymbal_crash",
            sustain_behavior="long_shimmer_decay",
        ),
    ),
    "HX_SNOWMAN_BASSIST": (
        AnimationTarget(
            state="pluck_e",
            family="bass",
            primary_submodels=("HX_SNOWMAN_BASSIST_STRING_E",),
            support_submodels=("HX_SNOWMAN_BASSIST_PLUCK_ZONE", "HX_SNOWMAN_BASSIST_BRIDGE"),
            timing_source="bass_note_e",
            sustain_behavior="vertical_note_travel",
        ),
        AnimationTarget(
            state="pluck_a",
            family="bass",
            primary_submodels=("HX_SNOWMAN_BASSIST_STRING_A",),
            support_submodels=("HX_SNOWMAN_BASSIST_PLUCK_ZONE", "HX_SNOWMAN_BASSIST_BRIDGE"),
            timing_source="bass_note_a",
            sustain_behavior="vertical_note_travel",
        ),
        AnimationTarget(
            state="pluck_d",
            family="bass",
            primary_submodels=("HX_SNOWMAN_BASSIST_STRING_D",),
            support_submodels=("HX_SNOWMAN_BASSIST_PLUCK_ZONE", "HX_SNOWMAN_BASSIST_BRIDGE"),
            timing_source="bass_note_d",
            sustain_behavior="vertical_note_travel",
        ),
        AnimationTarget(
            state="pluck_g",
            family="bass",
            primary_submodels=("HX_SNOWMAN_BASSIST_STRING_G",),
            support_submodels=("HX_SNOWMAN_BASSIST_PLUCK_ZONE", "HX_SNOWMAN_BASSIST_BRIDGE"),
            timing_source="bass_note_g",
            sustain_behavior="vertical_note_travel",
        ),
        AnimationTarget(
            state="bass_resonance",
            family="bass",
            primary_submodels=("HX_SNOWMAN_BASSIST_BODY_RESONANCE",),
            support_submodels=("HX_SNOWMAN_BASSIST_BASS_BODY",),
            timing_source="bass_sustain",
            sustain_behavior="body_bloom_decay",
        ),
    ),
    "HX_SNOWMAN_GUITARIST": (
        AnimationTarget(
            state="strum_down",
            family="guitar",
            primary_submodels=(
                "HX_SNOWMAN_GUITARIST_STRING_LOW_E",
                "HX_SNOWMAN_GUITARIST_STRING_A",
                "HX_SNOWMAN_GUITARIST_STRING_D",
                "HX_SNOWMAN_GUITARIST_STRING_G",
                "HX_SNOWMAN_GUITARIST_STRING_B",
                "HX_SNOWMAN_GUITARIST_STRING_HIGH_E",
            ),
            support_submodels=("HX_SNOWMAN_GUITARIST_PICK_ZONE", "HX_SNOWMAN_GUITARIST_BRIDGE"),
            timing_source="guitar_strum",
            sustain_behavior="horizontal_chord_sweep",
        ),
        AnimationTarget(
            state="pick_accent",
            family="guitar",
            primary_submodels=("HX_SNOWMAN_GUITARIST_PICK_ZONE",),
            support_submodels=("HX_SNOWMAN_GUITARIST_PICKUPS", "HX_SNOWMAN_GUITARIST_BODY_RESONANCE"),
            timing_source="accent_hits",
            sustain_behavior="short_pick_flash",
        ),
        AnimationTarget(
            state="neck_slide",
            family="guitar",
            primary_submodels=(
                "HX_SNOWMAN_GUITARIST_FRETBOARD_LOW",
                "HX_SNOWMAN_GUITARIST_FRETBOARD_MID",
                "HX_SNOWMAN_GUITARIST_FRETBOARD_HIGH",
            ),
            timing_source="pitch_motion",
            sustain_behavior="fretboard_chase",
        ),
    ),
    "HX_SNOWMAN_SINGER": (
        AnimationTarget(
            state="sing_start",
            family="lead_vocal",
            primary_submodels=("HX_SNOWMAN_SINGER_MOUTH", "HX_SNOWMAN_SINGER_MICROPHONE"),
            support_submodels=("HX_SNOWMAN_SINGER_VOCAL_GLOW",),
            timing_source="vocal_onset",
            sustain_behavior="phrase_bloom",
        ),
        AnimationTarget(
            state="power_belt",
            family="lead_vocal",
            primary_submodels=("HX_SNOWMAN_SINGER_MOUTH", "HX_SNOWMAN_SINGER_VOCAL_GLOW"),
            support_submodels=("HX_SNOWMAN_SINGER_RIGHT_HAND_MIC", "HX_SNOWMAN_SINGER_PLATFORM"),
            intensity_source="vocal_energy",
            timing_source="chorus_hooks",
            sustain_behavior="long_vocal_shimmer",
        ),
        AnimationTarget(
            state="heart_feel",
            family="lead_vocal",
            primary_submodels=("HX_SNOWMAN_SINGER_LEFT_HAND", "HX_SNOWMAN_SINGER_FACE"),
            support_submodels=("HX_SNOWMAN_SINGER_VOCAL_GLOW",),
            timing_source="lyric_emotion",
            sustain_behavior="soft_hold",
        ),
    ),
    "HX_SNOWMAN_SINGER_FEMALE": (
        AnimationTarget(
            state="harmony_start",
            family="harmony_vocal",
            primary_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH", "HX_SNOWMAN_SINGER_FEMALE_MICROPHONE"),
            support_submodels=("HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW",),
            timing_source="harmony_onset",
            sustain_behavior="harmony_bloom",
        ),
        AnimationTarget(
            state="call_response",
            family="harmony_vocal",
            primary_submodels=("HX_SNOWMAN_SINGER_FEMALE_RIGHT_HAND", "HX_SNOWMAN_SINGER_FEMALE_STAGE_GLOW"),
            support_submodels=("HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW",),
            timing_source="call_response",
            sustain_behavior="gesture_answer",
        ),
        AnimationTarget(
            state="big_vocal",
            family="harmony_vocal",
            primary_submodels=("HX_SNOWMAN_SINGER_FEMALE_MOUTH", "HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW"),
            support_submodels=("HX_SNOWMAN_SINGER_FEMALE_STAGE_GLOW", "HX_SNOWMAN_SINGER_FEMALE_BOW"),
            intensity_source="vocal_energy",
            timing_source="chorus_hooks",
            sustain_behavior="long_harmony_shimmer",
        ),
    ),
}


def animation_targets_for_model(model_name: str) -> tuple[AnimationTarget, ...]:
    return HELIXVILLE4_BAND_ANIMATION_MAP.get(model_name, ())


def all_required_animation_submodels() -> set[str]:
    required: set[str] = set()
    for targets in HELIXVILLE4_BAND_ANIMATION_MAP.values():
        for target in targets:
            required.update(target.primary_submodels)
            required.update(target.support_submodels)
    return required


def states_by_family(family: TriggerFamily) -> tuple[str, ...]:
    states: list[str] = []
    for targets in HELIXVILLE4_BAND_ANIMATION_MAP.values():
        states.extend(target.state for target in targets if target.family == family)
    return tuple(states)
