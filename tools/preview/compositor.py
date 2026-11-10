"""Layer compositor for Helix animated preview frames."""

from pathlib import Path
from PIL import Image


class SpriteCompositor:
    """Composites transparent sprite layers into a preview frame."""

    def __init__(self, asset_dir: str | Path, size=(1280, 720)):
        self.asset_dir = Path(asset_dir)
        self.size = size

    def render(self, layers: list[str]) -> Image.Image:
        frame = Image.new("RGBA", self.size, (0, 0, 0, 0))

        for layer in layers:
            path = self.asset_dir / f"{layer}.png"
            if path.exists():
                sprite = Image.open(path).convert("RGBA")
                frame.alpha_composite(sprite)

        return frame
