from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IntakeSummary:
    resource_count: int
    direct_download_count: int
    permitted_uses: dict[str, int]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_summary(resource_manifest: dict) -> IntakeSummary:
    resources = list(resource_manifest.get("resources", []) or [])
    permitted_uses: dict[str, int] = {}

    for item in resources:
        mode = str(item.get("permitted_use", "unknown") or "unknown")
        permitted_uses[mode] = permitted_uses.get(mode, 0) + 1

    return IntakeSummary(
        resource_count=len(resources),
        direct_download_count=sum(1 for item in resources if bool(item.get("direct_download"))),
        permitted_uses=permitted_uses,
    )


def print_manifest_overview(resource_manifest: dict, summary: IntakeSummary) -> None:
    print("=== Legal Resource Intake ===")
    print(f"Resources: {summary.resource_count}")
    print(f"Direct-download candidates: {summary.direct_download_count}")
    for item in resource_manifest.get("resources", []) or []:
        rid = item.get("id", "unknown")
        name = item.get("name", "")
        access = item.get("access", "")
        permitted_use = item.get("permitted_use", "")
        print(f"- {rid}: {name} | access={access} | permitted_use={permitted_use}")

    print("\n=== Permitted Use Histogram ===")
    for key in sorted(summary.permitted_uses):
        print(f"- {key}: {summary.permitted_uses[key]}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize legal resource intake manifest without retaining training guidance.")
    parser.add_argument(
        "--resource-manifest",
        default=str(Path("xlights") / "legal_free_resources_manifest.json"),
        help="Path to legal resource manifest JSON",
    )
    parser.add_argument("--report", help="Optional output JSON summary path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    resource_path = Path(args.resource_manifest)

    if not resource_path.exists():
        raise SystemExit(f"Missing resource manifest: {resource_path}")

    resource_manifest = _load_json(resource_path)
    summary = build_summary(resource_manifest)

    print_manifest_overview(resource_manifest, summary)

    if args.report:
        report_path = Path(args.report)
        payload = {
            "resource_count": summary.resource_count,
            "direct_download_count": summary.direct_download_count,
            "permitted_uses": summary.permitted_uses,
            "resource_manifest": str(resource_path),
        }
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nSaved summary report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
