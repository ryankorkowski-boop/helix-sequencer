"""Convert verified native xLights FSEQ into 30-fps V5 atlas frames.

Frame bytes are original RGB channel values, never fabricated colors.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from tools.layout_bench.xlights_fseq import load_fseq

def prepare(fseq: Path, dest: Path, *, pixels: int = 30240, fps: int = 30, seconds: float = 3) -> dict:
    source = load_fseq(fseq)
    width = pixels * 3
    frames = []
    for raw in source.rows():
        b = np.asarray(raw, dtype=np.uint8)
        origin = source.sparse_start
        if origin < 0 or origin >= width:
            raise ValueError("FSEQ does not cover V5 channel origin")
        frame = np.zeros(width, dtype=np.uint8)
        frame[origin:min(width, origin + len(b))] = b[:max(0, width - origin)]
        frames.append(frame)
    if not frames:
        raise ValueError("Empty native FSEQ")
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected = int(round(seconds * fps))
    lit = 0
    with dest.open("wb") as f:
        for i in range(expected):
            source_index = min(int((i * 1000 / fps) // source.step_ms), len(frames) - 1)
            row = frames[source_index]
            lit += int(np.count_nonzero(row))
            f.write(row.tobytes())
    if lit == 0:
        raise ValueError("All V5 village channels are dark in native FSEQ")
    result = {"frames": expected, "fps": fps, "pixels": pixels, "channels": width,
              "native_frames": len(frames), "native_step_ms": source.step_ms,
              "lit_channel_samples": lit, "source": str(fseq)}
    dest.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("fseq", type=Path); p.add_argument("output", type=Path)
    a = p.parse_args()
    print(json.dumps(prepare(a.fseq, a.output), indent=2))
