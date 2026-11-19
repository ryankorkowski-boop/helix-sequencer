"""Export the Helix Infinite Symphony 3D layout and keyboard-rung contract."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from models.infinite_symphony_showcase import build_megagarden, mega_manifest
from tools.build_helpers.ultimate_showcase import write_layout


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("outputs/Helix_Infinite_Symphony"))
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    garden = build_megagarden()
    manifest = mega_manifest(garden)
    if not 6 <= manifest["footprint_ratio_xz"] <= 10:
        raise ValueError(f"Footprint out of 6–10x requirement: {manifest['footprint_ratio_xz']}")
    if any(n < 3 for n in manifest["coverage"].values()):
        raise ValueError("Missing multiple instances of a native xLights family")
    if len(garden.models[-1].details["keyboard_rung_mapping"]) != 88:
        raise ValueError("Incomplete 88-note keyboard helix mapping")
    write_layout(garden, args.output)
    (args.output / "infinite_symphony_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({key: manifest[key] for key in
                      ("model_count", "channel_count", "footprint_ratio_xz",
                       "house_count", "double_helices", "coverage")}, indent=2))


if __name__ == "__main__":
    main()
