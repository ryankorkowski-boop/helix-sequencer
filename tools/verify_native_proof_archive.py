#!/usr/bin/env python3
"""Inspect native proof ZIP; distinguish source-verified showcases from diagnostics."""
import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

def inspect(archive):
    path = Path(archive)
    result = {"archive": str(path), "valid_zip": False, "entries": 0,
              "extensions": {}, "diagnostic_sources": {},
              "showcase_mp4s_verified": 0, "errors": []}
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
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.archive)
    except (OSError, zipfile.BadZipFile) as exc:
        result = {"valid_zip": False, "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("valid_zip") and not result.get("errors") else 1

if __name__ == "__main__":
    raise SystemExit(main())
