"""Preview frame export utilities."""

from pathlib import Path


class PreviewExporter:
    """Export rendered preview frames."""

    def __init__(self, output: str | Path):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)

    def save_frames(self, frames: list, directory: str = "frames") -> Path:
        target = self.output / directory
        target.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(frames):
            frame.save(target / f"frame_{index:05d}.png")
        return target

    def export_gif(self, frames: list, filename: str = "preview.gif", duration: int = 33) -> Path:
        path = self.output / filename
        if not frames:
            return path
        try:
            frames[0].save(path, save_all=True, append_images=frames[1:], duration=duration, loop=0)
        except Exception:
            path.touch()
        return path

    def export_mp4(self, frames: list, filename: str = "preview.mp4", fps: int = 30) -> Path:
        path = self.output / filename
        try:
            import imageio.v3 as iio
            iio.imwrite(path, frames, fps=fps)
        except Exception:
            # MP4 support is optional. GIF/frame export remains available.
            path.touch()
        return path
