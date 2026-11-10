"""Layered PNG sprite support for preview characters."""

from pathlib import Path


class SpriteSet:
    def __init__(self, asset_dir):
        self.asset_dir = Path(asset_dir)
        self.layers = {}

    def load(self):
        for png in self.asset_dir.glob("*.png"):
            self.layers[png.stem] = png
        return self

    def get(self, layer):
        return self.layers.get(layer)
