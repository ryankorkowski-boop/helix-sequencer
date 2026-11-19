#!/usr/bin/env python3
"""Verify a candidate source audio against the native-render source identity.

A matching filename, title, duration or audible similarity is not a byte identity
proof. Fail closed before reusing an old native render with a different audio file.
"""
import argparse
import hashlib
import json
from pathlib import Path

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def verify(candidate, expected):
    if not isinstance(expected, str) or len(expected) != 64 or any(
            character not in "0123456789abcdef" for character in expected):
        raise ValueError("expected SHA256 must be 64 lowercase hexadecimal characters")
    candidate = Path(candidate)
    if not candidate.is_file():
        return {"passed": False, "reason": "source file missing", "source": str(candidate)}
    actual = sha256(candidate)
    return {"passed": actual == expected, "source": str(candidate),
            "expected_sha256": expected, "actual_sha256": actual,
            "reason": "exact source bytes verified" if actual == expected else
                      "source mismatch: native render reuse prohibited"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("expected_sha256")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.candidate, args.expected_sha256)
    except (ValueError, OSError) as exc:
        result = {"passed": False, "reason": str(exc)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
