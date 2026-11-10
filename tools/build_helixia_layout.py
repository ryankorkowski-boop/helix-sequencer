from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_helpers.helixia import build_helixia_layout  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Helixia (Helixville4) manifest and xLights layout.")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "helixville4"),
        help="Output directory for Helixia planning manifest files.",
    )
    parser.add_argument("--rows", type=int, default=3, help="Village house grid rows.")
    parser.add_argument("--cols", type=int, default=4, help="Village house grid columns.")
    parser.add_argument(
        "--use-helixville4-band-model-specs",
        action="store_true",
        help="Generate spec-driven snowman band models/submodels instead of the legacy placeholder band path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_helixia_layout(
        output_dir=Path(args.output_dir).resolve(),
        village_rows=max(1, int(args.rows)),
        village_cols=max(1, int(args.cols)),
        use_helixville4_band_model_specs=bool(args.use_helixville4_band_model_specs),
    )
    print(
        f"Helixia manifest built: houses={len(payload['village_grid']['houses'])}, "
        f"special_lots={len(payload['special_lots'])}, "
        f"models={payload['xlights_layout']['model_count']}, "
        f"band_specs={payload['xlights_layout'].get('band_model_specs_enabled', False)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
