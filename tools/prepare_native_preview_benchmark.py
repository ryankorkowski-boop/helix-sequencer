"""Prepare original four-second native preview/audio evidence (stdlib only)."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import struct
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


def prepare_benchmark(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/quality"
    shutil.copyfile(fixture / "benchmark.xsq", output / "benchmark.xsq")
    layout = ET.parse(fixture / "layout.xml")
    # Larger visible dots only; channels and effects are unchanged.
    for model, x in zip(layout.findall("models/model"), (200, 500)):
        model.set("WorldPosX", str(x))
        model.set("WorldPosY", "200")
        model.set("PixelSize", "20")
    layout.write(output / "xlights_rgbeffects.xml", encoding="utf-8",
                 xml_declaration=True)
    rate = 16000
    samples = []
    for frame in range(rate * 4):
        t = frame / rate
        value = 0.0
        for onset, frequency in ((0, 440), (1, 880), (2.5, 660)):
            age = t - onset
            if 0 <= age < .15:
                value += (.4 * math.sin(2 * math.pi * frequency * age)
                          * math.sin(math.pi * age / .15) ** 2)
        samples.append(round(value * 32767))
    with wave.open(str(output / "original.wav"), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    (output / "run_manifest.json").write_text(json.dumps({
        "schema": "helix.run_manifest.v1", "status": "success",
        "warnings": [], "benchmark": "original_synthetic_four_seconds",
        "visual_review_status": "not_reviewed",
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    prepare_benchmark(parser.parse_args().output)
