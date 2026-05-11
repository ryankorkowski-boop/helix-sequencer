from __future__ import annotations

from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring

from core.band_vocal_face_export import VocalPhonemeTiming


class XSQSequence:
    def __init__(
        self,
        *,
        sequence_name: str,
        model_name: str,
        xml_text: str,
    ) -> None:
        self.sequence_name = sequence_name
        self.model_name = model_name
        self.xml_text = xml_text



def emit_xsq_sequence(
    *,
    timings: List[VocalPhonemeTiming],
    sequence_name: str,
    model_name: str,
) -> XSQSequence:
    """
    Emit a deterministic XSQ-compatible XML skeleton.

    v1 goals:
    - Stable XML ordering
    - Timing preservation
    - Intensity preservation
    - Face timing entries
    - Placeholder effect blocks
    - Deterministic output
    """

    root = Element("xsequence")
    root.set("name", sequence_name)
    root.set("model", model_name)

    timing_track = SubElement(root, "timingtrack")
    timing_track.set("name", "HelixVocalTrack")

    effects = SubElement(root, "effects")

    ordered = sorted(
        timings,
        key=lambda t: (t.start, t.performer, t.phoneme),
    )

    for idx, timing in enumerate(ordered):
        entry = SubElement(timing_track, "phoneme")
        entry.set("index", str(idx))
        entry.set("performer", timing.performer)
        entry.set("phoneme", timing.phoneme)
        entry.set("start", f"{timing.start:.6f}")
        entry.set("duration", f"{timing.duration:.6f}")
        entry.set("intensity", f"{timing.intensity:.4f}")

        effect = SubElement(effects, "effect")
        effect.set("index", str(idx))
        effect.set("type", "face")
        effect.set("start", f"{timing.start:.6f}")
        effect.set("duration", f"{timing.duration:.6f}")
        effect.set("phoneme", timing.phoneme)

    xml_bytes = tostring(root, encoding="utf-8")
    xml_text = xml_bytes.decode("utf-8")

    return XSQSequence(
        sequence_name=sequence_name,
        model_name=model_name,
        xml_text=xml_text,
    )
