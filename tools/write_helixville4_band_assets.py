from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from models.helixville4_band_assets import HELIXVILLE4_BAND_ASSETS, build_helixville4_band_asset_catalog, svg_for_band_asset


def write_band_assets(output_dir: str | Path) -> dict[str, object]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for asset in HELIXVILLE4_BAND_ASSETS:
        path = out_dir / f"{asset.asset_id}.svg"
        path.write_text(svg_for_band_asset(asset), encoding="utf-8")
        written.append(str(path))
    manifest_path = out_dir / "helixville4_band_assets_manifest.json"
    manifest_path.write_text(json.dumps(build_helixville4_band_asset_catalog(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "output_dir": str(out_dir),
        "asset_count": len(written),
        "svg_files": written,
        "manifest": str(manifest_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Helixville4 band background/white-outline SVG assets.")
    parser.add_argument("--output-dir", type=Path, default=Path("test_runs/helixville4_band_assets"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = write_band_assets(args.output_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
