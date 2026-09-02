from __future__ import annotations

from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring

from core.band_vocal_face_export import VocalPhonemeTiming


class XSQSequence:
    def __init__(self, *, sequence_name: str, model_name: str, xml_text: str) -> None:
        self.sequence_name = sequence_name
        self.model_name = model_name
        self.xml_text = xml_text


def emit_xsq_sequence(
    *,
    timings: List[VocalPhonemeTiming],
    sequence_name: str,
    model_name: str,
) -> XSQSequence:
    """Emit a deterministic synthetic XSQ with validator-compatible elements."""
    root = Element("xsequence", {"name": sequence_name, "model": model_name})
    timing_track = SubElement(root, "timingtrack", {"name": "HelixVocalTrack"})
    effects = SubElement(root, "effects")
    element_effects = SubElement(root, "ElementEffects")

    ordered = sorted(timings, key=lambda t: (t.start, t.performer, t.phoneme))
    for idx, timing in enumerate(ordered):
        entry = SubElement(timing_track, "phoneme", {
            "index": str(idx),
            "performer": timing.performer,
            "phoneme": timing.phoneme,
            "start": f"{timing.start:.6f}",
            "duration": f"{timing.duration:.6f}",
            "intensity": f"{timing.intensity:.4f}",
        })

        SubElement(effects, "effect", {
            "index": str(idx),
            "type": "face",
            "start": entry.attrib["start"],
            "duration": entry.attrib["duration"],
            "phoneme": timing.phoneme,
        })

        # Keep the legacy synthetic effect plus the Element form expected by
        # the current validator/preview stack. This is intentionally
        # channel-neutral and does not claim a physical electrical mapping.
        SubElement(element_effects, "Element", {
            "name": model_name,
            "effectIndex": str(idx),
            "type": "face",
            "start": entry.attrib["start"],
            "duration": entry.attrib["duration"],
            "intensity": entry.attrib["intensity"],
        })

    xml_text = tostring(root, encoding="utf-8").decode("utf-8")
    return XSQSequence(sequence_name=sequence_name, model_name=model_name, xml_text=xml_text)
