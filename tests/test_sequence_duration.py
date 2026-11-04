from __future__ import annotations

import wave
import xml.etree.ElementTree as ET
from pathlib import Path

from xlights.xml_io import apply_sequence_duration

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template.xsq"


def _write_wav(path: Path, seconds: float, rate: int = 8000) -> None:
    frames = int(rate * seconds)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * frames)


def _wav_seconds(path: Path) -> float:
    with wave.open(str(path), "r") as handle:
        return handle.getnframes() / float(handle.getframerate())


def _effect_bounds(root: ET.Element) -> list[tuple[str, int, int, str]]:
    parents: dict[int, ET.Element] = {}
    for parent in root.iter():
        for child in list(parent):
            parents[id(child)] = parent

    def owner_type(node: ET.Element) -> str:
        current: ET.Element | None = node
        while current is not None:
            if isinstance(current.tag, str) and current.tag.endswith("Element"):
                return (current.attrib.get("type") or "").lower()
            current = parents.get(id(current))
        return ""

    bounds: list[tuple[str, int, int, str]] = []
    for effect in root.iter():
        if not (isinstance(effect.tag, str) and effect.tag.endswith("Effect")):
            continue
        if "startTime" not in effect.attrib or "endTime" not in effect.attrib:
            continue
        bounds.append(
            (
                effect.attrib.get("name") or effect.attrib.get("label") or "",
                int(effect.attrib["startTime"]),
                int(effect.attrib["endTime"]),
                owner_type(effect),
            )
        )
    return bounds


def test_short_wav_replaces_template_duration_and_clips_marks(tmp_path: Path) -> None:
    audio = tmp_path / "thirty.wav"
    _write_wav(audio, 30.0)
    duration_s = _wav_seconds(audio)
    assert duration_s == 30.0

    root = ET.parse(TEMPLATE).getroot()
    original = root.find("./head/sequenceDuration")
    assert original is not None
    assert original.text == "132.039"
    original_bounds = _effect_bounds(root)
    assert any(end > 30_000 for _name, _start, end, _kind in original_bounds)

    report = apply_sequence_duration(root, duration_s)

    assert root.find("./head/sequenceDuration").text == "30.000"  # type: ignore[union-attr]
    assert report["duration_ms"] == 30_000
    assert int(report["removed"]) + int(report["clipped"]) > 0
    assert int(report["timing_removed"]) + int(report["timing_clipped"]) >= 0
    for _name, start, end, _kind in _effect_bounds(root):
        assert start < 30_000
        assert end <= 30_000
        assert end > start


def test_crossing_effect_is_clipped_and_late_timing_mark_is_removed() -> None:
    root = ET.fromstring(
        """
        <xsequence>
          <head><sequenceDuration>132.039</sequenceDuration></head>
          <ElementEffects>
            <Element type="model" name="Arch">
              <EffectLayer>
                <Effect name="On" startTime="1000" endTime="45000"/>
                <Effect name="On" startTime="31000" endTime="40000"/>
              </EffectLayer>
            </Element>
            <Element type="timing" name="Beats">
              <EffectLayer>
                <Effect label="late" startTime="29000" endTime="31000"/>
                <Effect label="after" startTime="30000" endTime="32000"/>
              </EffectLayer>
            </Element>
          </ElementEffects>
        </xsequence>
        """
    )
    report = apply_sequence_duration(root, 30.0)
    assert report["clipped"] == 1
    assert report["removed"] == 1
    assert report["timing_clipped"] == 1
    assert report["timing_removed"] == 1
    model_effects = root.findall(".//Element[@type='model']//Effect")
    assert [(item.attrib["startTime"], item.attrib["endTime"]) for item in model_effects] == [("1000", "30000")]
    timing_effects = root.findall(".//Element[@type='timing']//Effect")
    assert [(item.attrib["label"], item.attrib["endTime"]) for item in timing_effects] == [("late", "30000")]
