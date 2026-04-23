from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IntakeSummary:
    free_resource_count: int
    free_direct_download_count: int
    vendor_benchmark_count: int
    training_modes: dict[str, int]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_summary(free_manifest: dict, vendor_manifest: dict) -> IntakeSummary:
    resources = list(free_manifest.get("resources", []) or [])
    vendors = list(vendor_manifest.get("sources", []) or [])
    training_modes: dict[str, int] = {}

    for item in resources:
        mode = str(item.get("training_use", "unknown") or "unknown")
        training_modes[mode] = training_modes.get(mode, 0) + 1
    for item in vendors:
        mode = str(item.get("training_mode", "unknown") or "unknown")
        training_modes[mode] = training_modes.get(mode, 0) + 1

    return IntakeSummary(
        free_resource_count=len(resources),
        free_direct_download_count=sum(1 for item in resources if bool(item.get("direct_download"))),
        vendor_benchmark_count=len(vendors),
        training_modes=training_modes,
    )


def print_manifest_overview(free_manifest: dict, vendor_manifest: dict, summary: IntakeSummary) -> None:
    print("=== Legal Free Resource Intake ===")
    print(f"Resources: {summary.free_resource_count}")
    print(f"Direct-download candidates: {summary.free_direct_download_count}")
    for item in free_manifest.get("resources", []) or []:
        rid = item.get("id", "unknown")
        name = item.get("name", "")
        access = item.get("access", "")
        training = item.get("training_use", "")
        print(f"- {rid}: {name} | access={access} | training={training}")

    print("\n=== Vendor Benchmark Sources ===")
    print(f"Sources: {summary.vendor_benchmark_count}")
    for item in vendor_manifest.get("sources", []) or []:
        sid = item.get("id", "unknown")
        name = item.get("name", "")
        mode = item.get("training_mode", "")
        print(f"- {sid}: {name} | training={mode}")

    print("\n=== Training Mode Histogram ===")
    for key in sorted(summary.training_modes):
        print(f"- {key}: {summary.training_modes[key]}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize legal free resource intake and vendor benchmark manifests.")
    parser.add_argument(
        "--free-manifest",
        default=str(Path("xlights") / "legal_free_resources_manifest.json"),
        help="Path to legal free resource manifest JSON",
    )
    parser.add_argument(
        "--vendor-manifest",
        default=str(Path("xlights") / "vendor_benchmark_manifest.json"),
        help="Path to vendor benchmark manifest JSON",
    )
    parser.add_argument("--report", help="Optional output JSON summary path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    free_path = Path(args.free_manifest)
    vendor_path = Path(args.vendor_manifest)

    if not free_path.exists():
        raise SystemExit(f"Missing free manifest: {free_path}")
    if not vendor_path.exists():
        raise SystemExit(f"Missing vendor manifest: {vendor_path}")

    free_manifest = _load_json(free_path)
    vendor_manifest = _load_json(vendor_path)
    summary = build_summary(free_manifest, vendor_manifest)

    print_manifest_overview(free_manifest, vendor_manifest, summary)

    if args.report:
        report_path = Path(args.report)
        payload = {
            "free_resource_count": summary.free_resource_count,
            "free_direct_download_count": summary.free_direct_download_count,
            "vendor_benchmark_count": summary.vendor_benchmark_count,
            "training_modes": summary.training_modes,
            "free_manifest": str(free_path),
            "vendor_manifest": str(vendor_path),
        }
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nSaved summary report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
