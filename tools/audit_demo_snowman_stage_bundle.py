from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from tools.build_demo_snowman_stage_bundle import build_demo_snowman_stage_bundle_payload


DEFAULT_BUNDLE_DIR = Path("outputs/demo_snowman_stage_pack_bundle")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pass_fail(value: bool) -> str:
    return "PASS" if bool(value) else "FAIL"


def audit_bundle_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    validation = dict(summary.get("validation", {}) or {})
    summary_block = dict(summary.get("summary", {}) or {})
    checks = {
        "stage_pack_valid": bool(validation.get("stage_pack_valid")),
        "manifest_valid": bool(validation.get("manifest_valid")),
        "preview_has_floor_piano_link": bool(validation.get("preview_has_floor_piano_link")),
        "artifact_sources_are_consistent": bool(validation.get("artifact_sources_are_consistent")),
        "drummer_feeds_floor_piano": bool(summary_block.get("drummer_feeds_floor_piano")),
        "has_manifest_rows": int(summary_block.get("manifest_rows", 0) or 0) > 0,
        "has_expected_performers": set(summary_block.get("performers", []) or []) >= {
            "bassist",
            "drummer",
            "female_singer",
            "guitarist",
            "singer",
        },
        "has_floor_piano": "floor_piano" in set(summary_block.get("stage_props", []) or []),
    }
    return {
        "schema": "helix.demo_snowman_stage_bundle.audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "summary": summary_block,
    }


def audit_generated_bundle(bundle_dir: Path = DEFAULT_BUNDLE_DIR) -> dict[str, Any]:
    summary_path = bundle_dir / "demo_snowman_stage_pack_bundle_summary.json"
    if not summary_path.exists():
        return {
            "schema": "helix.demo_snowman_stage_bundle.audit.v1",
            "status": "fail",
            "checks": {"summary_file_exists": False},
            "summary": {"missing_path": str(summary_path)},
        }
    loaded = _load_json(summary_path)
    audit = audit_bundle_summary(loaded)
    audit["checks"] = {"summary_file_exists": True, **audit["checks"]}
    return audit


def audit_fresh_demo_bundle() -> dict[str, Any]:
    payload = build_demo_snowman_stage_bundle_payload()
    return audit_bundle_summary(
        {
            "schema": payload["schema"],
            "summary": payload["summary"],
            "validation": payload["validation"],
        }
    )


def format_audit_report(audit: Mapping[str, Any]) -> str:
    lines = [f"Snowman stage bundle audit: {str(audit.get('status', 'unknown')).upper()}"]
    for name, value in dict(audit.get("checks", {}) or {}).items():
        lines.append(f"{_pass_fail(bool(value))} {name}")
    summary = dict(audit.get("summary", {}) or {})
    if summary:
        lines.append(f"rows: {summary.get('manifest_rows', 0)}")
        lines.append(f"performers: {', '.join(summary.get('performers', []) or [])}")
        lines.append(f"props: {', '.join(summary.get('stage_props', []) or [])}")
        lines.append(f"timing_tracks: {', '.join(summary.get('timing_tracks', []) or [])}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the demo snowman stage bundle and print a compact pass/fail report.")
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--fresh", action="store_true", help="Audit a freshly built in-memory demo bundle instead of files on disk.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    args = parser.parse_args()
    audit = audit_fresh_demo_bundle() if args.fresh else audit_generated_bundle(args.bundle_dir)
    print(json.dumps(audit, indent=2) if args.json else format_audit_report(audit))


if __name__ == "__main__":
    main()
