from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping


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
                "pixel": ["mouth_closed", "mouth_ah", "mouth_ee", "mouth_oh", "lyric_text_hold"],
                "ac_rgbw": ["mouth_closed", "mouth_open_small", "mouth_open_mid", "mouth_open_wide"],
                "matrix": ["viseme_closed", "viseme_ah", "viseme_ee", "viseme_oh", "lyric_word"],
            },
        },
        "bassist": {
            "display_name": "Standup Bass Snowman",
            "role": "bassist",
            "preferred_targets": ["vertical_props", "trees", "columns"],
            "modes": {
                "pixel": ["string_lane_1", "string_lane_2", "string_lane_3", "string_lane_4", "head_bob"],
                "ac_rgbw": ["string_low", "string_lowmid", "string_highmid", "string_high", "body_bob"],
                "matrix": ["bass_lane_1", "bass_lane_2", "bass_lane_3", "bass_lane_4", "fret_position"],
            },
        },
        "guitarist": {
            "display_name": "Guitar Snowman",
            "role": "guitarist",
            "preferred_targets": ["arches", "directional_props", "matrices"],
            "modes": {
                "pixel": ["strum_down", "strum_up", "neck_pos_1", "neck_pos_2", "neck_pos_3", "neck_pos_4"],
                "ac_rgbw": ["strum_frame_a", "strum_frame_b", "neck_low", "neck_mid", "neck_high"],
                "matrix": ["guitar_arc", "guitar_ribbon", "neck_tracker"],
            },
        },
        "drummer": {
            "display_name": "Drummer Snowman",
            "role": "drummer",
            "preferred_targets": ["percussion_props", "matrices", "circles"],
            "modes": {
                "pixel": ["kick_center", "kick_mid", "kick_outer", "snare_burst", "hat_flash", "cymbal_shimmer"],
                "ac_rgbw": ["kick_ring_1", "kick_ring_2", "kick_ring_3", "snare_hit", "hat_open", "cymbal_frame_1", "cymbal_frame_2", "cymbal_frame_3", "cymbal_frame_4"],
                "matrix": ["kick_wave", "snare_contact", "hat_plate", "cymbal_arc"],
            },
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


def _build_bass_cues(parts: list[Any], bass_peaks: list[int], note_events: list[Any]) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for hit_ms in bass_peaks:
        midis = _extract_note_midis(note_events, hit_ms)
        pitch_midi = min(midis) if midis else 43.0
        string_index = _string_index_for_pitch(pitch_midi)
        neck_position = _neck_position_for_pitch(pitch_midi)
        cues.append(
            {
                "performer": "bassist",
                "start_ms": int(hit_ms),
                "end_ms": int(hit_ms) + 180,
                "kind": "bass_slap",
                "section": _part_label(parts, int(hit_ms)),
                "string_index": string_index,
                "neck_position": neck_position,
                "pitch_midi": round(float(pitch_midi), 2),
                "head_bob": True,
            }
        )
    return cues


def _build_guitar_cues(parts: list[Any], note_events: list[Any]) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    for event in note_events:
        start_ms = _event_start_ms(event)
        end_ms = _event_end_ms(event, fallback_ms=180)
        midis: list[float] = []
        for note in list(getattr(event, "notes", []) or []):
            if isinstance(note, (list, tuple)) and note:
                try:
                    midis.append(float(note[0]))
                except (TypeError, ValueError):
                    continue
        if not midis:
            continue
        pitch_midi = max(midis)
        cues.append(
            {
                "performer": "guitarist",
                "start_ms": start_ms,
                "end_ms": end_ms,
                "kind": "strum",
                "section": _part_label(parts, start_ms),
                "neck_position": _neck_position_for_pitch(pitch_midi),
                "pitch_midi": round(float(pitch_midi), 2),
                "headbang": _part_label(parts, start_ms) in {"CHORUS", "DROP"},
            }
        )
    return cues


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
    multiband: Any = None,
    enable_lyrics: bool = True,
) -> dict[str, Any]:
    layout_names = sorted(getattr(parsed_layout, "models", {}).keys()) if parsed_layout is not None else []
    face_routing = preferred_face_routing(layout_names)
    performers = _build_performer_catalog(face_routing)
    singer_cues, tunnel_overlays = _build_singer_cues(
        lyric_events,
        face_routing=face_routing,
        parts=parts,
        enable_lyrics=enable_lyrics,
    )
    bass_cues = _build_bass_cues(parts, bass_peaks, note_events)
    guitar_cues = _build_guitar_cues(parts, note_events)
    drum_cues, kit_components = _build_drum_cues(parts, kicks, snares, hats, releases)
    background_vocals = _build_background_vocals(vocal_peaks, parts)
    total_cues = len(singer_cues) + len(bass_cues) + len(guitar_cues) + len(drum_cues) + len(background_vocals)
    chronoflow_debug = dict((chronoflow_payload or {}).get("debug", {}) or {})
    tempo_bpm = float(getattr(multiband, "tempo_bpm", 0.0) or 0.0)
    return {
        "enabled": True,
        "version": "snowman_band_v1",
        "face_routing": face_routing,
        "performers": performers,
        "kit": {
            "components": kit_components,
            "beat_anchor_count": len(beat_ms),
            "release_count": len(releases),
            "build_count": len(build_lifts),
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
            "bassist": bass_cues,
            "guitarist": guitar_cues,
            "drummer": drum_cues,
        },
        "debug": {
            "tempo_bpm": round(tempo_bpm, 3),
            "total_cue_count": total_cues,
            "lyric_cues": len(singer_cues),
            "bass_cues": len(bass_cues),
            "guitar_cues": len(guitar_cues),
            "drum_cues": len(drum_cues),
            "background_vocal_cues": len(background_vocals),
            "soundtunnel_lyric_hits": len(tunnel_overlays),
            "chronoflow_event_count": int(chronoflow_debug.get("event_count", 0) or 0),
        },
    }


def build_timing_track(payload: Mapping[str, Any], limit: int = 1800) -> list[tuple[str, int, int]]:
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

    out.sort(key=lambda item: (item[1], item[2], item[0]))
    return out[: max(0, int(limit))]


def write_export_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
