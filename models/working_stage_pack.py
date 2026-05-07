from __future__ import annotations

from typing import Any, Iterable, Mapping

from models.working_band_member import (
    WORKING_MEMBER_SCHEMA,
    build_reactive_bassist_member,
    build_reactive_guitarist_member,
    build_reactive_singer_member,
    build_working_bassist,
    build_working_guitarist,
    build_working_singer,
)
from models.working_drummer import build_reactive_drummer_member, build_working_drummer
from models.working_female_singer import build_reactive_female_singer_member, build_working_female_singer
from models.working_floor_piano import build_reactive_floor_piano, build_working_floor_piano


STAGE_PACK_SCHEMA = "helix.working_snowman_stage_pack.v1"


def build_working_snowman_stage_pack(*, canvas_size: int = 64) -> dict[str, Any]:
    """Build the static working pack for the snowman band stage.

    This aggregates the individually proven working members/props into one
    payload so downstream export and preview tools have a stable entry point.
    """
    band_members = {
        "bassist": build_working_bassist(canvas_size),
        "guitarist": build_working_guitarist(canvas_size),
        "singer": build_working_singer(canvas_size),
        "female_singer": build_working_female_singer(canvas_size),
        "drummer": build_working_drummer(canvas_size),
    }
    stage_props = {"floor_piano": build_working_floor_piano()}
    return {
        "schema": STAGE_PACK_SCHEMA,
        "status": "working_stage_pack_slice",
        "pack_id": "HX_SNOWMAN_BAND_STAGE_PACK",
        "band_members": band_members,
        "stage_props": stage_props,
        "validation": {
            "all_members_have_required_submodels": all(
                member["validation"].get("has_required_submodels") for member in band_members.values()
            ),
            "all_members_have_animation_frames": all(
                member["validation"].get("has_animation_frames") for member in band_members.values()
            ),
            "all_stage_props_have_required_submodels": all(
                prop["validation"].get("has_required_submodels") for prop in stage_props.values()
            ),
        },
        "xlights_export_contract": {
            "target": "snowman_band_stage",
            "members": sorted(band_members),
            "stage_props": sorted(stage_props),
            "timing_tracks": ["phoneme", "word", "notes", "bass", "guitar", "drums", "beat", "phrase"],
            "first_sequence_smoke_test": "Render one short phrase with vocalist phonemes, guitar/bass cues, drum hits, and floor-piano key hooks.",
        },
    }


def build_reactive_snowman_stage_pack(
    *,
    lyric_events: Iterable[Any] = (),
    female_lyric_events: Iterable[Any] = (),
    vocal_peaks: Iterable[int] = (),
    female_vocal_peaks: Iterable[int] = (),
    note_events: Iterable[Any] = (),
    bass_peaks: Iterable[int] = (),
    guitar_onsets: Iterable[int] = (),
    beat_ms: Iterable[int] = (),
    parts: Iterable[Any] = (),
    drum_event_streams: dict[str, list[Any]] | None = None,
    kicks: Iterable[int] = (),
    snares: Iterable[int] = (),
    hats: Iterable[int] = (),
    cymbals: Iterable[int] = (),
    phrase_hits: Iterable[int] = (),
    band_sync_payload: Mapping[str, Any] | None = None,
    canvas_size: int = 64,
) -> dict[str, Any]:
    """Build the full reactive snowman band stage pack.

    The important integration here is that drummer reactive cues are fed into
    the floor piano, so the drummer can physically trigger stage-key hits via
    the existing player_piano_hook metadata.
    """
    note_event_list = list(note_events)
    beat_list = list(beat_ms)
    part_list = list(parts)
    vocal_peak_list = list(vocal_peaks)
    female_vocal_peak_list = list(female_vocal_peaks)
    drummer = build_reactive_drummer_member(
        drum_event_streams=drum_event_streams,
        kicks=kicks,
        snares=snares,
        hats=hats,
        cymbals=cymbals,
        canvas_size=canvas_size,
    )
    floor_piano = build_reactive_floor_piano(
        note_events=note_event_list,
        beat_ms=beat_list,
        drum_cues=drummer.get("reactive_cues", []),
        phrase_hits=phrase_hits,
    )
    band_members = {
        "bassist": build_reactive_bassist_member(
            bass_peaks=bass_peaks,
            note_events=note_event_list,
            beat_ms=beat_list,
            parts=part_list,
            band_sync_payload=band_sync_payload,
            canvas_size=canvas_size,
        ),
        "guitarist": build_reactive_guitarist_member(
            note_events=note_event_list,
            onset_ms=guitar_onsets,
            beat_ms=beat_list,
            parts=part_list,
            band_sync_payload=band_sync_payload,
            canvas_size=canvas_size,
        ),
        "singer": build_reactive_singer_member(
            lyric_events=lyric_events,
            vocal_peaks=vocal_peak_list,
            parts=part_list,
            canvas_size=canvas_size,
        ),
        "female_singer": build_reactive_female_singer_member(
            lyric_events=female_lyric_events,
            vocal_peaks=female_vocal_peak_list,
            parts=part_list,
            canvas_size=canvas_size,
        ),
        "drummer": drummer,
    }
    stage_props = {"floor_piano": floor_piano}
    floor_sources = {cue.get("source") for cue in floor_piano.get("reactive_cues", [])}
    return {
        "schema": STAGE_PACK_SCHEMA,
        "status": "reactive_working_stage_pack_slice",
        "pack_id": "HX_SNOWMAN_BAND_STAGE_PACK",
        "band_members": band_members,
        "stage_props": stage_props,
        "integration": {
            "drummer_feeds_floor_piano": "player_piano_hook" in floor_sources,
            "floor_piano_sources": sorted(str(source) for source in floor_sources if source),
            "drummer_cue_count": len(drummer.get("reactive_cues", [])),
            "floor_piano_cue_count": len(floor_piano.get("reactive_cues", [])),
        },
        "validation": {
            "all_members_have_reactive_cues": all(
                member["validation"].get("has_reactive_cues") for member in band_members.values()
            ),
            "all_member_reactive_cues_target_existing_submodels": all(
                member["validation"].get("reactive_cues_target_existing_submodels") for member in band_members.values()
            ),
            "all_stage_props_have_reactive_cues": all(
                prop["validation"].get("has_reactive_cues") for prop in stage_props.values()
            ),
            "all_stage_prop_cues_target_existing_submodels": all(
                prop["validation"].get("reactive_cues_target_existing_submodels") for prop in stage_props.values()
            ),
            "drummer_feeds_floor_piano": "player_piano_hook" in floor_sources,
        },
        "xlights_export_contract": {
            "target": "snowman_band_stage",
            "members": sorted(band_members),
            "stage_props": sorted(stage_props),
            "timing_tracks": ["phoneme", "word", "notes", "bass", "guitar", "drums", "beat", "phrase"],
            "first_sequence_smoke_test": "Render one short phrase with vocalist phonemes, guitar/bass cues, drum hits, and floor-piano key hooks.",
        },
    }
