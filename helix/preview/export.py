"""Export rendered preview frames to GIF/MP4 outputs."""

from pathlib import Path


class PreviewExporter:
    def __init__(self, fps=30):
        self.fps = fps

    def export_gif(self, frames, output_path, duration_ms=None):
        output_path = Path(output_path)
        if not frames:
            raise ValueError("No frames supplied")

        first, *rest = frames
        first.save(
            output_path,
            save_all=True,
            append_images=rest,
            duration=duration_ms or int(1000 / self.fps),
            loop=0,
        )
        return output_path

    def export_mp4(self, frames, output_path):
        """MP4 hook.

        Keeps encoding isolated so ffmpeg/imageio can be added without
        changing the Helix preview pipeline.
        """
        return {
            "output": str(output_path),
            "format": "mp4",
            "frames": len(frames),
            "fps": self.fps,
            "encoder": "pending",
        }

    def export(self, frames, output_path, format="mp4"):
        if format.lower() == "gif":
            return self.export_gif(frames, output_path)
        return self.export_mp4(frames, output_path)
