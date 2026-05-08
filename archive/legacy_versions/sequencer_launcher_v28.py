#!/usr/bin/env python3
"""Legacy GUI launcher with v28 Style lanes enabled.

This shim avoids rewriting the large legacy launcher file. It imports the
existing launcher module, appends the v28 registry entries in memory, rebuilds
its derived maps, then starts the same Launcher class.
"""

from __future__ import annotations

from dataclasses import dataclass

import sequencer_launcher as legacy


@dataclass(frozen=True)
class V28Lane:
    version: str
    label: str
    style_note: str
    density: float
    speed: float
    randomness: float
    energy: float
    palette_label: str = "Workspace Match"
    ac_only: bool = False

    @property
    def variant_note(self) -> str:
        return f"Current Helix pipeline exposed through the legacy GUI as {self.label}."


V28_LANES: tuple[V28Lane, ...] = (
    V28Lane("v28.1", "Style 1", "Current Helix pipeline default style lane.", 1.00, 1.00, 0.10, 0.70),
    V28Lane("v28.2", "Style 2", "Current Helix story-blend lane for balanced, song-first choreography.", 0.96, 1.00, 0.16, 0.62),
    V28Lane("v28.3", "Style 3", "Current Helix stem-choreo lane for separated bass, drum, vocal, and support roles.", 0.96, 1.02, 0.12, 0.64),
    V28Lane("v28.4", "Style 4", "Current Helix piano-spatial lane for note-driven sequential prop motion.", 1.04, 1.02, 0.10, 0.64, "Template"),
    V28Lane("v28.5", "Style 5", "Current Helix cinematic-finale lane for bigger builds, impacts, and closing scenes.", 1.02, 1.04, 0.13, 0.74),
    V28Lane("v28.6", "Style 6", "Current Helix vendor-grade lane for top-tier role hierarchy and model-fit sequencing.", 1.04, 1.08, 0.11, 0.76),
    V28Lane("v28.7", "Style 7", "Current Helix AC-heritage lane for dumb-light-friendly phrasing and contrast.", 0.88, 0.94, 0.08, 0.52, "Workspace Match", True),
    V28Lane("v28.8", "Style 8", "Current Helix motion-showcase lane for purposeful chase, wave, and sweep direction changes.", 1.08, 1.14, 0.16, 0.74),
    V28Lane("v28.9", "Style 9", "Current Helix customer-ready lane for role-based layering and pixel-family intent.", 0.98, 1.04, 0.10, 0.72),
)


def _variant_for_lane(lane: V28Lane) -> legacy.VariantOption:
    return legacy.VariantOption(lane.version, lane.label, lane.variant_note, "Helix v28")


def _style_for_lane(lane: V28Lane) -> legacy.StyleTypePreset:
    return legacy.StyleTypePreset(
        label=lane.label,
        note=f"{lane.style_note} Exposed as {lane.version}.",
        versions=(lane.version,),
        density=lane.density,
        speed=lane.speed,
        randomness=lane.randomness,
        energy=lane.energy,
        palette_label=lane.palette_label,
        ac_only=lane.ac_only,
    )


def enable_v28_styles() -> None:
    """Install all v28 Style lanes into the legacy launcher's runtime registries once."""

    existing_versions = {item.version for item in legacy.VARIANT_OPTIONS}
    for lane in V28_LANES:
        if lane.version not in existing_versions:
            legacy.VARIANT_OPTIONS.append(_variant_for_lane(lane))
            existing_versions.add(lane.version)

    legacy.ACTIVE_VARIANT_OPTIONS = [
        item for item in legacy.VARIANT_OPTIONS if legacy._major_version(item.version) >= 20
    ]
    legacy.SCRIPT_MAP = {
        item.version: legacy.APP_ROOT / f"{item.version}.py"
        for item in legacy.ACTIVE_VARIANT_OPTIONS
    }

    existing_style_labels = {item.label for item in legacy.STYLE_TYPE_OPTIONS}
    insert_at = 0
    for lane in reversed(V28_LANES):
        if lane.label not in existing_style_labels:
            legacy.STYLE_TYPE_OPTIONS.insert(insert_at, _style_for_lane(lane))
            existing_style_labels.add(lane.label)
    legacy.STYLE_TYPE_MAP = {item.label: item for item in legacy.STYLE_TYPE_OPTIONS}


# Backward-compatible name used by the first v28.1 test slice.
def enable_v28_1() -> None:
    enable_v28_styles()


def main() -> None:
    enable_v28_styles()
    app = legacy.Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()
