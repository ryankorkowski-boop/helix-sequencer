"""Preview asset definitions and validation helpers."""

from pathlib import Path

DRUMMER_LAYERS = (
    "stage",
    "base",
    "left_stick",
    "right_stick",
    "crash_left",
    "crash_right",
    "hihat",
    "snare",
    "tom_left",
    "tom_right",
    "kick",
)


class AssetPack:
    def __init__(self, root):
        self.root = Path(root)

    def path_for(self, layer):
        return self.root / f"{layer}.png"

    def validate(self):
        return {
            layer: self.path_for(layer).exists()
            for layer in DRUMMER_LAYERS
        }
