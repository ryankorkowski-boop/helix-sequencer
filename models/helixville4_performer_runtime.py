from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from models.helixville4_vocal_phonemes import PHONEME_NAMES, build_vocal_phoneme_catalog, validate_vocal_phoneme_catalog

@dataclass(frozen=True)
class PerformerState:
    name: str
    description: str
    primary_submodels: tuple[str, ...]
    intensity: float = 1.0
    def to_dict(self) -> dict[str, Any]: return asdict(self)

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
        payload = asdict(self); payload["states"] = [state.to_dict() for state in self.states]; return payload

def _sm(prefix: str, *names: str) -> tuple[str, ...]: return tuple(f"{prefix}_{name}" for name in names)
def _state(prefix: str, name: str, desc: str, parts: tuple[str, ...], intensity: float = 1.0) -> PerformerState: return PerformerState(name=name, description=desc, primary_submodels=_sm(prefix, *parts), intensity=intensity)

# Drummer V3 is asset-first and must use the approved V3 visual/model contract.
DRUMMER_V3_MODEL = "HX_SNOWMAN_DRUMMER_V3"
DRUMMER_V3_TOMS = ("TOM_HIGH", "TOM_MID", "TOM_FLOOR")
DRUMMER_V3_COMPONENTS = ("KICK", "SNARE", "HI_HAT", "TOM_HIGH", "TOM_MID", "TOM_FLOOR", "CYMBAL_LEFT", "CYMBAL_RIGHT")

DRUMMER_PARTS = ("HEAD", "FACE", "HAT", "HAT_BAND", "SCARF", "TORSO", "BUTTONS", "PLATFORM", *DRUMMER_V3_COMPONENTS)
DRUMMER_COMPONENTS = _sm(DRUMMER_V3_MODEL, *DRUMMER_V3_COMPONENTS)

BASSIST_PARTS = ("HEAD", "FACE", "HAT", "HAT_BAND", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "PLATFORM", "HAT_HOLLY", "BASS_BODY", "BASS_NECK", "BASS_SCROLL", "STRING_E", "STRING_A", "STRING_D", "STRING_G", "FINGERBOARD", "NECK_LOW", "NECK_MID", "NECK_HIGH", "PLUCK_ZONE", "BRIDGE", "BODY_RESONANCE")
GUITARIST_PARTS = ("HEAD", "FACE", "HAT", "HAT_BAND", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "PLATFORM", "HAT_HOLLY", "GUITAR_BODY", "GUITAR_NECK", "GUITAR_HEAD", "STRING_LOW_E", "STRING_A", "STRING_D", "STRING_G", "STRING_B", "STRING_HIGH_E", "PICK_ZONE", "PICKUPS", "BRIDGE", "FRETBOARD_LOW", "FRETBOARD_MID", "FRETBOARD_HIGH", "BODY_RESONANCE")
PHONEME_MOUTH_PARTS = tuple(f"MOUTH_{phoneme}" for phoneme in PHONEME_NAMES)
SINGER_PARTS = ("HEAD", "FACE", "HAT", "HAT_BAND", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "PLATFORM", "CARROT_NOSE", "HAT_HOLLY", "LEFT_HAND", "RIGHT_HAND_MIC", "MICROPHONE", "MIC_STAND", "MOUTH", *PHONEME_MOUTH_PARTS, "EYES", "EYEBROWS", "VOCAL_GLOW")
FEMALE_SINGER_PARTS = ("HEAD", "FACE", "HAT", "HAT_BAND", "SCARF", "TORSO", "BUTTONS", "LEFT_ARM", "RIGHT_ARM", "PLATFORM", "BOW", "EYES", "EYELASHES", "CARROT_NOSE", "MOUTH", *PHONEME_MOUTH_PARTS, "SCARF_TAIL_LEFT", "SCARF_TAIL_RIGHT", "LEFT_HAND", "RIGHT_HAND", "MICROPHONE", "MIC_STAND", "TORSO_UPPER", "TORSO_LOWER", "VOCAL_GLOW", "STAGE_GLOW")

DRUMMER = PerformerRuntimeSpec(
    performer_id="drummer", display_name="Mad Drummer Snowman", role="drums_transient_driver", model_name=DRUMMER_V3_MODEL,
    approved_state="approved_design_drummer_v3_three_tom_eight_component", visual_target="fixtures/band_geometry/drummer_v3_pose_spec.json",
    submodels=DRUMMER_COMPONENTS,
    states=(
        _state(DRUMMER_V3_MODEL, "ready_idle", "Standing ready behind the kit.", ("KICK",), 0.25),
        _state(DRUMMER_V3_MODEL, "kick_hit", "Kick drum impact; no stick channel.", ("KICK",), 0.85),
        _state(DRUMMER_V3_MODEL, "snare_hit", "Snare plus contacting stick contained in the snare component.", ("SNARE",), 0.9),
        _state(DRUMMER_V3_MODEL, "hi_hat_pulse", "Hi-hat plus contacting stick contained in the hi-hat component.", ("HI_HAT",), 0.65),
        _state(DRUMMER_V3_MODEL, "high_tom_hit", "High tom plus its contacting stick.", ("TOM_HIGH",), 0.8),
        _state(DRUMMER_V3_MODEL, "mid_tom_hit", "Mid tom plus its contacting stick.", ("TOM_MID",), 0.8),
        _state(DRUMMER_V3_MODEL, "floor_tom_hit", "Floor tom plus its contacting stick.", ("TOM_FLOOR",), 0.8),
        _state(DRUMMER_V3_MODEL, "left_cymbal_hit", "Left cymbal plus contacting stick contained in the left cymbal component.", ("CYMBAL_LEFT",), 1.0),
        _state(DRUMMER_V3_MODEL, "right_cymbal_hit", "Right cymbal plus contacting stick contained in the right cymbal component.", ("CYMBAL_RIGHT",), 1.0),
        _state(DRUMMER_V3_MODEL, "downbeat_impact", "Simultaneous kit impact across canonical components; no synthetic stick channels.", ("KICK", "SNARE", "CYMBAL_LEFT", "CYMBAL_RIGHT"), 1.0),
    ),
    audio_inputs=("kick", "snare", "cymbal_energy", "transients", "fill_density", "downbeat"),
    sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_INSTRUMENTS", "HX_SNOWMAN_DRUMS"),
)

GUITARIST = PerformerRuntimeSpec(performer_id="guitarist", display_name="Rock Guitar Snowman", role="rhythm_guitar_midrange_motion", model_name="HX_SNOWMAN_GUITARIST", approved_state="approved_design_guitarist_reactive_strings_v2_stem_ready", visual_target="docs/HELIXVILLE4_GUITARIST_REACTIVE_STRINGS.md", submodels=_sm("HX_SNOWMAN_GUITARIST", *GUITARIST_PARTS), states=(), audio_inputs=("midrange_energy", "guitar_transients", "beat", "section_intensity", "sustain"), sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_INSTRUMENTS", "HX_SNOWMAN_STRINGS"))
BASSIST = PerformerRuntimeSpec(performer_id="bassist", display_name="Bass Snowman", role="bass_groove_low_frequency_motion", model_name="HX_SNOWMAN_BASSIST", approved_state="approved_design_bassist_reactive_strings_v2_stem_ready", visual_target="docs/HELIXVILLE4_BASSIST_REACTIVE_STRINGS.md", submodels=_sm("HX_SNOWMAN_BASSIST", *BASSIST_PARTS), states=(), audio_inputs=("bass_energy", "low_frequency_onsets", "beat", "groove_density", "section_intensity"), sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_INSTRUMENTS", "HX_SNOWMAN_STRINGS"))
SINGER = PerformerRuntimeSpec(performer_id="singer", display_name="Lead Vocal Snowman", role="lead_vocal_focus", model_name="HX_SNOWMAN_SINGER", approved_state="approved_design_singer_vocal_performance_v2_phoneme_ready", visual_target="docs/HELIXVILLE4_SINGER_VOCAL_PERFORMANCE.md", submodels=_sm("HX_SNOWMAN_SINGER", *SINGER_PARTS), states=(), audio_inputs=("vocal_onset", "vocal_energy", "pitch_confidence", "lyric_phrase", "section_intensity", "phoneme"), sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_VOCALS"))
FEMALE_SINGER = PerformerRuntimeSpec(performer_id="female_singer", display_name="Harmony Vocal Snowman", role="harmony_vocal_call_response", model_name="HX_SNOWMAN_SINGER_FEMALE", approved_state="approved_design_female_singer_vocal_performance_v2_phoneme_ready", visual_target="docs/HELIXVILLE4_FEMALE_SINGER_VOCAL_PERFORMANCE.md", submodels=_sm("HX_SNOWMAN_SINGER_FEMALE", *FEMALE_SINGER_PARTS), states=(), audio_inputs=("harmony_onset", "vocal_energy", "call_response", "lyric_phrase", "section_intensity", "phoneme"), sequencing_groups=("HX_SNOWMAN_BAND", "HX_SNOWMAN_VOCALS"))
HELIXVILLE4_PERFORMERS = (DRUMMER, GUITARIST, BASSIST, SINGER, FEMALE_SINGER)

def build_performer_runtime_catalog() -> dict[str, Any]: return {"schema":"helixville4.performer_runtime_catalog.v3","catalog_id":"HELIXVILLE4_SNOWMAN_BAND_RUNTIME","state":"drummer_three_tom_eight_component_contract","performer_count":len(HELIXVILLE4_PERFORMERS),"model_names":[p.model_name for p in HELIXVILLE4_PERFORMERS],"groups":sorted({g for p in HELIXVILLE4_PERFORMERS for g in p.sequencing_groups}),"vocal_phonemes":build_vocal_phoneme_catalog(),"performers":[p.to_dict() for p in HELIXVILLE4_PERFORMERS]}

def validate_performer_runtime_catalog() -> dict[str, Any]:
    errors=[]
    for performer in HELIXVILLE4_PERFORMERS:
        known=set(performer.submodels)
        if "HX_SNOWMAN_BAND" not in performer.sequencing_groups: errors.append(f"{performer.model_name} missing HX_SNOWMAN_BAND group")
        if not performer.audio_inputs: errors.append(f"{performer.model_name} has no audio inputs")
        if not performer.states and performer is DRUMMER: errors.append(f"{performer.model_name} has no states")
        for state in performer.states:
            missing=sorted(set(state.primary_submodels)-known)
            if missing: errors.append(f"{performer.model_name}.{state.name} references missing submodels: {missing}")
    if DRUMMER.model_name != DRUMMER_V3_MODEL: errors.append("Drummer runtime is not bound to HX_SNOWMAN_DRUMMER_V3")
    if DRUMMER_V3_TOMS != ("TOM_HIGH", "TOM_MID", "TOM_FLOOR"): errors.append("Drummer V3 tom contract changed")
    if len(DRUMMER_V3_COMPONENTS) != 8: errors.append("Drummer V3 must expose exactly eight canonical components")
    phoneme_validation=validate_vocal_phoneme_catalog(singer_submodels=SINGER.submodels,female_singer_submodels=FEMALE_SINGER.submodels)
    errors.extend(phoneme_validation["errors"])
    return {"schema":"helixville4.performer_runtime_validation.v3","valid":not errors,"error_count":len(errors),"errors":errors,"performer_count":len(HELIXVILLE4_PERFORMERS),"phoneme_count":phoneme_validation["phoneme_count"]}
