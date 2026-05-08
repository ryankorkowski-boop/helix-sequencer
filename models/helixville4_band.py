from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StagePosition:
    x_ft: float
    y_ft: float
    z_ft: float = 0.0
    facing: str = "front"


@dataclass(frozen=True)
class BandMemberSpec:
    member_id: str
    display_name: str
    performer_type: str
    primary_role: str
    instrument: str
    model_prefix: str
    body_model: str
    instrument_model: str
    stage_position: StagePosition
    sequencing_lane: str
    timing_tracks: tuple[str, ...]
    animation_cues: tuple[str, ...]
    phoneme_capable: bool = False
    priority: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stage_position"] = asdict(self.stage_position)
        payload["timing_tracks"] = list(self.timing_tracks)
        payload["animation_cues"] = list(self.animation_cues)
        return payload


HELIXVILLE4_BAND_MEMBERS: tuple[BandMemberSpec, ...] = (
    BandMemberSpec(
        member_id="snowman_bassist",
        display_name="Snowman Bassist",
        performer_type="snowman",
        primary_role="low_end_groove",
        instrument="bass",
        model_prefix="HX_SNOWMAN_BASSIST",
        body_model="HX_SNOWMAN_BASSIST_BODY",
        instrument_model="HX_SNOWMAN_BASSIST_INSTRUMENT",
        stage_position=StagePosition(x_ft=285.0, y_ft=-48.0),
        sequencing_lane="lane_bass_groove",
        timing_tracks=("bass_hits", "downbeats", "section_pulses"),
        animation_cues=("pluck_zone", "neck_chase", "body_bob", "downbeat_pop"),
        priority=3,
    ),
    BandMemberSpec(
        member_id="snowman_guitarist",
        display_name="Snowman Guitarist",
        performer_type="snowman",
        primary_role="rhythm_and_hooks",
        instrument="guitar",
        model_prefix="HX_SNOWMAN_GUITARIST",
        body_model="HX_SNOWMAN_GUITARIST_BODY",
        instrument_model="HX_SNOWMAN_GUITARIST_INSTRUMENT",
        stage_position=StagePosition(x_ft=315.0, y_ft=-50.0),
        sequencing_lane="lane_guitar_hooks",
        timing_tracks=("guitar_strums", "chorus_hooks", "accent_hits"),
        animation_cues=("strum_zone", "string_chase", "head_nod", "chorus_flash"),
        priority=3,
    ),
    BandMemberSpec(
        member_id="snowman_drummer",
        display_name="Snowman Drummer",
        performer_type="snowman",
        primary_role="beat_anchor",
        instrument="drums",
        model_prefix="HX_SNOWMAN_DRUMMER",
        body_model="HX_SNOWMAN_DRUMMER_BODY",
        instrument_model="HX_SNOWMAN_DRUMMER_INSTRUMENT",
        stage_position=StagePosition(x_ft=345.0, y_ft=-58.0),
        sequencing_lane="lane_drum_hits",
        timing_tracks=("kick", "snare", "hihat", "fills", "downbeats"),
        animation_cues=("kick_hit", "snare_hit", "cymbal_crash", "stick_motion", "fill_sweep"),
        priority=4,
    ),
    BandMemberSpec(
        member_id="snowman_singer",
        display_name="Snowman Lead Singer",
        performer_type="snowman",
        primary_role="lead_vocal",
        instrument="microphone",
        model_prefix="HX_SNOWMAN_SINGER",
        body_model="HX_SNOWMAN_SINGER_BODY",
        instrument_model="HX_SNOWMAN_SINGER_INSTRUMENT",
        stage_position=StagePosition(x_ft=315.0, y_ft=-30.0),
        sequencing_lane="lane_lead_vocal",
        timing_tracks=("lyrics", "phonemes", "vocal_phrases", "chorus_hooks"),
        animation_cues=("mouth_phoneme", "mic_glow", "body_sway", "phrase_hold"),
        phoneme_capable=True,
        priority=5,
    ),
    BandMemberSpec(
        member_id="snowman_singer_female",
        display_name="Snowman Female Singer",
        performer_type="snowman",
        primary_role="harmony_vocal",
        instrument="microphone",
        model_prefix="HX_SNOWMAN_SINGER_FEMALE",
        body_model="HX_SNOWMAN_SINGER_FEMALE_BODY",
        instrument_model="HX_SNOWMAN_SINGER_FEMALE_INSTRUMENT",
        stage_position=StagePosition(x_ft=350.0, y_ft=-32.0),
        sequencing_lane="lane_harmony_vocal",
        timing_tracks=("lyrics", "phonemes", "harmony_phrases", "call_response"),
        animation_cues=("mouth_phoneme", "mic_glow", "call_response_step", "harmony_hold"),
        phoneme_capable=True,
        priority=5,
    ),
)


def build_helixville4_band_member_catalog() -> dict[str, Any]:
    members = [member.to_dict() for member in HELIXVILLE4_BAND_MEMBERS]
    return {
        "schema": "helixville4.band_members.v1",
        "stage_id": "snowman_band_stage",
        "scope": "layout_and_sequencing_metadata",
        "members": members,
        "groups": {
            "HX_SNOWMAN_BAND": [member.model_prefix for member in HELIXVILLE4_BAND_MEMBERS],
            "HX_SNOWMAN_VOCALS": [
                member.model_prefix for member in HELIXVILLE4_BAND_MEMBERS if member.phoneme_capable
            ],
            "HX_SNOWMAN_INSTRUMENTS": [
                member.model_prefix for member in HELIXVILLE4_BAND_MEMBERS if not member.phoneme_capable
            ],
        },
        "sequencing_lanes": [member.sequencing_lane for member in HELIXVILLE4_BAND_MEMBERS],
        "phoneme_models": [
            member.body_model for member in HELIXVILLE4_BAND_MEMBERS if member.phoneme_capable
        ],
        "implementation_boundary": {
            "layout_metadata": True,
            "layout_xml_generation": False,
            "sequencing_behavior": False,
            "audio_analysis": False,
            "animation_runtime": False,
        },
    }


def band_member_by_id(member_id: str) -> BandMemberSpec:
    normalized = member_id.strip().lower().replace("-", "_").replace(" ", "_")
    for member in HELIXVILLE4_BAND_MEMBERS:
        if member.member_id == normalized:
            return member
    known = ", ".join(member.member_id for member in HELIXVILLE4_BAND_MEMBERS)
    raise KeyError(f"Unknown Helixville4 band member {member_id!r}. Known members: {known}")
