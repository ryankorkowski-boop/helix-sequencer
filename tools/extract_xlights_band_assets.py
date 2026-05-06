from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence


BAND_KEYWORDS = (
    "band",
    "singer",
    "singing",
    "vocal",
    "phoneme",
    "mouth",
    "bulb",
    "guitar",
    "bass",
    "drum",
    "drummer",
    "snowman",
)

PHONEME_HINTS = ("AI", "E", "FV", "L", "MBP", "O", "REST", "U", "WQ", "MOUTH", "PHONEME")
TIMING_TAGS = ("TimingTrack", "timingTrack", "timing", "Timing")


def _norm(value: object) -> str:
    return str(value or "").strip()


def _lower(value: object) -> str:
    return _norm(value).lower()


def _name(el: ET.Element) -> str:
    return _norm(el.attrib.get("name") or el.attrib.get("Name"))


def _submodel_names(model: ET.Element) -> list[str]:
    names: list[str] = []
    for sub in list(model.findall(".//subModel")) + list(model.findall(".//SubModel")):
        name = _name(sub)
        if name:
            names.append(name)
    return list(dict.fromkeys(names))


def _matches_band_model(name: str, submodels: list[str]) -> bool:
    haystack = " ".join([name, *submodels]).lower()
    return any(keyword in haystack for keyword in BAND_KEYWORDS)


def _phoneme_submodels(submodels: list[str]) -> list[str]:
    out: list[str] = []
    for name in submodels:
        upper = name.upper().replace("-", "_").replace(" ", "_")
        if any(hint in upper for hint in PHONEME_HINTS):
            out.append(name)
    return list(dict.fromkeys(out))


def _classify_member(name: str, submodels: list[str]) -> str:
    haystack = " ".join([name, *submodels]).lower()
    if any(word in haystack for word in ("drum", "snare", "kick", "cymbal", "hihat", "hi_hat")):
        return "snowman_drummer"
    if "bass" in haystack:
        return "snowman_bassist"
    if "guitar" in haystack or "slash" in haystack:
        return "snowman_guitarist"
    if any(word in haystack for word in ("female", "harmony")):
        return "snowman_singer_female"
    if any(word in haystack for word in ("singer", "singing", "vocal", "phoneme", "mouth", "bulb")):
        return "snowman_singer"
    return "unknown_band_member"


def extract_band_models(root: ET.Element) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for model in list(root.findall(".//model")) + list(root.findall(".//Model")):
        name = _name(model)
        if not name:
            continue
        submodels = _submodel_names(model)
        if not _matches_band_model(name, submodels):
            continue
        phonemes = _phoneme_submodels(submodels)
        candidates.append(
            {
                "name": name,
                "member_hint": _classify_member(name, submodels),
                "display_as": _norm(model.attrib.get("DisplayAs")),
                "start_channel": _norm(model.attrib.get("StartChannel")),
                "submodels": submodels,
                "phoneme_submodels": phonemes,
                "phoneme_capable": bool(phonemes),
            }
        )
    return candidates


def extract_band_groups(root: ET.Element) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in list(root.findall(".//modelGroup")) + list(root.findall(".//ModelGroup")):
        name = _name(group)
        members = _norm(group.attrib.get("models") or group.attrib.get("Models"))
        haystack = f"{name} {members}".lower()
        if not any(keyword in haystack for keyword in BAND_KEYWORDS):
            continue
        groups.append(
            {
                "name": name,
                "members": [item.strip() for item in members.split(",") if item.strip()],
            }
        )
    return groups


def extract_timing_tracks(root: ET.Element) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in TIMING_TAGS and "timing" not in tag.lower():
            continue
        name = _name(el) or _norm(el.attrib.get("label") or el.attrib.get("Label"))
        if not name:
            continue
        key = f"{tag}:{name}"
        if key in seen:
            continue
        seen.add(key)
        lower_name = name.lower()
        tracks.append(
            {
                "name": name,
                "tag": tag,
                "member_hint": _classify_member(name, []),
                "band_related": any(keyword in lower_name for keyword in BAND_KEYWORDS),
                "attributes": dict(el.attrib),
            }
        )
    return tracks


def extract_xlights_band_assets(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    models = extract_band_models(root)
    groups = extract_band_groups(root)
    timing_tracks = extract_timing_tracks(root)
    return {
        "schema": "helixville4.xlights_band_asset_extract.v1",
        "source_file": str(path),
        "model_count": len(models),
        "group_count": len(groups),
        "timing_track_count": len(timing_tracks),
        "models": models,
        "groups": groups,
        "timing_tracks": timing_tracks,
        "band_related_timing_tracks": [track for track in timing_tracks if track["band_related"]],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Helixville band models, singing bulbs, submodels, and timing-track names from xLights XML."
    )
    parser.add_argument("xml", type=Path, help="Path to xlights_rgbeffects.xml, .xbkp, .xsq, or related XML")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = extract_xlights_band_assets(args.xml)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
