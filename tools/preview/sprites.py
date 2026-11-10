"""Layered sprite support for animated preview characters."""

from pathlib import Path


class SpriteLibrary:
    def __init__(self, asset_dir: str | Path):
        self.asset_dir = Path(asset_dir)
        self.layers: dict[str, Path] = {}

    def register(self, name: str, filename: str) -> None:
        self.layers[name] = self.asset_dir / filename

    def get(self, name: str) -> Path | None:
        return self.layers.get(name)


DEFAULT_DRUMMER_LAYERS = [
    "base",
    "left_stick",
    "right_stick",
    "left_crash",
    "right_crash",
    "hihat",
    "snare",
    "left_tom",
    "right_tom",
    "kick",
    "stage",
]
