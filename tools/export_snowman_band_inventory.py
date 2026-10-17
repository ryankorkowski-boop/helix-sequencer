"""Generate snowman band pixel and AC wiring inventories without music input.

Run: python -m tools.export_snowman_band_inventory --output-dir build/snowman_wiring
Does not infer hardware controller addresses or physical AC bulb quantities.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from models.native_review_band import add_band, ac_variant, allocate
from models.snowman_wiring_inventory import write_inventory
from models.ultimate_showcase import Garden


def export_band_inventories(destination: Path):
    destination = Path(destination)
    garden = Garden(title="Helix Snowman Band Wiring Inventory", slug="Helix_Snowman_Wiring")
    pixel_models = add_band(garden)
    expected = {"drummer", "bass", "guitar", "piano", "xylophone", "lead", "harmony"}
    roles = [model.details.get("review_role") for model in pixel_models]
    if len(roles) != 7 or set(roles) != expected:
        raise ValueError(f"Expected seven distinct snowman roles, got {roles}")
    ac_models = [ac_variant(model) for model in pixel_models]
    if any(model.kind != "ac" or len(model.submodels) > 16 for model in ac_models):
        raise ValueError("AC16 conversion did not produce seven <=16-circuit models")
    ac_garden = Garden(title="Helix Snowman AC16", slug="Helix_Snowman_AC16")
    ac_garden.models.extend(ac_models)
    allocate(ac_garden)
    pixel_files = write_inventory(pixel_models, destination / "pixel")
    ac_files = write_inventory(ac_models, destination / "ac16")
    return {"pixel": pixel_files, "ac16": ac_files}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    for mode, files in export_band_inventories(args.output_dir).items():
        print(f"{mode}: {files[0]} | {files[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
