"""Select verified owner-curated Helix showcase audio from the Starred catalog.

Selection is deterministic, supports rotation, and never substitutes unverified audio.
This utility selects Drive IDs; download, SHA256 verification, and musical analysis
remain mandatory before native rendering.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "showcase" / "starred_music_catalog.json"


def candidates(catalog: dict, *, requested_id: str | None = None) -> list[dict]:
    files = catalog.get("files", [])
    if not isinstance(files, list):
        raise ValueError("Invalid Starred catalog")
    valid = [f for f in files if isinstance(f, dict) and f.get("id") and f.get("title")]
    if len({f["id"] for f in valid}) != len(valid):
        raise ValueError("Duplicate Drive file IDs in catalog")
    if requested_id:
        matches = [f for f in valid if f["id"] == requested_id]
        if not matches:
            raise ValueError("Requested audio ID not in Starred catalog; use explicit authorized source workflow")
        return matches
    return valid


def select(catalog: dict, *, rotation: int = 0, requested_id: str | None = None,
           used_ids: set[str] | None = None) -> dict:
    if rotation < 0:
        raise ValueError("rotation must be nonnegative")
    rows = candidates(catalog, requested_id=requested_id)
    if not rows:
        raise ValueError("No eligible Starred audio")
    if requested_id:
        return rows[0]
    # Do not automatically repeat an already-used source; require an explicit
    # new rotation cycle or an owner-selected ID before reusing it.
    unused = [r for r in rows if r["id"] not in (used_ids or set())]
    if not unused:
        raise ValueError("All Starred source IDs already used; reset the rotation ledger explicitly")
    pool = unused
    return pool[rotation % len(pool)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--rotation", type=int, default=0)
    parser.add_argument("--requested-id")
    parser.add_argument("--used-ids-json", type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    used = set(json.loads(args.used_ids_json.read_text())) if args.used_ids_json else set()
    selected = select(catalog, rotation=args.rotation, requested_id=args.requested_id, used_ids=used)
    print(json.dumps({"drive_file_id": selected["id"], "title": selected["title"],
                      "source_folder": catalog["folder_url"],
                      "verification": "SHA256 and duration must be checked after download"}, indent=2))


if __name__ == "__main__":
    main()
