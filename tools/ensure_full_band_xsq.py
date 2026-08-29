from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


PERFORMER_MODELS = {
    "bassist": "HX_SNOWMAN_BASSIST",
    "guitarist": "HX_SNOWMAN_GUITARIST",
    "drummer": "HX_SNOWMAN_DRUMMER",
    "lead_singer": "HX_SNOWMAN_SINGER",
    "female_singer": "HX_SNOWMAN_SINGER_FEMALE",
}


def _target_for_cue(performer: str, cue: dict) -> str:
    model = PERFORMER_MODELS[performer]
    submodel = str(cue.get("submodel") or "").strip().lower()

    if performer == "bassist":
        suffix = {
            "pluck_zone": "HX_SNOWMAN_BASSIST_PLUCK_ZONE",
            "fret_zone": "HX_SNOWMAN_BASSIST_NECK_MID",
            "string_e": "HX_SNOWMAN_BASSIST_STRING_E",
            "string_a": "HX_SNOWMAN_BASSIST_STRING_A",
            "string_d": "HX_SNOWMAN_BASSIST_STRING_D",
            "string_g": "HX_SNOWMAN_BASSIST_STRING_G",
        }.get(submodel, "HX_SNOWMAN_BASSIST_BASS_BODY")
    elif performer == "guitarist":
        if submodel == "strum_zone":
            suffix = "HX_SNOWMAN_GUITARIST_PICK_ZONE"
        elif submodel == "fret_zone":
            neck = int(cue.get("neck_position") or 2)
            suffix = {
                1: "HX_SNOWMAN_GUITARIST_FRETBOARD_LOW",
                2: "HX_SNOWMAN_GUITARIST_FRETBOARD_MID",
                3: "HX_SNOWMAN_GUITARIST_FRETBOARD_HIGH",
            }.get(neck, "HX_SNOWMAN_GUITARIST_FRETBOARD_MID")
        else:
            suffix = "HX_SNOWMAN_GUITARIST_GUITAR_BODY"
    elif performer == "drummer":
        suffix = {
            "kick": "HX_SNOWMAN_DRUMMER_KICK",
            "snare": "HX_SNOWMAN_DRUMMER_SNARE",
            "tom": "HX_SNOWMAN_DRUMMER_TOM_LEFT",
            "hihat": "HX_SNOWMAN_DRUMMER_HI_HAT",
            "cymbal": "HX_SNOWMAN_DRUMMER_CYMBAL_LEFT",
            "drum_bus": "HX_SNOWMAN_DRUMMER_TORSO",
        }.get(submodel, "HX_SNOWMAN_DRUMMER_TORSO")
    elif performer == "lead_singer":
        suffix = {
            "mouth": "HX_SNOWMAN_SINGER_MOUTH",
            "mouth_a": "HX_SNOWMAN_SINGER_MOUTH_AH",
            "mouth_e": "HX_SNOWMAN_SINGER_MOUTH_EE",
            "mouth_o": "HX_SNOWMAN_SINGER_MOUTH_OH",
        }.get(submodel, "HX_SNOWMAN_SINGER_VOCAL_GLOW")
    else:
        suffix = "HX_SNOWMAN_SINGER_FEMALE_STAGE_GLOW"

    return f"{model}/{suffix}"


def _append_effect(element: ET.Element, start_ms: int, end_ms: int) -> None:
    layer = element.find("EffectLayer")
    if layer is None:
        layer = ET.SubElement(element, "EffectLayer")
        layer.set("collapsed", "0")
    ET.SubElement(
        layer,
        "Effect",
        {
            "ref": "0",
            "name": "On",
            "startTime": str(max(0, int(start_ms))),
            "endTime": str(max(int(start_ms) + 1, int(end_ms))),
            "palette": "0",
        },
    )


def ensure_band(xsq_path: Path, band_json: Path) -> dict[str, int]:
    tree = ET.parse(xsq_path)
    root = tree.getroot()
    effects_root = root.find("ElementEffects")
    if effects_root is None:
        raise RuntimeError("XSQ has no ElementEffects block")

    payload = json.loads(band_json.read_text(encoding="utf-8"))
    added: dict[str, int] = {key: 0 for key in PERFORMER_MODELS}

    elements = {
        element.attrib.get("name"): element
        for element in effects_root.findall("Element")
        if element.attrib.get("name")
    }

    def add(performer: str, cue: dict) -> None:
        start = cue.get("start_ms")
        end = cue.get("end_ms")
        if start is None or end is None or int(end) <= int(start):
            return
        target = _target_for_cue(performer, cue)
        element = elements.get(target)
        if element is None:
            element = ET.SubElement(effects_root, "Element", {"type": "model", "name": target})
            elements[target] = element
        _append_effect(element, int(start), int(end))
        added[performer] += 1

    cues = payload.get("cues", {})
    for performer in ("bassist", "guitarist", "drummer"):
        for cue in cues.get(performer, []):
            if isinstance(cue, dict):
                add(performer, cue)

    # Lead singer and female singer share the major performer-hit timeline so
    # both vocalists are visibly represented even when lyric transcription is
    # unavailable.
    for cue in cues.get("part_hit_reactions", []):
        if not isinstance(cue, dict):
            continue
        if cue.get("performer") == "lead_singer":
            add("lead_singer", cue)
            add("female_singer", cue)

    tree.write(xsq_path, encoding="utf-8", xml_declaration=True)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Write analyzed full snowman band cues into an XSQ.")
    parser.add_argument("xsq", type=Path)
    parser.add_argument("band_json", type=Path)
    args = parser.parse_args()
    result = ensure_band(args.xsq, args.band_json)
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"Total band cue effects added: {sum(result.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
