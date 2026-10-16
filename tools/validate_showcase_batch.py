#!/usr/bin/env python3
"""Validate a six-video Helix pilot manifest and its encoded MP4 deliverables.

Usage: python tools/validate_showcase_batch.py pilots.json --report pilots-report.json
Manifest schema: {"pilots":[{"id":"drums","video":"renders/drums.mp4",
"audio_source":"music/song.wav","excerpt_start_seconds":12.5,
"excerpt_duration_seconds":35.0,"layout":"snowman-band"}]}
"""
import argparse
import importlib.util
import json
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "validate_showcase_mp4", Path(__file__).with_name("validate_showcase_mp4.py"))
_validator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_validator)

REQUIRED = {"id", "video", "audio_source", "excerpt_start_seconds",
            "excerpt_duration_seconds", "layout"}


def validate_manifest(path):
    path = Path(path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    pilots = manifest.get("pilots")
    if not isinstance(pilots, list) or len(pilots) != 6:
        raise ValueError("Manifest must contain exactly six pilots")
    ids = [p.get("id") for p in pilots]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != 6:
        raise ValueError("Pilot IDs must be six distinct nonempty strings")
    results = []
    for pilot in pilots:
        missing = REQUIRED - pilot.keys()
        if missing:
            results.append({"id": pilot["id"], "passed": False,
                            "errors": ["Missing fields: " + ", ".join(sorted(missing))]})
            continue
        errors = []
        for key in ("video", "audio_source", "layout"):
            if not isinstance(pilot[key], str) or not pilot[key].strip():
                errors.append(f"{key} must be a nonempty string")
        try:
            start = float(pilot["excerpt_start_seconds"])
            duration = float(pilot["excerpt_duration_seconds"])
            if not 0 <= start or not 30 <= duration <= 42:
                errors.append("Excerpt must start at >=0 and last 30-42 seconds")
        except (TypeError, ValueError):
            errors.append("Invalid excerpt timestamps")
            duration = 0
        video = path.parent / pilot["video"] if isinstance(pilot["video"], str) else path
        checked = _validator.validate(video) if not errors else {"passed": False, "errors": []}
        errors.extend(checked["errors"])
        if checked.get("duration_seconds") is not None and abs(
                checked["duration_seconds"] - duration) > 0.5:
            errors.append("Encoded duration differs from requested excerpt by >0.5s")
        source = path.parent / pilot["audio_source"] if isinstance(pilot["audio_source"], str) else path
        if not source.is_file():
            errors.append("Source audio file missing")
        results.append({"id": pilot["id"], "passed": not errors,
                        "errors": errors, "video_validation": checked})
    return {"passed": all(r["passed"] for r in results), "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = validate_manifest(args.manifest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"passed": False, "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
