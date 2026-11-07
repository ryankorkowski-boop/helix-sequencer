"""Build non-destructive vocal targets from discovered xLights Faces definitions."""
from __future__ import annotations

from dataclasses import dataclass

from core.singing_face_discovery import SingingFace

# Canonical xLights mouth groups. Never infer node ranges from model names.
PHONEME_ALIASES = {
    "A": ("AI", "A"),
    "E": ("E", "AI"),
    "I": ("AI", "I"),
    "O": ("O",),
    "U": ("U", "O"),
    "MBP": ("MBP",),
    "FV": ("FV",),
    "L": ("L",),
    "WQ": ("WQ", "U"),
    "REST": ("REST", "OFF"),
}


@dataclass(frozen=True)
class VocalTarget:
    model: str
    face_definition: str
    phoneme_keys: dict[str, str]
    unresolved: tuple[str, ...]


def _mouth_key(key: str) -> str | None:
    normalized = key.upper().replace("_", "-").replace(" ", "")
    if normalized.startswith("MOUTH-"):
        return normalized[6:]
    return None


def route_singing_faces(faces: list[SingingFace]) -> list[VocalTarget]:
    """Resolve phoneme-to-existing-face-attribute routing, without editing XML.

    Return unresolved phonemes explicitly so the sequence exporter can choose a
    supported fallback instead of silently outputting incorrect channel data.
    """
    targets = []
    for face in faces:
        mouth_attrs = {_mouth_key(k): k for k, v in face.mappings.items()
                       if _mouth_key(k) is not None and v.strip()}
        if not mouth_attrs:
            continue
        resolved = {}
        missing = []
        for phoneme, aliases in PHONEME_ALIASES.items():
            match = next((mouth_attrs[alias] for alias in aliases if alias in mouth_attrs), None)
            if match:
                resolved[phoneme] = match
            else:
                missing.append(phoneme)
        targets.append(VocalTarget(face.model, face.name, resolved, tuple(missing)))
    return targets
