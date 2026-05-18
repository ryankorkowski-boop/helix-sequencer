from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_helpers.helixville4_visible_band import upgrade_visible_band_models


DEFAULT_LAYOUT = ROOT / "test_runs" / "helixia_layout_smoke_lightsouttheme" / "helixville4_show_folder" / "xlights_rgbeffects.xml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upgrade the Helixville4 split snowman band models that existing sequences target."
    )
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT, help="xlights_rgbeffects.xml to update in place")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = upgrade_visible_band_models(args.layout)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if payload.get("missing") else 0


if __name__ == "__main__":
    raise SystemExit(main())
