"""Run a short synthetic sequence and reject a white-only palette.

The sequence uses the repository template and layout. Audio is generated
here and is not a tester song.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import sys
import wave
from collections import Counter
from pathlib import Path

import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.effect_engine import (  # noqa: E402
    color_palette_table,
    enabled_palette_hexes,
    hex_is_near_white,
    palette_collapses_to_white,
)


def write_tone(path: Path, seconds: float = 8.0, rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        chunk = bytearray()
        for index in range(frames):
            value = int(8000 * math.sin(2 * math.pi * 220 * index / rate))
            chunk += struct.pack("<h", value)
        handle.writeframes(chunk)


def effect_rows(root: ET.Element) -> list[ET.Element]:
    """Placed effects. EffectDB entries are an empty catalog, not output."""
    return [
        element
        for element in root.iter()
        if element.tag == "Effect" and element.attrib.get("name")
    ]


def summarize(xsq_path: Path) -> dict:
    root = ET.parse(xsq_path).getroot()
    tables = color_palette_table(root)
    effects = effect_rows(root)
    indexes: Counter[str] = Counter()
    white_only = 0
    chromatic = 0
    for effect in effects:
        choice = effect.attrib.get("palette", "")
        indexes[choice] += 1
        if palette_collapses_to_white(choice, tables):
            white_only += 1
        else:
            chromatic += 1
    sample = []
    for index, text in enumerate(tables[:8]):
        colors = enabled_palette_hexes(text)
        sample.append({
            "index": index,
            "colors": colors,
            "white_only": bool(colors) and all(hex_is_near_white(color) for color in colors),
        })
    return {
        "xsq": str(xsq_path),
        "effect_count": len(effects),
        "chromatic_effects": chromatic,
        "white_only_effects": white_only,
        "palette_indexes": dict(indexes),
        "palette_sample": sample,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("palette-smoke"))
    parser.add_argument("--template", type=Path, default=ROOT / "template.xsq")
    parser.add_argument("--layout", type=Path, default=ROOT / "xlights_rgbeffects.xml")
    parser.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        help="Runner prefix. Default is the current Python and main.py.",
    )
    args = parser.parse_args(argv)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    audio = output / "synthetic-tone.wav"
    write_tone(audio)
    command = list(args.command or [sys.executable, str(ROOT / "main.py")])
    if command and command[0] == "--":
        command = command[1:]
    command += [
        "--profile", "master", "--",
        "--template", str(args.template),
        "--audio", str(audio),
        "--layout-file", str(args.layout),
        "--output-dir", str(output / "out"),
        "--variants", "1",
        "--no-prompt",
        "--no-polish",
        "--no-birdsong",
        "--no-matrix-intelligence",
        "--no-workspace-history",
        "--no-learning-memory",
        "--no-effects-orchestrator",
    ]
    completed = subprocess.run(command, cwd=str(ROOT), text=True)
    xsqs = sorted((output / "out").rglob("*.xsq"))
    report = {"returncode": completed.returncode, "command": command, "sequences": []}
    if completed.returncode != 0 or not xsqs:
        report["ok"] = False
        report["error"] = "sequence command failed" if completed.returncode else "no xsq written"
        (output / "palette-smoke.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 1
    failed = False
    for path in xsqs:
        summary = summarize(path)
        indexes = {key for key in summary["palette_indexes"] if key.strip()}
        summary["ok"] = (
            summary["effect_count"] > 0
            and summary["white_only_effects"] == 0
            and summary["chromatic_effects"] == summary["effect_count"]
            and len(indexes) > 1
        )
        report["sequences"].append(summary)
        failed = failed or not summary["ok"]
    report["ok"] = not failed
    (output / "palette-smoke.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
