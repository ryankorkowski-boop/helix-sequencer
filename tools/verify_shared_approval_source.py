"""Fail closed unless every approval render consumes the same original analysis pass.

Usage: python -m tools.verify_shared_approval_source manifest.json output.json ...
Each manifest must contain source_audio_sha256, analysis_sha256 and source_commit.
"""
import argparse
import json
import re
from pathlib import Path

HEX = re.compile(r"^[0-9a-f]{64}$")


def verify(paths):
    if len(paths) != 3:
        raise ValueError("Exactly three approval receipts required: 16-panel, 12-layout, band")
    receipts = [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]
    expected_roles = {"16-panel", "12-layout", "six-snowman-band"}
    roles = [receipt.get("role") for receipt in receipts]
    if set(roles) != expected_roles or len(set(roles)) != 3:
        raise ValueError("Missing or duplicated approval video role")
    for key in ("source_audio_sha256", "analysis_sha256", "source_commit"):
        values = [receipt.get(key) for receipt in receipts]
        if not all(isinstance(v, str) and v for v in values) or len(set(values)) != 1:
            raise ValueError(f"Approval outputs do not share a single {key}")
    if not HEX.fullmatch(receipts[0]["source_audio_sha256"]) or not HEX.fullmatch(receipts[0]["analysis_sha256"]):
        raise ValueError("Invalid source or analysis SHA256")
    for receipt in receipts:
        if receipt.get("native_verified") is not True or receipt.get("mp4_verified") is not True:
            raise ValueError(f"Unverified native MP4: {receipt['role']}")
        if receipt.get("owner_approved") is not False:
            raise ValueError("Owner approval must remain pending")
    return {"status": "AWAITING_OWNER_APPROVAL", "roles": sorted(expected_roles),
            "source_audio_sha256": receipts[0]["source_audio_sha256"],
            "analysis_sha256": receipts[0]["analysis_sha256"],
            "source_commit": receipts[0]["source_commit"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", type=Path, nargs=3)
    args = parser.parse_args()
    print(json.dumps(verify(args.receipts), indent=2))


if __name__ == "__main__":
    main()
