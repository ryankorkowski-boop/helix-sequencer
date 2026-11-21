"""Prop-specific mouth-shape adapters; vocal timing is independent of display geometry.

A single singer's aligned phoneme events can be rendered on multiple face styles.
Custom mappings are explicit and validated rather than silently producing REST.
"""
from __future__ import annotations

from collections.abc import Mapping
from models.helixville4_vocal_phonemes import PHONEME_NAMES, singer_phoneme_submodel, female_singer_phoneme_submodel

# Canonical seven phonemes are the current Helix contract. A face can supply
# its own shape identifiers without changing the singer's timing track.
CANONICAL = frozenset(PHONEME_NAMES)
FACE_STYLES = {
    "coro": {p: p for p in PHONEME_NAMES},
    "pixel": {p: "MOUTH_" + p for p in PHONEME_NAMES},
    "singing_tree": {p: "TREE_MOUTH_" + p for p in PHONEME_NAMES},
    "snowman_lead": {p: singer_phoneme_submodel(p) for p in PHONEME_NAMES},
    "snowman_harmony": {p: female_singer_phoneme_submodel(p) for p in PHONEME_NAMES},
}

def resolve_face_mapping(style: str, custom: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a complete mapping or raise, never guess a missing mouth shape."""
    if custom is None:
        if style not in FACE_STYLES:
            raise ValueError(f"Unknown singing-face style: {style}")
        mapping = FACE_STYLES[style]
    else:
        mapping = custom
    if set(mapping) != CANONICAL:
        raise ValueError(f"Face mapping must define exactly {sorted(CANONICAL)}")
    if any(not isinstance(v, str) or not v.strip() for v in mapping.values()):
        raise ValueError("Face shape identifiers must be nonempty strings")
    return dict(mapping)

def render_phoneme_events(events, *, style: str, custom: Mapping[str, str] | None = None):
    """Map event phonemes to geometry while preserving all other event fields.

    Events: mappings containing 'phoneme', e.g. singer_id/start/end/confidence.
    The original list and events are never modified.
    """
    mapping = resolve_face_mapping(style, custom)
    output = []
    for event in events:
        phoneme = event["phoneme"]
        if phoneme not in mapping:
            raise ValueError(f"Unsupported phoneme: {phoneme}")
        output.append({**event, "mouth_shape": mapping[phoneme]})
    return output
