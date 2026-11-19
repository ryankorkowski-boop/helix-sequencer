#!/usr/bin/env python3
"""Validate six real Helix showcase MP4 deliverables and their source manifest."""
import argparse
import importlib.util
import json
import math
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "validate_showcase_mp4", Path(__file__).with_name("validate_showcase_mp4.py"))
_validator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_validator)

REQUIRED = {"id", "video", "audio_source", "excerpt_start_seconds",
            "excerpt_duration_seconds", "layout"}


def _local_file(root, value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty relative path")
    candidate = Path(value)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise ValueError(f"{field} must remain within the manifest directory")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field} escapes the manifest directory")
    return resolved


def _timestamp(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{field} must be a finite number") from None
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def validate_manifest(path):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be an object")
    pilots = manifest.get("pilots")
    if not isinstance(pilots, list) or len(pilots) != 6:
        raise ValueError("Manifest must contain exactly six pilots")
    if any(not isinstance(p, dict) for p in pilots):
        raise ValueError("Each pilot must be an object")
    ids = [p.get("id") for p in pilots]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != 6:
        raise ValueError("Pilot IDs must be six distinct nonempty strings")
    root = path.parent
    results = []
    for pilot in pilots:
        errors = []
        missing = REQUIRED - pilot.keys()
        if missing:
            errors.append("Missing fields: " + ", ".join(sorted(missing)))
        video = source = None
        for field in ("video", "audio_source"):
            if field not in pilot:
                continue
            try:
                resolved = _local_file(root, pilot[field], field)
                if field == "video":
                    video = resolved
                else:
                    source = resolved
            except ValueError as exc:
                errors.append(str(exc))
        if "layout" in pilot and (not isinstance(pilot["layout"], str)
                                   or not pilot["layout"].strip()):
            errors.append("layout must be a nonempty string")
        duration = None
        if "excerpt_start_seconds" in pilot and "excerpt_duration_seconds" in pilot:
            try:
                start = _timestamp(pilot["excerpt_start_seconds"], "excerpt_start_seconds")
                duration = _timestamp(pilot["excerpt_duration_seconds"], "excerpt_duration_seconds")
                if start < 0 or not 30 <= duration <= 42:
                    errors.append("Excerpt must start at >=0 and last 30-42 seconds")
            except ValueError as exc:
                errors.append(str(exc))
        if source is not None and not source.is_file():
            errors.append("Source audio file missing")
        checked = {"passed": False, "errors": ["Video not checked due to manifest errors"]}
        if video is not None and not errors:
            checked = _validator.validate(video)
            errors.extend(checked.get("errors", []))
            if not checked.get("passed", False):
                errors.append("Video validation did not pass")
            actual = checked.get("duration_seconds")
            if actual is not None and duration is not None:
                try:
                    if not math.isfinite(float(actual)) or abs(float(actual) - duration) > 0.5:
                        errors.append("Encoded duration differs from requested excerpt by >0.5s")
                except (ValueError, TypeError, OverflowError):
                    errors.append("Invalid encoded duration")
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
