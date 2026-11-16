"""Compose an ordered review playlist or a grid with one soundtrack."""
from pathlib import Path
import subprocess
import tempfile


def compose(paths, output, *, comparison):
    from imageio_ffmpeg import get_ffmpeg_exe

    paths = [Path(path).resolve(strict=True) for path in paths]
    output = Path(output).resolve()
    if not 2 <= len(paths) <= 8 or len(set(paths)) != len(paths):
        raise ValueError("Choose two to eight distinct variant previews")
    if output in paths:
        raise ValueError("Choose a separate file for the combined preview")
    columns = min(len(paths), 4)
    args = [get_ffmpeg_exe(), "-nostdin", "-v", "error", "-y", "-filter_complex_threads", "2"]
    for path in paths:
        args.extend(["-threads", "1", "-i", str(path)])
    if comparison:
        positions = "|".join(f"{i % columns * 480}_{i // columns * 270}" for i in range(len(paths)))
        filters = [
            f"[{i}:v]setpts=PTS-STARTPTS,scale=480:270:force_original_aspect_ratio=decrease,"
            f"pad=480:270:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]"
            for i in range(len(paths))
        ]
        filters.append("".join(f"[v{i}]" for i in range(len(paths)))
                       + f"xstack=inputs={len(paths)}:layout={positions}:shortest=1[v]")
        maps = ["-map", "[v]", "-map", "0:a:0", "-shortest"]
    else:
        filters = ["".join(f"[{i}:v:0][{i}:a:0]" for i in range(len(paths)))
                   + f"concat=n={len(paths)}:v=1:a=1[v][a]"]
        maps = ["-map", "[v]", "-map", "[a]"]
    # Write beside the final output for an atomic rename even across Windows drives.
    with tempfile.TemporaryDirectory(dir=output.parent, prefix="helix-review-") as folder:
        pending = Path(folder) / "review.mp4"
        result = subprocess.run(
            [*args, "-filter_complex", ";".join(filters), *maps, "-c:v", "libx264",
             "-preset", "veryfast", "-threads", "2", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-movflags", "+faststart", str(pending)],
            capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode or not pending.is_file():
            raise RuntimeError(result.stderr.strip() or "Unable to create variant review")
        pending.replace(output)
