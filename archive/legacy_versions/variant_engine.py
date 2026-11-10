from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


V28_ALIASES: dict[str, tuple[str, str, dict[str, object]]] = {
    "v28.1": ("v27.3", "Style 1", {}),
    "v28.2": ("v23.1", "Style 2", {"density_scale": 0.96, "speed_scale": 1.00, "randomness_scale": 0.16}),
    "v28.3": ("v23.2", "Style 3", {"density_scale": 0.96, "speed_scale": 1.02, "randomness_scale": 0.12}),
    "v28.4": ("v19.1", "Style 4", {"density_scale": 1.04, "speed_scale": 1.02, "randomness_scale": 0.10}),
    "v28.5": ("v23.5", "Style 5", {"density_scale": 1.02, "speed_scale": 1.04, "randomness_scale": 0.13}),
    "v28.6": ("v24.3", "Style 6", {"density_scale": 1.04, "speed_scale": 1.08, "randomness_scale": 0.11}),
    "v28.7": ("v9.2", "Style 7", {"density_scale": 0.88, "speed_scale": 0.94, "randomness_scale": 0.08}),
    "v28.8": ("v16.3", "Style 8", {"density_scale": 1.08, "speed_scale": 1.14, "randomness_scale": 0.16}),
    "v28.9": ("v24.1", "Style 9", {"density_scale": 0.98, "speed_scale": 1.04, "randomness_scale": 0.10}),
}


def enable_v28_aliases() -> None:
    """Install v28 aliases into the core lazy variant catalog.

    The legacy GUI exposes v28 as the current-pipeline family. Rather than
    rewriting the large canonical style catalog in-place, this compatibility
    adapter aliases each v28 lane to the closest existing maintained style and
    stamps the runtime style with the v28 version/title.
    """

    from core import effect_engine

    catalog = effect_engine.VARIANTS._ensure_loaded()  # noqa: SLF001 - intentional adapter hook
    for version, (base_version, title, overrides) in V28_ALIASES.items():
        if version in catalog:
            continue
        base_style = catalog[base_version]
        catalog[version] = replace(
            base_style,
            version=version,
            family="v28",
            title=title,
            **overrides,
        )


def main_for(version: str, engine_args: list[str] | None = None) -> None:
    enable_v28_aliases()
    from core import effect_engine

    effect_engine.main_for(version, engine_args)
