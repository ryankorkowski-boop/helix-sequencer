from __future__ import annotations

import argparse
import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Mapping

from export.stage_pack_manifest_export import build_demo_stage_pack_export_manifest


STAGE_PACK_CSV_SCHEMA = "helix.stage_pack_manifest_csv.v1"
DEFAULT_OUTPUT_PATH = Path("outputs/demo_snowman_stage_pack_bundle/demo_snowman_stage_pack_manifest.csv")
CSV_COLUMNS = [
    "start_ms",
    "end_ms",
    "duration_ms",
    "performer_kind",
    "performer",
    "role",
    "kind",
    "target_model",
    "target_submodel",
    "effect",
    "timing_track",
    "source",
    "intensity",
    "confidence",
]


def _row_to_csv_record(row: Mapping[str, Any]) -> dict[str, Any]:
    return {column: row.get(column, "") for column in CSV_COLUMNS}


def manifest_rows_to_csv_text(rows: Iterable[Mapping[str, Any]]) -> str:
    """Convert flattened manifest rows to stable spreadsheet-friendly CSV text."""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(_row_to_csv_record(row))
    return buffer.getvalue()


def build_stage_pack_manifest_csv(manifest: Mapping[str, Any]) -> dict[str, Any]:
    rows = list(manifest.get("rows", []) or [])
    csv_text = manifest_rows_to_csv_text(rows)
    performers = sorted({str(row.get("performer", "")) for row in rows if row.get("performer")})
    timing_tracks = sorted({str(row.get("timing_track", "")) for row in rows if row.get("timing_track")})
    target_submodels = sorted({str(row.get("target_submodel", "")) for row in rows if row.get("target_submodel")})
    return {
        "schema": STAGE_PACK_CSV_SCHEMA,
        "source_schema": manifest.get("schema"),
        "pack_id": manifest.get("pack_id"),
        "status": "stage_pack_manifest_csv",
        "columns": list(CSV_COLUMNS),
        "row_count": len(rows),
        "csv_text": csv_text,
        "summary": {
            "performers": performers,
            "timing_tracks": timing_tracks,
            "target_submodels": target_submodels,
        },
        "validation": {
            "has_rows": bool(rows),
            "has_header": csv_text.startswith(",".join(CSV_COLUMNS)),
            "row_count_matches_manifest": len(rows) == int(manifest.get("row_count", len(rows)) or 0),
            "includes_faces_effect": "Faces" in {str(row.get("effect", "")) for row in rows},
            "includes_floor_piano_hooks": any(
                row.get("performer") == "floor_piano" and row.get("source") == "player_piano_hook" for row in rows
            ),
            "includes_all_expected_performers": set(performers) >= {
                "bassist",
                "drummer",
                "female_singer",
                "floor_piano",
                "guitarist",
                "singer",
            },
        },
    }


def build_demo_stage_pack_manifest_csv() -> dict[str, Any]:
    return build_stage_pack_manifest_csv(build_demo_stage_pack_export_manifest())


def write_demo_stage_pack_manifest_csv(path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    payload = build_demo_stage_pack_manifest_csv()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload["csv_text"], encoding="utf-8", newline="")
    summary_path = path.with_suffix(".csv.summary.json")
    summary_path.write_text(
        json.dumps(
            {
                "schema": payload["schema"],
                "source_schema": payload["source_schema"],
                "pack_id": payload["pack_id"],
                "status": payload["status"],
                "columns": payload["columns"],
                "row_count": payload["row_count"],
                "summary": payload["summary"],
                "validation": payload["validation"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "path": str(path),
        "summary": str(summary_path),
        "schema": payload["schema"],
        "row_count": payload["row_count"],
        "validation": payload["validation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a CSV export of the demo snowman stage-pack manifest.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    print(json.dumps(write_demo_stage_pack_manifest_csv(args.output), indent=2))


if __name__ == "__main__":
    main()
