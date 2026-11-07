#!/usr/bin/env python3
"""Inspect native proof ZIPs and optionally enforce the musical-showcase acceptance gate."""
import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path


def inspect(archive, require_showcase=False):
    path = Path(archive)
    result = {
        "archive": str(path),
        "valid_zip": False,
        "entries": 0,
        "extensions": {},
        "diagnostic_sources": {},
        "showcase_mp4s_verified": 0,
        "errors": [],
    }
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            result["errors"].append("ZIP CRC failure: " + bad)
            return result
        names = [i.filename for i in z.infolist() if not i.is_dir()]
        result["valid_zip"] = True
        result["entries"] = len(names)
        result["extensions"] = dict(Counter(Path(n).suffix.lower() for n in names))
        for name in names:
            if name.endswith("/verification.json"):
                try:
                    record = json.loads(z.read(name))
                    if isinstance(record, dict) and "source" in record:
                        result["diagnostic_sources"][name] = record["source"]
                except (ValueError, UnicodeDecodeError) as exc:
                    result["errors"].append(name + ": " + str(exc))
        result["mp4s_present"] = [n for n in names if n.lower().endswith(".mp4")]
        # Presence alone cannot prove native render/source-audio identity.
        result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

        if require_showcase:
            failures = []
            validation = None
            validation_path = next((name for name in ("native-proof/VALIDATION.json", "VALIDATION.json") if name in names), None)
            if validation_path:
                try:
                    validation = json.loads(z.read(validation_path))
                except (ValueError, UnicodeDecodeError) as exc:
                    failures.append("VALIDATION.json is unreadable: " + str(exc))
            else:
                failures.append("VALIDATION.json is missing")

            if isinstance(validation, dict):
                if validation.get("full_song_showcase_complete") is not True:
                    failures.append("full_song_showcase_complete is not true")
                final_band = validation.get("final_band_output")
                physical = validation.get("physical")
                band_verified = validation.get("complete_band_verified") is True
                for section in (final_band, physical):
                    if isinstance(section, dict):
                        band_verified = band_verified or section.get("complete_band_verified") is True
                if not band_verified:
                    failures.append("complete-band verification is not true")

            if not isinstance(validation, dict) and validation_path:
                failures.append("VALIDATION.json is not a JSON object")

            non_diagnostic_mp4s = [
                n for n in result["mp4s_present"]
                if "diagnostic" not in n.lower()
            ]
            if not non_diagnostic_mp4s:
                failures.append("no non-diagnostic MP4 is present")
            for video in non_diagnostic_mp4s:
                with z.open(video) as stream:
                    header = stream.read(12)
                if len(header) < 12 or header[4:8] != b"ftyp":
                    failures.append(video + ": invalid MP4 container header")

            result["acceptance"] = {
                "required": True,
                "passed": not failures,
                "failures": failures,
                "non_diagnostic_mp4s": non_diagnostic_mp4s,
            }
            if failures:
                result["errors"].extend("showcase acceptance: " + item for item in failures)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--require-showcase",
        action="store_true",
        help="fail unless the archive proves a complete, full-band musical showcase",
    )
    args = parser.parse_args()
    try:
        result = inspect(args.archive, require_showcase=args.require_showcase)
    except (OSError, zipfile.BadZipFile) as exc:
        result = {"valid_zip": False, "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("valid_zip") and not result.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
