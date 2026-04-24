from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from core import vocal_timeline as vt
from core import vocal_emotion
from animation import drummer_motion
from animation import string_motion
from effects import drum_effects
from audio import instrument_detection
from mapping import drum_mapper


def normalize_name(value: str) -> str:
    return " ".join((value or "").lower().replace("_", " ").replace("-", " ").split())


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _event_start_ms(event: Any) -> int:
    return max(0, int(getattr(event, "start_ms", 0) or 0))


def _event_end_ms(event: Any, fallback_ms: int = 140) -> int:
    start_ms = _event_start_ms(event)
    return max(start_ms + fallback_ms, int(getattr(event, "end_ms", start_ms + fallback_ms) or (start_ms + fallback_ms)))


def _event_text(event: Any) -> str:
    return str(getattr(event, "text", "") or "").strip()


def _part_label(parts: list[Any], target_ms: int) -> str:
    for part in parts:
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", start_ms) or start_ms)
        if start_ms <= target_ms < end_ms:
            return str(getattr(part, "label", "SECTION") or "SECTION").upper()
    return "SECTION"


def _extract_note_midis(note_events: list[Any], target_ms: int) -> list[float]:
    best_event: Any | None = None
    best_distance: int | None = None
    for event in note_events:
        start_ms = _event_start_ms(event)
        end_ms = _event_end_ms(event, fallback_ms=180)
        if start_ms <= target_ms <= end_ms:
            best_event = event
            break
        distance = min(abs(target_ms - start_ms), abs(target_ms - end_ms))
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_event = event
    if best_event is None:
        return []
    out: list[float] = []
    for note in list(getattr(best_event, "notes", []) or []):
        if isinstance(note, (list, tuple)) and note:
            try:
                out.append(float(note[0]))
            except (TypeError, ValueError):
                continue
    return out


def _string_index_for_pitch(pitch_midi: float) -> int:
    clamped = min(67.0, max(36.0, float(pitch_midi)))
    return int(min(4, max(1, round(((clamped - 36.0) / 31.0) * 3.0) + 1)))


def _neck_position_for_pitch(pitch_midi: float) -> int:
    clamped = min(84.0, max(42.0, float(pitch_midi)))
    return int(min(4, max(1, round(((clamped - 42.0) / 42.0) * 3.0) + 1)))


def _split_lyric_fragments(text: str, max_parts: int = 5) -> list[str]:
    tokens = [token for token in re.findall(r"[A-Za-z']+", text) if token]
    if not tokens:
        return []
    fragments: list[str] = []
    for token in tokens:
        pieces = re.findall(r"[^aeiouyAEIOUY]*[aeiouyAEIOUY]+(?:[^aeiouyAEIOUY]*|$)", token)
        if not pieces:
            pieces = [token]
        for piece in pieces:
            cleaned = piece.strip("-' ")
            if cleaned:
                fragments.append(cleaned)
        if len(fragments) >= max_parts:
            break
    if not fragments:
        return tokens[:max_parts]
    return fragments[:max_parts]


def _viseme_for_fragment(fragment: str) -> str:
    text = normalize_name(fragment)
    if not text:
        return "REST"
    if any(text.startswith(prefix) for prefix in ("m", "b", "p")):
        return "MBP"
    if any(char in text for char in ("f", "v")):
        return "FV"
    if any(char in text for char in ("o", "u", "w")):
        return "OH"
    if any(char in text for char in ("i", "e", "y")):
        return "EE"
    if any(char in text for char in ("a", "r")):
        return "AH"
    return "REST"


def preferred_face_routing(layout_names: list[str]) -> dict[str, Any]:
    normalized = [(name, normalize_name(name)) for name in layout_names]
    mascot_custom = [name for name, norm in normalized if "helixmascot" in norm and "custom" in norm]
    mascot_image = [name for name, norm in normalized if "helixmascot" in norm and "image" in norm]
    support_faces = [
        name
        for name, norm in normalized
        if any(token in norm for token in ("singing face", "talking head", "face panel", "singer"))
    ]
    lyric_surfaces = [
        name
        for name, norm in normalized
        if any(token in norm for token in ("matrix", "custom", "word helix", "helixmascot", "singing face"))
    ]

    preferred_lead = ""
    if mascot_custom:
        preferred_lead = mascot_custom[0]
    elif support_faces:
        preferred_lead = support_faces[0]
    elif mascot_image:
        preferred_lead = mascot_image[0]

    lead_cycle: list[str] = []
    if mascot_custom:
        lead_cycle.extend([mascot_custom[0], mascot_custom[0]])
    elif mascot_image:
        lead_cycle.append(mascot_image[0])
    lead_cycle.extend(support_faces)
    if not lead_cycle:
        lead_cycle.extend(mascot_custom or mascot_image or support_faces)

    surfaces = _unique(lyric_surfaces or mascot_custom or mascot_image or support_faces)
    return {
        "preferred_lead": preferred_lead,
        "lead_cycle": lead_cycle,
        "support_faces": _unique(support_faces),
        "lyric_surfaces": surfaces,
    }


def _build_performer_catalog(face_routing: Mapping[str, Any]) -> dict[str, Any]:
    preferred_lead = str(face_routing.get("preferred_lead", "") or "")
    singer_name = "Helix Helper" if "helixmascot" in normalize_name(preferred_lead) else "Lead Snowman"
    return {
        "lead_singer": {
            "display_name": singer_name,
            "role": "lead_singer",
            "preferred_targets": _unique(list(face_routing.get("lead_cycle", []) or [])),
            "modes": {
                "pixel": ["mouth_closed", "mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP", "lyric_text_hold"],
                "ac_rgbw": ["mouth_closed", "mouth_open_small", "mouth_open_mid", "mouth_open_wide"],
                "matrix": ["viseme_closed", "mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP", "lyric_word"],
            },
            "face_definition": {"style": "full", "intensity": 1.0, "xlights_mode": "custom_submodels"},
        },
        "bassist": {
            "display_name": "Standup Bass Snowman",
            "role": "bassist",
            "preferred_targets": ["vertical_props", "trees", "columns"],
            "modes": {
                "pixel": ["string_lane_1", "string_lane_2", "string_lane_3", "string_lane_4", "head_bob", "bg_mouth_A", "bg_mouth_E", "bg_mouth_I", "bg_mouth_O", "bg_mouth_U", "bg_mouth_MBP"],
                "ac_rgbw": ["string_low", "string_lowmid", "string_highmid", "string_high", "body_bob"],
                "matrix": ["bass_lane_1", "bass_lane_2", "bass_lane_3", "bass_lane_4", "fret_position", "bg_face_small"],
            },
            "face_definition": {"style": "minimalist_background", "intensity": 0.38, "xlights_mode": "custom_submodels"},
        },
        "guitarist": {
            "display_name": "Guitar Snowman",
            "role": "guitarist",
            "preferred_targets": ["arches", "directional_props", "matrices"],
            "modes": {
                "pixel": ["strum_down", "strum_up", "neck_pos_1", "neck_pos_2", "neck_pos_3", "neck_pos_4", "bg_mouth_A", "bg_mouth_E", "bg_mouth_I", "bg_mouth_O", "bg_mouth_U", "bg_mouth_MBP"],
                "ac_rgbw": ["strum_frame_a", "strum_frame_b", "neck_low", "neck_mid", "neck_high"],
                "matrix": ["guitar_arc", "guitar_ribbon", "neck_tracker", "bg_face_small"],
            },
            "face_definition": {"style": "minimalist_background", "intensity": 0.42, "xlights_mode": "custom_submodels"},
        },
        "drummer": {
            "display_name": "Drummer Snowman",
            "role": "drummer",
            "preferred_targets": ["percussion_props", "matrices", "circles"],
            "modes": {
                "pixel": ["kick_center", "kick_mid", "kick_outer", "snare_burst", "hat_flash", "cymbal_shimmer"],
                "ac_rgbw": ["kick_ring_1", "kick_ring_2", "kick_ring_3", "snare_hit", "hat_open", "cymbal_frame_1", "cymbal_frame_2", "cymbal_frame_3", "cymbal_frame_4"],
                "matrix": ["kick_wave", "snare_contact", "hat_plate", "cymbal_arc", "cheer_face"],
            },
            "face_definition": {"style": "reaction_only", "intensity": 0.32, "xlights_mode": "custom_submodels"},
        },
    }


def _build_singer_cues(
    lyric_events: list[Any],
    *,
    face_routing: Mapping[str, Any],
    parts: list[Any],
    enable_lyrics: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not enable_lyrics:
        return [], []
    singer_cues: list[dict[str, Any]] = []
    tunnel_overlays: list[dict[str, Any]] = []
    lead_cycle = list(face_routing.get("lead_cycle", []) or [])
    preferred_lead = str(face_routing.get("preferred_lead", "") or "")
    for index, lyric_event in enumerate(lyric_events):
        text = _event_text(lyric_event)
        if not text:
            continue
        start_ms = _event_start_ms(lyric_event)
        end_ms = _event_end_ms(lyric_event, fallback_ms=220)
        fragments = _split_lyric_fragments(text)
        if not fragments:
            continue
        step_ms = max(55, int((end_ms - start_ms) / max(1, len(fragments))))
        target_name = lead_cycle[index % len(lead_cycle)] if lead_cycle else preferred_lead
        section = _part_label(parts, start_ms)
        for fragment_index, fragment in enumerate(fragments):
            frag_start = start_ms + fragment_index * step_ms
            frag_end = min(end_ms, frag_start + max(45, int(step_ms * 0.78)))
            viseme = _viseme_for_fragment(fragment)
            singer_cues.append(
                {
                    "performer": "lead_singer",
                    "target": target_name,
                    "start_ms": frag_start,
                    "end_ms": frag_end,
                    "kind": "viseme",
                    "section": section,
                    "lyric_text": text,
                    "fragment": fragment,
                    "viseme": viseme,
                    "pixel_frame": f"mouth_{viseme.lower()}",
                    "ac_frame": viseme.lower(),
                    "matrix_frame": f"viseme_{viseme.lower()}",
                }
            )
        horizon_ms = min(2200, max(420, (end_ms - start_ms) * 3))
        tunnel_overlays.append(
            {
                "text": text,
                "preview_start_ms": max(0, start_ms - horizon_ms),
                "hit_ms": start_ms,
                "impact_end_ms": min(end_ms + 320, start_ms + 1800),
                "decay_mode": "reverse_smoke",
                "target": target_name,
                "section": section,
            }
        )
    return singer_cues, tunnel_overlays


def _build_string_realism_cues(
    parts: list[Any],
    bass_peaks: list[int],
    note_events: list[Any],
    beat_ms: list[int],
    band_sync_payload: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    guitar_events, guitar_debug = instrument_detection.derive_guitar_events(
        note_events,
        onset_ms=bass_peaks,
        beat_ms=beat_ms,
    )
    bass_events, bass_debug = instrument_detection.derive_bass_events(
        bass_peaks,
        note_events,
        beat_ms=beat_ms,
    )
    guitar_cues = string_motion.build_guitar_motion_cues(
        guitar_events,
        parts=parts,
        band_sync_payload=band_sync_payload,
    )
    bass_cues = string_motion.build_bass_motion_cues(
        bass_events,
        parts=parts,
        band_sync_payload=band_sync_payload,
    )
    debug = {
        "schema": "helix.string_instrument_realism.v1",
        "guitar": {
            **dict(guitar_debug),
            "events": [event.to_dict() for event in guitar_events],
            "motion_timeline": guitar_cues,
            "mapping_log": [
                {
                    "event_type": cue.get("kind"),
                    "submodel": cue.get("submodel"),
                    "start_ms": cue.get("start_ms"),
                    "confidence": cue.get("confidence"),
                }
                for cue in guitar_cues
            ],
        },
        "bass": {
            **dict(bass_debug),
            "events": [event.to_dict() for event in bass_events],
            "motion_timeline": bass_cues,
            "mapping_log": [
                {
                    "event_type": cue.get("kind"),
                    "submodel": cue.get("submodel"),
                    "start_ms": cue.get("start_ms"),
                    "confidence": cue.get("confidence"),
                }
                for cue in bass_cues
            ],
        },
        "fallback_logic": {
            "guitar": "uses note clusters first, then onset/beat rhythm fallback",
            "bass": "uses bass peaks and low note sustains first, then beat fallback",
            "silent_failure_policy": "debug event_count and fallback_mode are always emitted",
        },
    }
    return bass_cues, guitar_cues, debug


def _build_drum_cues(
    parts: list[Any],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    releases: list[int],
) -> tuple[list[dict[str, Any]], list[str]]:
    cues: list[dict[str, Any]] = []
    kit: list[str] = []
    if kicks:
        kit.append("kick")
        for hit_ms in kicks:
            cues.append(
                {
                    "performer": "drummer",
                    "start_ms": int(hit_ms),
                    "end_ms": int(hit_ms) + 120,
                    "kind": "kick",
                    "section": _part_label(parts, int(hit_ms)),
                    "frames": ["kick_center", "kick_mid", "kick_outer"],
                }
            )
    if snares:
        kit.append("snare")
        for hit_ms in snares:
            cues.append(
                {
                    "performer": "drummer",
                    "start_ms": int(hit_ms),
                    "end_ms": int(hit_ms) + 110,
                    "kind": "snare",
                    "section": _part_label(parts, int(hit_ms)),
                    "frames": ["snare_burst"],
                }
            )
    if hats:
        kit.append("hihat")
        for hit_ms in hats:
            cues.append(
                {
                    "performer": "drummer",
                    "start_ms": int(hit_ms),
                    "end_ms": int(hit_ms) + 90,
                    "kind": "hihat",
                    "section": _part_label(parts, int(hit_ms)),
                    "frames": ["hat_flash"],
                }
            )
    cymbal_hits = sorted({int(value) for value in list(releases or []) + list(hats[:: max(1, len(hats) // 24)] if hats else [])})
    if cymbal_hits:
        kit.append("cymbal")
        for hit_ms in cymbal_hits:
            cues.append(
                {
                    "performer": "drummer",
                    "start_ms": int(hit_ms),
                    "end_ms": int(hit_ms) + 220,
                    "kind": "cymbal",
                    "section": _part_label(parts, int(hit_ms)),
                    "frames": ["cymbal_frame_1", "cymbal_frame_2", "cymbal_frame_3", "cymbal_frame_4"],
                    "shimmer": True,
                }
            )
    return cues, kit


def _build_intelligent_drum_cues(
    parts: list[Any],
    *,
    drum_event_streams: dict[str, list[Any]] | None,
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    releases: list[int],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    resolved = drum_mapper.resolve_drum_streams(
        drum_event_streams,
        fallback_kicks=kicks,
        fallback_snares=snares,
        fallback_hats=hats,
        fallback_cymbals=releases,
    )
    events = list(resolved["events"])
    mapped = list(resolved["mapped_events"])
    motions = drummer_motion.build_drummer_motion(events)
    effect_cues = drum_effects.build_drum_effect_cues(events)
    cues: list[dict[str, Any]] = []
    for idx, item in enumerate(mapped):
        start_ms = int(item["timestamp_ms"])
        drum_type = str(item["drum_type"])
        effect = effect_cues[idx] if idx < len(effect_cues) else {}
        cue = {
            "performer": "drummer",
            "start_ms": start_ms,
            "end_ms": int(effect.get("end_ms", start_ms + 140)),
            "kind": drum_type,
            "section": _part_label(parts, start_ms),
            "submodel": item["submodel"],
            "composite_submodels": item["composite_submodels"],
            "velocity": item["velocity"],
            "confidence": item["confidence"],
            "frequency_band_info": item["frequency_band_info"],
            "cluster_id": item["cluster_id"],
            "source": item["source"],
            "visual_effect": effect,
        }
        if drum_type == "kick":
            cue["frames"] = ["kick_center", "kick_mid", "kick_outer"]
        elif drum_type == "snare":
            cue["frames"] = ["snare_burst"]
        elif drum_type == "hihat":
            cue["frames"] = ["hat_flash"]
        elif drum_type == "cymbal":
            cue["frames"] = ["cymbal_frame_1", "cymbal_frame_2", "cymbal_frame_3", "cymbal_frame_4"]
            cue["shimmer"] = True
        elif drum_type == "tom":
            cue["frames"] = ["tom_bounce"]
        else:
            cue["frames"] = ["drum_bus_pulse"]
        cues.append(cue)
    kit = sorted({str(item["drum_type"]) for item in mapped if item["drum_type"] != "drum_bus"})
    if any(str(item["drum_type"]) == "drum_bus" for item in mapped):
        kit.append("drum_bus")
    debug = {
        "fallback_mode": resolved["fallback_mode"],
        "counts": resolved["counts"],
        "motion_events": motions,
        "effect_cues": effect_cues,
        "mapping": mapped,
    }
    return cues, kit, debug


def _build_background_vocals(vocal_peaks: list[int], parts: list[Any]) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for index, hit_ms in enumerate(vocal_peaks):
        performer = "bassist" if index % 2 == 0 else "guitarist"
        cues.append(
            {
                "performer": performer,
                "start_ms": int(hit_ms),
                "end_ms": int(hit_ms) + 120,
                "kind": "background_vocal",
                "section": _part_label(parts, int(hit_ms)),
            }
        )
    return cues


def _song_part_multiplier(part_name: str, performer: str) -> float:
    part = part_name.lower()
    if performer == "lead_singer":
        if part in {"chorus", "post_chorus"}:
            return 1.0
        if part in {"bridge"}:
            return 0.82
        if part in {"breakdown", "drop"}:
            return 0.62
        if part == "outro":
            return 0.58
        return 0.78
    if performer in {"guitarist", "bassist"}:
        if part in {"chorus", "post_chorus"}:
            return 1.0
        if part in {"bridge"}:
            return 0.68
        if part in {"drop"}:
            return 0.48
        if part == "outro":
            return 0.4
        return 0.34
    return 0.35


def _build_lead_face_activations(lyric_timeline: vt.LyricTimeline, song_parts: list[vt.SongPart]) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for event in lyric_timeline.phoneme_events:
        part = vt.part_name_at(song_parts, event.start_time)
        intensity = round(min(1.0, event.confidence * _song_part_multiplier(part, "lead_singer") + 0.18), 3)
        cues.append(
            {
                "performer": "lead_singer",
                "role": "lead_vocal",
                "start_ms": event.start_ms,
                "end_ms": event.end_ms,
                "kind": "phoneme_face",
                "part_name": part,
                "phoneme": event.phoneme,
                "mouth_shape": event.mouth_shape,
                "mouth_submodel": event.mouth_submodel,
                "lyric_text": event.word_text,
                "confidence": round(event.confidence, 3),
                "intensity": intensity,
                "xlights": {"effect": "Faces", "face_definition": "lead_singer_full", "timing_track": "phoneme"},
            }
        )
    return cues


def _mouth_event_for_window(window: Mapping[str, Any], lyric_timeline: vt.LyricTimeline) -> vt.PhonemeEvent:
    start = float(window.get("start_time", 0.0) or 0.0)
    end = float(window.get("end_time", start + 0.16) or (start + 0.16))
    overlapping = [
        event
        for event in lyric_timeline.phoneme_events
        if event.start_time <= end and event.end_time >= start
    ]
    if overlapping:
        return overlapping[0]
    return vt.PhonemeEvent("AH", "mouth_A", "mouth_A", start, end, float(window.get("confidence", 0.4) or 0.4), "bg_vocal", "background_energy")


def _build_background_face_activations(
    lyric_timeline: vt.LyricTimeline,
    song_parts: list[vt.SongPart],
    background_windows: list[dict[str, Any]],
    *,
    config: vt.VocalRoutingConfig,
    note_events: list[Any],
    bass_peaks: list[int],
) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for window in background_windows:
        performers = ["guitarist", "bassist"] if str(window.get("performer", "guitarist")) == "group" else [str(window.get("performer", "guitarist"))]
        event = _mouth_event_for_window(window, lyric_timeline)
        start_ms = int(round(float(window.get("start_time", event.start_time)) * 1000.0))
        end_ms = int(round(float(window.get("end_time", event.end_time)) * 1000.0))
        part = str(window.get("part_name") or vt.part_name_at(song_parts, start_ms / 1000.0))
        for performer in performers:
            conflict_scale = 1.0
            if performer == "guitarist":
                busy = sum(1 for note in note_events if _event_start_ms(note) <= start_ms <= _event_end_ms(note))
                conflict_scale = 0.74 if busy else 1.0
            elif performer == "bassist":
                busy = any(abs(int(peak) - start_ms) < 90 for peak in bass_peaks)
                conflict_scale = 0.70 if busy else 0.88
            intensity = min(
                config.background_face_max_intensity,
                float(window.get("confidence", 0.4) or 0.4) * _song_part_multiplier(part, performer) * conflict_scale,
            )
            cues.append(
                {
                    "performer": performer,
                    "role": "group_chant" if window.get("role") == "group_chant" else "background_vocal",
                    "start_ms": start_ms,
                    "end_ms": max(start_ms + int(config.background_face_min_duration * 1000), end_ms),
                    "kind": "minimalist_background_face",
                    "part_name": part,
                    "phoneme": event.phoneme,
                    "mouth_shape": event.mouth_shape,
                    "mouth_submodel": f"bg_{event.mouth_submodel}",
                    "lyric_text": event.word_text,
                    "confidence": round(float(window.get("confidence", event.confidence) or event.confidence), 3),
                    "intensity": round(max(0.08, intensity), 3),
                    "source_reason": str(window.get("source_reason", "background_vocal_window")),
                    "classifier_role": str(window.get("classifier_role", "")),
                    "instrument_conflict_scale": round(conflict_scale, 3),
                    "xlights": {"effect": "Faces", "face_definition": f"{performer}_minimalist_background", "timing_track": "background_phoneme"},
                }
            )
        if window.get("role") == "group_chant":
            cues.append(
                {
                    "performer": "drummer",
                    "role": "group_chant_reaction",
                    "start_ms": start_ms,
                    "end_ms": max(start_ms + 180, end_ms),
                    "kind": "cheer_face",
                    "part_name": part,
                    "mouth_shape": "mouth_O",
                    "mouth_submodel": "cheer_face",
                    "confidence": round(float(window.get("confidence", 0.5) or 0.5), 3),
                    "intensity": 0.36,
                    "source_reason": str(window.get("source_reason", "background_vocal_window")),
                }
            )
    return cues


def _build_part_hit_reactions(part_hits: list[vt.PartHit]) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for hit in part_hits:
        start_ms = hit.start_ms
        duration = 220 if hit.hit_type != "lyric_phrase_hit" else 140
        if hit.hit_type in {"chorus_start", "drop_hit", "breakdown_start", "bridge_enter", "solo_enter"}:
            for performer in ("lead_singer", "guitarist", "bassist"):
                cues.append(
                    {
                        "performer": performer,
                        "role": "part_hit_reaction",
                        "start_ms": start_ms,
                        "end_ms": start_ms + duration,
                        "kind": "performer_emphasis",
                        "part_name": hit.part_name,
                        "hit_type": hit.hit_type,
                        "strength": hit.strength,
                        "confidence": hit.confidence,
                    }
                )
            cues.append(
                {
                    "performer": "drummer",
                    "role": "drummer_face_reaction",
                    "start_ms": start_ms,
                    "end_ms": start_ms + max(duration, 260),
                    "kind": "cheer_face",
                    "part_name": hit.part_name,
                    "hit_type": hit.hit_type,
                    "mouth_shape": "mouth_O",
                    "mouth_submodel": "cheer_face",
                    "intensity": round(min(0.55, 0.2 + hit.strength * 0.35), 3),
                    "confidence": hit.confidence,
                }
            )
    return cues


def _debug_timeline(
    lyric_timeline: vt.LyricTimeline,
    song_parts: list[vt.SongPart],
    part_hits: list[vt.PartHit],
    face_activations: list[dict[str, Any]],
    background_windows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "lyric_timeline": [f"{line.start_time:.2f}-{line.end_time:.2f} {line.text}" for line in lyric_timeline.lines[:80]],
        "phoneme_timeline": [
            f"{event.start_time:.2f}-{event.end_time:.2f} {event.word_text}:{event.phoneme}->{event.mouth_shape}"
            for event in lyric_timeline.phoneme_events[:180]
        ],
        "song_parts": [
            f"{part.name} {part.start_time:.2f}-{part.end_time:.2f} conf={part.confidence:.2f} energy={part.energy_level:.2f}"
            for part in song_parts
        ],
        "part_hits": [
            f"{hit.timestamp:.2f} {hit.part_name}:{hit.hit_type} strength={hit.strength:.2f} conf={hit.confidence:.2f}"
            for hit in part_hits[:120]
        ],
        "face_activation_log": [
            f"{cue.get('start_ms', 0)/1000:.2f} {cue.get('performer')} {cue.get('role')} {cue.get('mouth_shape', cue.get('hit_type', ''))} i={cue.get('intensity', cue.get('strength', ''))}"
            for cue in face_activations[:220]
        ],
        "vocal_routing_log": [
            f"{window.get('start_time'):.2f} {window.get('performer')} bg conf={window.get('confidence')} reason={window.get('source_reason')}"
            for window in background_windows[:120]
        ],
    }


def _build_timing_intelligence(
    *,
    lyric_timeline: vt.LyricTimeline,
    song_parts: list[vt.SongPart],
    part_hits: list[vt.PartHit],
    performers: Mapping[str, Any],
    face_events: list[dict[str, Any]],
    background_windows: list[dict[str, Any]],
) -> dict[str, Any]:
    face_definitions = {
        name: {
            **dict(performer.get("face_definition", {}) or {}),
            "performer": name,
            "mouth_shapes": ["mouth_A", "mouth_E", "mouth_I", "mouth_O", "mouth_U", "mouth_MBP"],
        }
        for name, performer in performers.items()
        if performer.get("face_definition")
    }
    faces_effect_instructions: list[dict[str, Any]] = []
    for cue in face_events:
        xlights = dict(cue.get("xlights", {}) or {})
        if not cue.get("mouth_submodel") and xlights.get("effect") != "Faces":
            continue
        performer = str(cue.get("performer", ""))
        role = str(cue.get("role", ""))
        faces_effect_instructions.append(
            {
                "effect": "Faces",
                "performer": performer,
                "vocal_role": role,
                "face_definition": xlights.get("face_definition") or f"{performer}_reaction",
                "timing_track": xlights.get("timing_track") or ("part_hit_reaction" if "hit" in role else "face_timing"),
                "start_ms": int(cue.get("start_ms", 0) or 0),
                "end_ms": int(cue.get("end_ms", 0) or 0),
                "phoneme": cue.get("phoneme", ""),
                "mouth_shape": cue.get("mouth_shape", ""),
                "mouth_submodel": cue.get("mouth_submodel", ""),
                "intensity": float(cue.get("intensity", cue.get("strength", 0.0)) or 0.0),
                "confidence": float(cue.get("confidence", 0.0) or 0.0),
                "source_reason": cue.get("source_reason", ""),
            }
        )
    return {
        "schema": "helix.snowman_band.timing_intelligence.v1",
        "purpose": "structured timing data for lyrics, phonemes, face definitions, performer vocal routing, and xLights Faces translation",
        "lyric_timing_track": [
            {
                "text": line.text,
                "start_ms": int(round(line.start_time * 1000.0)),
                "end_ms": int(round(line.end_time * 1000.0)),
                "confidence": round(float(line.confidence), 3),
            }
            for line in lyric_timeline.lines
        ],
        "word_timing_track": [
            {
                "text": word.text,
                "start_ms": word.start_ms,
                "end_ms": word.end_ms,
                "confidence": round(float(word.confidence), 3),
            }
            for word in lyric_timeline.words
        ],
        "phoneme_timing_track": [
            {
                "phoneme": event.phoneme,
                "mouth_shape": event.mouth_shape,
                "mouth_submodel": event.mouth_submodel,
                "start_ms": event.start_ms,
                "end_ms": event.end_ms,
                "confidence": round(float(event.confidence), 3),
                "word_text": event.word_text,
                "source": event.source,
            }
            for event in lyric_timeline.phoneme_events
        ],
        "face_definitions": face_definitions,
        "performer_vocal_routes": [
            {
                "performer": window.get("performer"),
                "vocal_role": window.get("role"),
                "start_ms": int(round(float(window.get("start_time", 0.0) or 0.0) * 1000.0)),
                "end_ms": int(round(float(window.get("end_time", 0.0) or 0.0) * 1000.0)),
                "confidence": window.get("confidence"),
                "source_reason": window.get("source_reason"),
            }
            for window in background_windows
        ],
        "faces_effect_instructions": faces_effect_instructions,
        "song_part_markers": [
            {
                "name": part.name,
                "start_ms": part.start_ms,
                "end_ms": part.end_ms,
                "confidence": part.confidence,
                "energy_level": part.energy_level,
                "dominant_sources": part.dominant_sources,
                "repetition_signature": part.repetition_signature,
            }
            for part in song_parts
        ],
        "part_hit_markers": [
            {
                "timestamp_ms": hit.start_ms,
                "part_name": hit.part_name,
                "hit_type": hit.hit_type,
                "strength": hit.strength,
                "confidence": hit.confidence,
                "source_reason": hit.source_reason,
            }
            for hit in part_hits
        ],
    }


def _face_target_for_instruction(cue: Mapping[str, Any], face_routing: Mapping[str, Any]) -> str:
    performer = str(cue.get("performer", "") or "")
    start_ms = int(cue.get("start_ms", 0) or 0)
    lead_cycle = list(face_routing.get("lead_cycle", []) or [])
    support_faces = list(face_routing.get("support_faces", []) or [])
    lyric_surfaces = list(face_routing.get("lyric_surfaces", []) or [])
    if performer == "lead_singer":
        if lead_cycle:
            return str(lead_cycle[(start_ms // 100) % len(lead_cycle)])
        return str(face_routing.get("preferred_lead", "") or "")
    if performer in {"guitarist", "bassist"} and support_faces:
        offset = 0 if performer == "guitarist" else 1
        return str(support_faces[((start_ms // 100) + offset) % len(support_faces)])
    if performer == "drummer" and support_faces:
        return str(support_faces[-1])
    if lyric_surfaces:
        return str(lyric_surfaces[(start_ms // 100) % len(lyric_surfaces)])
    return ""


def _build_sequence_face_instructions(
    *,
    faces_effect_instructions: list[dict[str, Any]],
    face_routing: Mapping[str, Any],
) -> list[dict[str, Any]]:
    instructions: list[dict[str, Any]] = []
    for instruction in faces_effect_instructions:
        target = _face_target_for_instruction(instruction, face_routing)
        start_ms = int(instruction.get("start_ms", 0) or 0)
        end_ms = int(instruction.get("end_ms", 0) or 0)
        if not target or end_ms <= start_ms:
            continue
        performer = str(instruction.get("performer", "") or "face")
        vocal_role = str(instruction.get("vocal_role", "") or "face")
        mouth_shape = str(instruction.get("mouth_shape", "") or "mouth_A")
        timing_track = str(instruction.get("timing_track", "face_timing") or "face_timing")
        instructions.append(
            {
                "schema": "helix.snowman_band.sequence_effect_instruction.v1",
                "target_model": target,
                "effect": "Faces",
                "fallback_effect": "On",
                "label": f"snowman_{performer}_{vocal_role}",
                "timing_track": timing_track,
                "timing_label": f"{performer}:{vocal_role}:{mouth_shape}",
                "start_ms": start_ms,
                "end_ms": end_ms,
                "performer": performer,
                "vocal_role": vocal_role,
                "face_definition": instruction.get("face_definition", ""),
                "mouth_shape": mouth_shape,
                "mouth_submodel": instruction.get("mouth_submodel", ""),
                "phoneme": instruction.get("phoneme", ""),
                "intensity": instruction.get("intensity", 0.0),
                "confidence": instruction.get("confidence", 0.0),
                "source_reason": instruction.get("source_reason", ""),
            }
        )
    instructions.sort(key=lambda item: (int(item["start_ms"]), int(item["end_ms"]), str(item["target_model"])))
    return instructions


def build_snowman_band_plan(
    *,
    parsed_layout: Any,
    parts: list[Any],
    lyric_events: list[Any],
    note_events: list[Any],
    beat_ms: list[int],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    build_lifts: list[int],
    releases: list[int],
    chronoflow_payload: Mapping[str, Any] | None = None,
    band_sync_payload: Mapping[str, Any] | None = None,
    multiband: Any = None,
    enable_lyrics: bool = True,
    background_vocal_events: list[Any] | None = None,
    drum_event_streams: dict[str, list[Any]] | None = None,
) -> dict[str, Any]:
    layout_names = sorted(getattr(parsed_layout, "models", {}).keys()) if parsed_layout is not None else []
    face_routing = preferred_face_routing(layout_names)
    performers = _build_performer_catalog(face_routing)
    lyric_timeline = vt.build_lyric_timeline(lyric_events, vocal_peaks)
    song_parts = vt.build_song_parts(parts, vocal_peaks_ms=vocal_peaks, bass_peaks_ms=bass_peaks, drum_hits_ms=list(kicks) + list(snares) + list(hats))
    part_hits = vt.detect_part_hits(
        song_parts,
        lyric_timeline,
        vocal_peaks_ms=vocal_peaks,
        build_lifts_ms=build_lifts,
        releases_ms=releases,
    )
    routing_config = vt.VocalRoutingConfig()
    background_windows = vt.detect_background_vocal_windows(
        lyric_timeline,
        song_parts,
        vocal_peaks,
        routing_config,
        classifier_events=background_vocal_events,
    )
    singer_cues, tunnel_overlays = _build_singer_cues(
        lyric_events,
        face_routing=face_routing,
        parts=parts,
        enable_lyrics=enable_lyrics,
    )
    bass_cues, guitar_cues, string_realism_debug = _build_string_realism_cues(
        parts,
        bass_peaks,
        note_events,
        beat_ms,
        band_sync_payload,
    )
    if drum_event_streams:
        drum_cues, kit_components, drum_intelligence_debug = _build_intelligent_drum_cues(
            parts,
            drum_event_streams=drum_event_streams,
            kicks=kicks,
            snares=snares,
            hats=hats,
            releases=releases,
        )
    else:
        drum_cues, kit_components = _build_drum_cues(parts, kicks, snares, hats, releases)
        drum_intelligence_debug = {"fallback_mode": "legacy_marks", "counts": {}, "motion_events": [], "effect_cues": [], "mapping": []}
    background_vocals = _build_background_vocals(vocal_peaks, parts)
    vocal_emotion_payload = vocal_emotion.build_vocal_emotion_timeline(
        lyric_timeline=lyric_timeline,
        song_parts=song_parts,
        vocal_peaks_ms=vocal_peaks,
        multiband=multiband,
    )
    lead_face_activations = _build_lead_face_activations(lyric_timeline, song_parts) if enable_lyrics else []
    lead_face_activations, lead_emotion_logs = vocal_emotion.apply_emotion_to_face_cues(
        lead_face_activations,
        vocal_emotion_payload,
    )
    background_face_activations = _build_background_face_activations(
        lyric_timeline,
        song_parts,
        background_windows,
        config=routing_config,
        note_events=note_events,
        bass_peaks=bass_peaks,
    )
    background_face_activations, background_emotion_logs = vocal_emotion.apply_emotion_to_face_cues(
        background_face_activations,
        vocal_emotion_payload,
    )
    part_hit_reactions = _build_part_hit_reactions(part_hits)
    part_hit_reactions, part_hit_emotion_logs = vocal_emotion.apply_emotion_to_face_cues(
        part_hit_reactions,
        vocal_emotion_payload,
    )
    face_activations = lead_face_activations + background_face_activations + part_hit_reactions
    total_cues = len(singer_cues) + len(bass_cues) + len(guitar_cues) + len(drum_cues) + len(background_vocals) + len(face_activations)
    chronoflow_debug = dict((chronoflow_payload or {}).get("debug", {}) or {})
    band_sync_frames = list((band_sync_payload or {}).get("state_frames", []) or [])
    tempo_bpm = float(getattr(multiband, "tempo_bpm", 0.0) or 0.0)
    global_timeline = {
        "lyric_words": vt.as_plain_dict(lyric_timeline.words),
        "lyric_lines": vt.as_plain_dict(lyric_timeline.lines),
        "phoneme_events": vt.as_plain_dict(lyric_timeline.phoneme_events),
        "vocal_role_events": background_windows,
        "song_parts": vt.as_plain_dict(song_parts),
        "part_hits": vt.as_plain_dict(part_hits),
        "vocal_emotion_events": list(vocal_emotion_payload.get("events", []) or []),
        "face_activation_events": face_activations,
        "face_timing_events": face_activations,
        "performer_emphasis_events": [cue for cue in part_hit_reactions if cue.get("role") == "part_hit_reaction"],
    }
    timing_intelligence = _build_timing_intelligence(
        lyric_timeline=lyric_timeline,
        song_parts=song_parts,
        part_hits=part_hits,
        performers=performers,
        face_events=face_activations,
        background_windows=background_windows,
    )
    sequence_face_instructions = _build_sequence_face_instructions(
        faces_effect_instructions=timing_intelligence["faces_effect_instructions"],
        face_routing=face_routing,
    )
    xlights_translation = {
        "lyric_timing_tracks": timing_intelligence["lyric_timing_track"],
        "phoneme_timing_tracks": timing_intelligence["phoneme_timing_track"],
        "faces_effect_placements": timing_intelligence["faces_effect_instructions"],
        "sequence_effect_instructions": sequence_face_instructions,
        "face_definition_assignments": timing_intelligence["face_definitions"],
        "background_vocal_face_metadata": {
            "thresholds": vt.as_plain_dict(routing_config),
            "max_intensity": routing_config.background_face_max_intensity,
        },
        "song_part_timing_markers": timing_intelligence["song_part_markers"],
        "emotion_palette_timeline": [
            {
                "start_ms": event.get("start_ms"),
                "end_ms": event.get("end_ms"),
                "emotion_type": event.get("emotion_type"),
                "palette": vocal_emotion_payload.get("palettes", {}).get(str(event.get("emotion_type")), {}).get("palette", "balanced_white"),
                "brightness": round(0.18 + float(event.get("intensity", 0.0) or 0.0) * 0.76, 3),
                "motion_style": vocal_emotion_payload.get("palettes", {}).get(str(event.get("emotion_type")), {}).get("motion_style", "steady"),
            }
            for event in list(vocal_emotion_payload.get("events", []) or [])
        ],
    }
    debug_timeline = _debug_timeline(lyric_timeline, song_parts, part_hits, face_activations, background_windows)
    emotion_face_logs = lead_emotion_logs + background_emotion_logs + part_hit_emotion_logs
    return {
        "enabled": True,
        "version": "snowman_band_v2_vocal_timeline",
        "face_routing": face_routing,
        "performers": performers,
        "vocal_routing": {
            "priority": [
                "lead_vocal_to_lead_singer",
                "background_vocal_to_guitarist_or_bassist",
                "group_chant_to_all_vocalist_faces",
                "uncertain_vocal_energy_to_lead_only",
            ],
            "thresholds": vt.as_plain_dict(routing_config),
            "background_windows": background_windows,
        },
        "band_sync": {
            "schema": (band_sync_payload or {}).get("schema", ""),
            "state_frames": band_sync_frames,
            "performer_focus": list((band_sync_payload or {}).get("performer_focus", []) or []),
            "energy_distributions": list((band_sync_payload or {}).get("energy_distributions", []) or []),
            "coordination_note": "Snowman performer intensities should be interpreted through these shared band-state frames.",
        },
        "song_part_behavior": {
            "verse": "lead singer active; background faces stay quiet unless harmony confidence passes threshold",
            "chorus": "lead full intensity; guitarist and bassist background faces may activate at subordinate intensity",
            "bridge": "motion reduced unless vocals dominate; faces become more expressive for lyric-heavy spans",
            "breakdown_drop": "drummer and environment can lead; singer reduces unless a vocal hit exists",
            "outro": "mouth and performer intensity fade softer",
            "part_hit": "lead phoneme emphasis, brief guitarist/bassist reaction, drummer cheer face, instrument and spatial pulse metadata",
        },
        "kit": {
            "components": kit_components,
            "beat_anchor_count": len(beat_ms),
            "release_count": len(releases),
            "build_count": len(build_lifts),
            "drum_intelligence": drum_intelligence_debug,
            "string_instrument_realism": string_realism_debug,
            "vocal_emotion": vocal_emotion_payload,
        },
        "layout_mapping": {
            "lead_singer": {"family": "talking_heads", "targets": performers["lead_singer"]["preferred_targets"]},
            "bassist": {"family": "vertical_props", "targets": performers["bassist"]["preferred_targets"]},
            "guitarist": {"family": "arches", "targets": performers["guitarist"]["preferred_targets"]},
            "drummer": {"family": "percussion_props", "targets": performers["drummer"]["preferred_targets"]},
        },
        "visualizer_overlay": {
            "lyrics_enabled": bool(enable_lyrics),
            "soundtunnel_lyrics": tunnel_overlays,
            "style": "reverse_causality_spiral_tunnel",
        },
        "cues": {
            "lead_singer": singer_cues,
            "background_vocals": background_vocals,
            "lead_face_activations": lead_face_activations,
            "background_face_activations": background_face_activations,
            "part_hit_reactions": part_hit_reactions,
            "bassist": bass_cues,
            "guitarist": guitar_cues,
            "drummer": drum_cues,
        },
        "global_timeline": global_timeline,
        "timing_intelligence": timing_intelligence,
        "xlights_translation": xlights_translation,
        "debug_timeline": debug_timeline,
        "emotion": {
            "schema": vocal_emotion_payload.get("schema", "helix.vocal_emotion.v1"),
            "timeline": list(vocal_emotion_payload.get("events", []) or []),
            "palettes": vocal_emotion_payload.get("palettes", {}),
            "face_intensity_logs": emotion_face_logs,
            "integration_hooks": {
                "band_sync": "emotion intensity is layered onto performer state after band focus scaling",
                "effect_scoring": "face cues carry effect_scoring_hint with emotion brightness and motion style",
                "spatial": "face cues carry spatial_emotion_hint for center glow/support washes",
            },
        },
        "debug": {
            "tempo_bpm": round(tempo_bpm, 3),
            "total_cue_count": total_cues,
            "lyric_cues": len(singer_cues),
            "lyric_words": len(lyric_timeline.words),
            "phoneme_events": len(lyric_timeline.phoneme_events),
            "song_parts": len(song_parts),
            "part_hits": len(part_hits),
            "face_activation_events": len(face_activations),
            "bass_cues": len(bass_cues),
            "guitar_cues": len(guitar_cues),
            "drum_cues": len(drum_cues),
            "drum_intelligence_mode": drum_intelligence_debug.get("fallback_mode", "legacy_marks"),
            "guitar_realism_mode": string_realism_debug["guitar"].get("fallback_mode", ""),
            "bass_realism_mode": string_realism_debug["bass"].get("fallback_mode", ""),
            "string_realism_events": int(string_realism_debug["guitar"].get("event_count", 0) or 0)
            + int(string_realism_debug["bass"].get("event_count", 0) or 0),
            "vocal_emotion_events": int((vocal_emotion_payload.get("debug", {}) or {}).get("event_count", 0) or 0),
            "emotion_face_logs": len(emotion_face_logs),
            "background_vocal_cues": len(background_vocals),
            "soundtunnel_lyric_hits": len(tunnel_overlays),
            "chronoflow_event_count": int(chronoflow_debug.get("event_count", 0) or 0),
            "band_sync_frames": len(band_sync_frames),
        },
    }


def build_timing_track(payload: Mapping[str, Any], limit: int = 1800) -> list[tuple[str, int, int]]:
    xlights_translation = dict(payload.get("xlights_translation", {}) or {})
    sequence_instructions = list(xlights_translation.get("sequence_effect_instructions", []) or [])
    if sequence_instructions:
        out = [
            (
                str(instruction.get("timing_label") or instruction.get("label") or "snowman:face"),
                int(instruction.get("start_ms", 0) or 0),
                int(instruction.get("end_ms", 0) or 0),
            )
            for instruction in sequence_instructions
            if int(instruction.get("end_ms", 0) or 0) > int(instruction.get("start_ms", 0) or 0)
        ]
        out.sort(key=lambda item: (item[1], item[2], item[0]))
        return out[: max(0, int(limit))]

    cues = dict(payload.get("cues", {}) or {})
    out: list[tuple[str, int, int]] = []

    for cue in list(cues.get("lead_singer", []) or []):
        out.append((f"vox:{cue.get('viseme', 'REST')}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("bassist", []) or []):
        out.append((f"bass:s{int(cue.get('string_index', 1))}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("guitarist", []) or []):
        out.append((f"gtr:n{int(cue.get('neck_position', 1))}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("drummer", []) or []):
        out.append((f"drm:{str(cue.get('kind', 'hit'))}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("background_vocals", []) or []):
        performer = str(cue.get("performer", "bgv"))
        label = "bgv:bass" if performer == "bassist" else "bgv:gtr"
        out.append((label, int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("lead_face_activations", []) or []):
        out.append((f"face:lead:{cue.get('mouth_shape', 'mouth_A')}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("background_face_activations", []) or []):
        performer = str(cue.get("performer", "bgv"))
        out.append((f"face:{performer}:bg:{cue.get('mouth_shape', 'mouth_A')}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))
    for cue in list(cues.get("part_hit_reactions", []) or []):
        out.append((f"hit:{cue.get('performer', 'band')}:{cue.get('hit_type', 'part')}", int(cue.get("start_ms", 0)), int(cue.get("end_ms", 0))))

    out.sort(key=lambda item: (item[1], item[2], item[0]))
    return out[: max(0, int(limit))]


def write_export_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
