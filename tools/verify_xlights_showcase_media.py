#!/usr/bin/env python3
"""Fail closed on unbound xLights animations being labeled musical showcases."""
import argparse
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

def audit_archive(path):
    with zipfile.ZipFile(path) as archive:
        xsqs = [name for name in archive.namelist() if name.lower().endswith(".xsq")]
        details = []
        for name in xsqs:
            try:
                head = ET.fromstring(archive.read(name)).find("head")
                media = (head.findtext("mediaFile") or "").strip() if head is not None else ""
                kind = (head.findtext("sequenceType") or "").strip() if head is not None else ""
                duration = (head.findtext("sequenceDuration") or "").strip() if head is not None else ""
                details.append({"path": name, "sequence_type": kind, "duration_seconds": duration,
                                "media_file": media, "musical_showcase_eligible": bool(media) and kind.lower() != "animation"})
            except ET.ParseError as exc:
                details.append({"path": name, "musical_showcase_eligible": False, "error": str(exc)})
    return {"musical_showcase_eligible": bool(details) and all(d["musical_showcase_eligible"] for d in details),
            "sequence_count": len(details), "sequences": details}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = audit_archive(args.archive)
    except (OSError, zipfile.BadZipFile) as exc:
        result = {"musical_showcase_eligible": False, "error": str(exc)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["musical_showcase_eligible"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
