from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PerformerState:
    name: str
    description: str
    primary_submodels: tuple[str, ...]
    intensity: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PerformerRuntimeSpec:
    performer_id: str
    display_name: str
    role: str
    model_name: str
    approved_state: str
    visual_target: str
    submodels: tuple[str, ...]
    states: tuple[PerformerState, ...]
    audio_inputs: tuple[str, ...]
    sequencing_groups: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["states"] = [state.to_dict() for state in self.states]
        return payload


def _sm(prefix: str, *names: str) -> tuple[str, ...]:
    return tuple(f"{prefix}_{name}" for name in names)


def _state(prefix: str, name: str, desc: str, parts: tuple[str, ...], intensity: float = 1.0) -> PerformerState:
    return PerformerState(name=name, description=desc, primary_submodels=_sm(prefix, *parts), intensity=intensity)


DRUMMER = PerformerRuntimeSpec(
    performer_id="drummer",
    display_name="Mad Drummer Snowman",
    role="drums_transient_driver",
    model_name="HX_SNOWMAN_DRUMMER",
    approved_state="approved_design_drummer_v1",
    visual_target="docs/HELIXVILLE4_DRUMMER_TARGET.md",
    submodels=_sm("HX_SNOWMAN_DRUMMER", "HEAD", "FACE", "HAT", "HAT_BAND", "HAT_HOLLY", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "LEFT_STICK", "RIGHT_STICK", "KICK", "KICK_RIM", "SNARE", "SNARE_RIM", "TOM_LEFT", "TOM_RIGHT", "HI_HAT", "CYMBAL_LEFT", "CYMBAL_RIGHT", "STANDS", "PLATFORM"),
    states=(
        _state("HX_SNOWMAN_DRUMMER", "ready_idle", "Standing ready behind the kit.", ("TORSO", "KICK"), 0.25),
        _state("HX_SNOWMAN_DRUMMER", "kick_hit", "Kick drum impact.", ("KICK", "KICK_RIM"), 0.75),
        _state("HX_SNOWMAN_DRUMMER", "snare_hit", "Snare hit with stick motion.", ("SNARE", "SNARE_RIM", "LEFT_STICK", "RIGHT_STICK"), 0.9),
        _state("HX_SNOWMAN_DRUMMER", "hi_hat_pulse", "Tight hi-hat pulse.", ("HI_HAT", "LEFT_ARM"), 0.65),
        _state("HX_SNOWMAN_DRUMMER", "tom_fill", "Tom fill movement across the kit.", ("TOM_LEFT", "TOM_RIGHT", "LEFT_STICK", "RIGHT_STICK"), 0.8),
        _state("HX_SNOWMAN_DRUMMER", "cymbal_crash", "Wide cymbal crash.", ("CYMBAL_LEFT", "CYMBAL_RIGHT", "RIGHT_ARM"), 1.0),
        _state("HX_SNOWMAN_DRUMMER", "downbeat_impact", "Full-kit downbeat impact.", ("KICK", "SNARE", "CYMBAL_LEFT", "CYMBAL_RIGHT"), 1.0),
    ),
    audio_inputs=("kick", "snare", "cymbal_energy", "transients", "fill_density", "downbeat"),
    sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_INSTRUMENTS", "HX_SNOWMAN_DRUMS"),
)

GUITARIST = PerformerRuntimeSpec(
    performer_id="guitarist",
    display_name="Rock Guitar Snowman",
    role="rhythm_guitar_midrange_motion",
    model_name="HX_SNOWMAN_GUITARIST",
    approved_state="approved_design_guitarist_reactive_strings_v1",
    visual_target="docs/HELIXVILLE4_GUITARIST_REACTIVE_STRINGS.md",
    submodels=_sm("HX_SNOWMAN_GUITARIST", "HEAD", "FACE", "HAT", "HAT_BAND", "HAT_HOLLY", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "GUITAR_BODY", "GUITAR_NECK", "GUITAR_HEAD", "GUITAR_STRINGS", "GUITAR_PICKUPS", "GUITAR_BRIDGE", "LEFT_HAND", "RIGHT_HAND", "STRUM_ZONE", "PLATFORM"),
    states=(
        _state("HX_SNOWMAN_GUITARIST", "ready_idle", "Standing ready with guitar.", ("GUITAR_BODY", "TORSO"), 0.25),
        _state("HX_SNOWMAN_GUITARIST", "strum_down", "Strong down strum.", ("RIGHT_HAND", "STRUM_ZONE", "GUITAR_STRINGS"), 0.8),
        _state("HX_SNOWMAN_GUITARIST", "chord_groove", "Grooving on chords.", ("GUITAR_STRINGS", "GUITAR_BODY"), 0.65),
        _state("HX_SNOWMAN_GUITARIST", "neck_slide", "Slide up the neck.", ("LEFT_HAND", "GUITAR_NECK", "GUITAR_STRINGS"), 0.75),
        _state("HX_SNOWMAN_GUITARIST", "hit_end", "Big chord hit and settle.", ("STRUM_ZONE", "GUITAR_STRINGS", "GUITAR_BODY"), 1.0),
    ),
    audio_inputs=("midrange_energy", "guitar_transients", "beat", "section_intensity", "sustain"),
    sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_INSTRUMENTS", "HX_SNOWMAN_STRINGS"),
)

BASSIST = PerformerRuntimeSpec(
    performer_id="bassist",
    display_name="Bass Snowman",
    role="bass_groove_low_frequency_motion",
    model_name="HX_SNOWMAN_BASSIST",
    approved_state="approved_design_bassist_reactive_strings_v1",
    visual_target="docs/HELIXVILLE4_BASSIST_REACTIVE_STRINGS.md",
    submodels=_sm("HX_SNOWMAN_BASSIST", "HEAD", "FACE", "HAT", "HAT_BAND", "HAT_HOLLY", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "BASS_BODY", "BASS_NECK", "BASS_SCROLL", "BASS_STRINGS", "BASS_BRIDGE", "LEFT_HAND", "RIGHT_HAND", "PLUCK_ZONE", "PLATFORM"),
    states=(
        _state("HX_SNOWMAN_BASSIST", "ready_idle", "Standing ready with upright bass.", ("BASS_BODY", "TORSO"), 0.25),
        _state("HX_SNOWMAN_BASSIST", "groove_start", "Gets into the groove.", ("BASS_BODY", "BASS_STRINGS"), 0.55),
        _state("HX_SNOWMAN_BASSIST", "pluck_groove", "Plucks with right hand.", ("RIGHT_HAND", "PLUCK_ZONE", "BASS_STRINGS"), 0.8),
        _state("HX_SNOWMAN_BASSIST", "neck_slide_up", "Left hand slides up neck.", ("LEFT_HAND", "BASS_NECK"), 0.65),
        _state("HX_SNOWMAN_BASSIST", "hit_end", "Big pluck hit and settle.", ("PLUCK_ZONE", "BASS_STRINGS", "BASS_BODY"), 1.0),
    ),
    audio_inputs=("bass_energy", "low_frequency_onsets", "beat", "groove_density", "section_intensity"),
    sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_INSTRUMENTS", "HX_SNOWMAN_STRINGS"),
)

SINGER = PerformerRuntimeSpec(
    performer_id="singer",
    display_name="Lead Vocal Snowman",
    role="lead_vocal_focus",
    model_name="HX_SNOWMAN_SINGER",
    approved_state="approved_design_singer_vocal_performance_v1",
    visual_target="docs/HELIXVILLE4_SINGER_VOCAL_PERFORMANCE.md",
    submodels=_sm("HX_SNOWMAN_SINGER", "HEAD", "FACE", "CARROT_NOSE", "HAT", "HAT_BAND", "HAT_HOLLY", "SCARF", "TORSO", "LEFT_ARM", "RIGHT_ARM", "LEFT_HAND", "RIGHT_HAND_MIC", "BUTTONS", "MICROPHONE", "MIC_STAND", "PLATFORM", "MOUTH", "EYES", "EYEBROWS", "VOCAL_GLOW"),
    states=(
        _state("HX_SNOWMAN_SINGER", "ready_idle", "Standing ready at the microphone.", ("TORSO", "MICROPHONE"), 0.25),
        _state("HX_SNOWMAN_SINGER", "sing_start", "Leans in and opens mouth.", ("MOUTH", "MICROPHONE", "VOCAL_GLOW"), 0.75),
        _state("HX_SNOWMAN_SINGER", "hand_raise", "Right hand lifts up.", ("RIGHT_ARM", "RIGHT_HAND_MIC", "VOCAL_GLOW"), 0.7),
        _state("HX_SNOWMAN_SINGER", "emote_high", "Big vocal moment.", ("MOUTH", "EYEBROWS", "VOCAL_GLOW"), 1.0),
        _state("HX_SNOWMAN_SINGER", "hit_hold", "Sustained note hold.", ("MOUTH", "VOCAL_GLOW", "MICROPHONE"), 1.0),
    ),
    audio_inputs=("vocal_onset", "vocal_energy", "pitch_confidence", "lyric_phrase", "section_intensity"),
    sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_VOCALS"),
)

FEMALE_SINGER = PerformerRuntimeSpec(
    performer_id="female_singer",
    display_name="Harmony Vocal Snowman",
    role="harmony_vocal_call_response",
    model_name="HX_SNOWMAN_SINGER_FEMALE",
    approved_state="approved_design_female_singer_vocal_performance_v1",
    visual_target="docs/HELIXVILLE4_FEMALE_SINGER_VOCAL_PERFORMANCE.md",
    submodels=_sm("HX_SNOWMAN_SINGER_FEMALE", "HEAD", "FACE", "EYES", "EYELASHES", "CARROT_NOSE", "MOUTH", "BOW", "SCARF", "SCARF_TAIL_LEFT", "SCARF_TAIL_RIGHT", "MIC_STAND", "MICROPHONE", "TORSO_UPPER", "TORSO_LOWER", "LEFT_ARM", "RIGHT_ARM", "LEFT_HAND", "RIGHT_HAND", "BUTTONS", "PLATFORM", "VOCAL_GLOW", "STAGE_GLOW", "CALL_RESPONSE"),
    states=(
        _state("HX_SNOWMAN_SINGER_FEMALE", "ready_idle", "Standing ready at the microphone.", ("TORSO_UPPER", "MICROPHONE"), 0.25),
        _state("HX_SNOWMAN_SINGER_FEMALE", "sing_start", "Leans in and opens mouth.", ("MOUTH", "MICROPHONE", "VOCAL_GLOW"), 0.75),
        _state("HX_SNOWMAN_SINGER_FEMALE", "point_out", "Points to the audience.", ("RIGHT_ARM", "RIGHT_HAND", "CALL_RESPONSE"), 0.8),
        _state("HX_SNOWMAN_SINGER_FEMALE", "big_vocal", "Big mouth, big moment.", ("MOUTH", "VOCAL_GLOW", "STAGE_GLOW"), 1.0),
        _state("HX_SNOWMAN_SINGER_FEMALE", "both_hands_up", "Crowd energy moment.", ("LEFT_ARM", "RIGHT_ARM", "LEFT_HAND", "RIGHT_HAND"), 0.95),
        _state("HX_SNOWMAN_SINGER_FEMALE", "hit_hold", "Sustained harmony hold.", ("MOUTH", "VOCAL_GLOW", "MICROPHONE"), 1.0),
    ),
    audio_inputs=("harmony_onset", "vocal_energy", "call_response", "lyric_phrase", "section_intensity"),
    sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_VOCALS"),
)

HELIXVILLE4_PERFORMERS: tuple[PerformerRuntimeSpec, ...] = (DRUMMER, GUITARIST, BASSIST, SINGER, FEMALE_SINGER)


def build_performer_runtime_catalog() -> dict[str, Any]:
    return {
        "schema": "helixville4.performer_runtime_catalog.v1",
        "catalog_id": "HELIXVILLE4_SNOWMAN_BAND_RUNTIME",
        "state": "approved_finished_band_members_v1",
        "performer_count": len(HELIXVILLE4_PERFORMERS),
        "model_names": [p.model_name for p in HELIXVILLE4_PERFORMERS],
        "groups": sorted({g for p in HELIXVILLE4_PERFORMERS for g in p.sequencing_groups}),
        "performers": [p.to_dict() for p in HELIXVILLE4_PERFORMERS],
    }


def validate_performer_runtime_catalog() -> dict[str, Any]:
    errors: list[str] = []
    for performer in HELIXVILLE4_PERFORMERS:
        known = set(performer.submodels)
        if "HX_SNOWMAN_BAND" not in performer.sequencing_groups:
            errors.append(f"{performer.model_name} missing HX_SNOWMAN_BAND group")
        if not performer.audio_inputs:
            errors.append(f"{performer.model_name} has no audio inputs")
        if not performer.states:
            errors.append(f"{performer.model_name} has no states")
        for state in performer.states:
            missing = sorted(set(state.primary_submodels) - known)
            if missing:
                errors.append(f"{performer.model_name}.{state.name} references missing submodels: {missing}")
    return {"schema": "helixville4.performer_runtime_validation.v1", "valid": not errors, "error_count": len(errors), "errors": errors, "performer_count": len(HELIXVILLE4_PERFORMERS)}
