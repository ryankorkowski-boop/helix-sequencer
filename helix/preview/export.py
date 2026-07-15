"""Export helpers for preview engine output."""

import json
from pathlib import Path

from .renderer import Frame


def export_json(frames: list[Frame], output: str | Path) -> Path:
    """Write preview frames to a portable JSON format."""
    path = Path(output)
    payload = [
        {"timestamp_ms": f.timestamp_ms, "channels": f.channels}
        for f in frames
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
