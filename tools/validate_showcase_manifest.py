#!/usr/bin/env python3
"""Validate six distinct Helix pilot deliverables and their MP4 media."""
import argparse
import json
from pathlib import Path
from validate_showcase_mp4 import validate

REQUIRED = {"percussion_snowmen", "christmas_mallets", "rock_guitar",
            "vocal_snowmen", "integrated_3d", "six_layout_comparison"}

def check_manifest(manifest_path):
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    pilots = data.get("pilots", [])
    errors = []
    ids = [p.get("id") for p in pilots]
    if len(ids) != 6 or set(ids) != REQUIRED or len(set(ids)) != 6:
        errors.append("Exactly six unique required pilot IDs are needed")
    results = []
    for p in pilots:
        for key in ("id", "audio_source", "excerpt_start_seconds", "video"):
            if key not in p:
                errors.append(f"{p.get('id', '?')}: missing {key}")
        if "video" not in p:
            continue
        video = Path(manifest_path).parent / p["video"]
        result = validate(video)
        result["pilot_id"] = p.get("id")
        results.append(result)
        if not result["passed"]:
            errors.append(f"{p.get('id')}: MP4 failed validation")
    return {"passed": not errors, "errors": errors, "videos": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = check_manifest(args.manifest)
    output = json.dumps(result, indent=2)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
