from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_helpers.helixville2 import (
    DEFAULT_GP_LAYOUT,
    DEFAULT_NEIGHBOR_LAYOUT,
    build_helixville2_layout,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Helixville2 (GP 256ch -> 3D + neighbor common-prop district).")
    parser.add_argument("--source-layout", default=str(DEFAULT_GP_LAYOUT), help="Path to GP baseline xlights_rgbeffects.xml")
    parser.add_argument(
        "--neighbor-layout",
        default=str(DEFAULT_NEIGHBOR_LAYOUT),
        help="Path to allmodels xlights_rgbeffects.xml containing NBH_* imports",
    )
    parser.add_argument("--output-dir", default=str(ROOT / "helixville2"), help="Output show folder path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_layout = Path(args.source_layout).resolve()
    neighbor_layout = Path(args.neighbor_layout).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not source_layout.exists():
        raise SystemExit(f"GP layout not found: {source_layout}")
    if not neighbor_layout.exists():
        raise SystemExit(f"Neighbor layout not found: {neighbor_layout}")

    manifest = build_helixville2_layout(
        source_layout=source_layout,
        neighbor_layout=neighbor_layout,
        output_dir=output_dir,
    )
    print(f"Helixville2 layout created: {manifest['output_layout']}")
    print(f"GP models: {manifest['gp_model_count']}")
    print(f"Imported neighbor models: {manifest['neighbor_imported_count']}")
    print(f"Total models: {manifest['total_model_count']}")
    print(f"Z world range: {manifest['z_world_range']['min']} .. {manifest['z_world_range']['max']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
