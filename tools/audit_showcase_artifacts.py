#!/usr/bin/env python3
"""Audit recovered showcase files without promoting missing or mismatched artifacts."""
import argparse
import hashlib
import json
from pathlib import Path

def audit(root, manifest):
    root = Path(root).resolve()
    records = json.loads(Path(manifest).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Manifest must be a JSON list")
    results = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            results.append({"path": None, "passed": False, "errors": ["record must be an object"], "actual_sha256": None, "bytes": None})
            continue
        name = record.get("path")
        expected = record.get("sha256")
        errors = []
        if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
            errors.append("unsafe path")
            path = None
        else:
            path = (root / name).resolve()
            if not path.is_relative_to(root):
                errors.append("path escapes root")
            if name in seen:
                errors.append("duplicate path")
            seen.add(name)
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            errors.append("invalid expected SHA256")
        actual = None
        size = None
        if path is not None and not errors:
            if not path.is_file():
                errors.append("missing file")
            else:
                digest = hashlib.sha256()
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                actual = digest.hexdigest()
                size = path.stat().st_size
                if actual != expected:
                    errors.append("SHA256 mismatch")
                if size == 0:
                    errors.append("empty file")
        results.append({"path": name, "passed": not errors, "errors": errors,
                        "actual_sha256": actual, "bytes": size})
    return {"passed": bool(results) and all(r["passed"] for r in results),
            "verified": sum(r["passed"] for r in results), "total": len(results),
            "results": results}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path,
                        help='JSON array of {"path":"relative/file.mp4","sha256":"..."}')
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.root, args.manifest)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        result = {"passed": False, "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
