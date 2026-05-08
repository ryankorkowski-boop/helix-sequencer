from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from models.helixville4_band import HELIXVILLE4_BAND_MEMBERS


MEMBER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "snowman_singer": ("singer", "singing", "vocal", "phoneme", "mouth", "bulb", "steven", "tyler"),
    "snowman_singer_female": ("female", "harmony", "duet", "backup", "call_response"),
    "snowman_guitarist": ("guitar", "guitarist", "slash", "strum", "fret"),
    "snowman_bassist": ("bass", "bassist", "bassman", "claypool", "pluck"),
    "snowman_drummer": ("drum", "drummer", "kick", "snare", "cymbal", "hihat", "hi_hat", "tom", "moore"),
}


def _norm(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _member_ids() -> list[str]:
    return [member.member_id for member in HELIXVILLE4_BAND_MEMBERS]


def infer_member_id(text: object, fallback: str = "unknown_band_member") -> str:
    haystack = _norm(text)
    for member_id, keywords in MEMBER_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return member_id
    return fallback


def _merge_extracts(paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {"models": [], "groups": [], "timing_tracks": []}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        merged["models"].extend(item for item in payload.get("models", []) if isinstance(item, dict))
        merged["groups"].extend(item for item in payload.get("groups", []) if isinstance(item, dict))
        merged["timing_tracks"].extend(item for item in payload.get("timing_tracks", []) if isinstance(item, dict))
        merged["timing_tracks"].extend(
            item for item in payload.get("band_related_timing_tracks", []) if isinstance(item, dict)
        )
    return merged


def _dedupe_dicts(items: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = tuple(str(item.get(field, "")) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def build_integration_plan_from_extracts(paths: list[Path]) -> dict[str, Any]:
    merged = _merge_extracts(paths)
    models = _dedupe_dicts(merged["models"], ("name", "start_channel"))
    groups = _dedupe_dicts(merged["groups"], ("name",))
    timing_tracks = _dedupe_dicts(merged["timing_tracks"], ("name", "tag"))

    assignments: dict[str, dict[str, Any]] = {
        member_id: {
            "member_id": member_id,
            "discovered_models": [],
            "discovered_phoneme_submodels": [],
            "discovered_timing_tracks": [],
            "discovered_groups": [],
            "ready_for_layout_mapping": False,
            "ready_for_timing_mapping": False,
        }
        for member_id in _member_ids()
    }
    assignments["unknown_band_member"] = {
        "member_id": "unknown_band_member",
        "discovered_models": [],
        "discovered_phoneme_submodels": [],
        "discovered_timing_tracks": [],
        "discovered_groups": [],
        "ready_for_layout_mapping": False,
        "ready_for_timing_mapping": False,
    }

    for model in models:
        hint = str(model.get("member_hint") or "")
        member_id = hint if hint in assignments else infer_member_id(model.get("name"))
        bucket = assignments.get(member_id, assignments["unknown_band_member"])
        bucket["discovered_models"].append(
            {
                "name": model.get("name", ""),
                "display_as": model.get("display_as", ""),
                "start_channel": model.get("start_channel", ""),
                "submodels": list(model.get("submodels", []) or []),
                "phoneme_capable": bool(model.get("phoneme_capable", False)),
            }
        )
        bucket["discovered_phoneme_submodels"].extend(list(model.get("phoneme_submodels", []) or []))

    for track in timing_tracks:
        hint = str(track.get("member_hint") or "")
        member_id = hint if hint in assignments else infer_member_id(track.get("name"))
        bucket = assignments.get(member_id, assignments["unknown_band_member"])
        bucket["discovered_timing_tracks"].append(
            {
                "name": track.get("name", ""),
                "tag": track.get("tag", ""),
                "band_related": bool(track.get("band_related", False)),
            }
        )

    group_members_by_member: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        group_name = str(group.get("name", ""))
        members = list(group.get("members", []) or [])
        target_member = infer_member_id(" ".join([group_name, *members]))
        group_members_by_member[target_member].append({"name": group_name, "members": members})
    for member_id, group_items in group_members_by_member.items():
        assignments.get(member_id, assignments["unknown_band_member"])["discovered_groups"].extend(group_items)

    for bucket in assignments.values():
        bucket["discovered_phoneme_submodels"] = list(dict.fromkeys(bucket["discovered_phoneme_submodels"]))
        bucket["ready_for_layout_mapping"] = bool(bucket["discovered_models"] or bucket["discovered_groups"])
        bucket["ready_for_timing_mapping"] = bool(bucket["discovered_timing_tracks"])

    known_assignments = [assignments[member_id] for member_id in _member_ids()]
    unknown = assignments["unknown_band_member"]
    return {
        "schema": "helixville4.band_integration_plan.v1",
        "source_extracts": [str(path) for path in paths],
        "assignment_count": len(known_assignments),
        "assignments": known_assignments,
        "unknown": unknown,
        "summary": {
            "members_with_layout_sources": sum(1 for item in known_assignments if item["ready_for_layout_mapping"]),
            "members_with_timing_sources": sum(1 for item in known_assignments if item["ready_for_timing_mapping"]),
            "phoneme_source_members": [
                item["member_id"] for item in known_assignments if item["discovered_phoneme_submodels"]
            ],
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Helixville4 band integration plan from xLights extractor JSON files.")
    parser.add_argument("extracts", nargs="+", type=Path, help="JSON files from tools.extract_xlights_band_assets")
    parser.add_argument("--output", type=Path, default=None, help="Optional output JSON path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_integration_plan_from_extracts(list(args.extracts))
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
