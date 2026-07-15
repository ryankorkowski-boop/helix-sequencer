"""Drummer background visual artifact.

The background is a persistent layer that exists independently from
instrument reactions. Individual components are layered above it.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DrummerBackground:
    asset: str = "drummerbackground.png"
    always_on: bool = True
    opacity: float = 1.0

    def exists(self, root: str = ".") -> bool:
        return Path(root, self.asset).exists()

    def render_state(self) -> dict:
        return {
            "asset": self.asset,
            "visible": self.always_on,
            "opacity": self.opacity,
            "layer": "background",
        }
