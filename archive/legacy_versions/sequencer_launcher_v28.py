#!/usr/bin/env python3
"""Legacy GUI launcher with the v28.1 Style 1 lane enabled.

This shim avoids rewriting the large legacy launcher file. It imports the
existing launcher module, appends the v28.1 registry entries in memory, rebuilds
its derived maps, then starts the same Launcher class.
"""

from __future__ import annotations

import sequencer_launcher as legacy


V28_VARIANT = legacy.VariantOption(
    "v28.1",
    "Style 1",
    "Current Helix pipeline exposed through the legacy GUI as the first v28 style lane.",
    "Helix v28",
)

V28_STYLE = legacy.StyleTypePreset(
    label="Style 1",
    note="Current Helix pipeline default style lane exposed as v28.1.",
    versions=("v28.1",),
    density=1.00,
    speed=1.00,
    randomness=0.10,
    energy=0.70,
    palette_label="Workspace Match",
)


def enable_v28_1() -> None:
    """Install v28.1 into the legacy launcher's runtime registries once."""

    if not any(item.version == V28_VARIANT.version for item in legacy.VARIANT_OPTIONS):
        legacy.VARIANT_OPTIONS.append(V28_VARIANT)

    legacy.ACTIVE_VARIANT_OPTIONS = [
        item for item in legacy.VARIANT_OPTIONS if legacy._major_version(item.version) >= 20
    ]
    legacy.SCRIPT_MAP = {
        item.version: legacy.APP_ROOT / f"{item.version}.py"
        for item in legacy.ACTIVE_VARIANT_OPTIONS
    }

    if not any(item.label == V28_STYLE.label for item in legacy.STYLE_TYPE_OPTIONS):
        legacy.STYLE_TYPE_OPTIONS.insert(0, V28_STYLE)
    legacy.STYLE_TYPE_MAP = {item.label: item for item in legacy.STYLE_TYPE_OPTIONS}


def main() -> None:
    enable_v28_1()
    app = legacy.Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()
