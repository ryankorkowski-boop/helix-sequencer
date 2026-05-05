from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


_EFFECT_HINTS = {
    "on": ("on", "intensity", "solid"),
    "fade": ("fade", "ramp", "twinklefade"),
    "twinkle": ("twinkle",),
    "shimmer": ("shimmer",),
    "chase": ("chase", "wave", "sweep"),
    "off": ("off",),
}

_TIME_ATTRS = (
    "time",
    "centisecond",
    "centiseconds",
    "start",
    "end",
    "starttime",
    "endtime",
    "start_time",
    "end_time",
    "startcs",
    "endcs",
)

_CHANNEL_ATTRS = (
    "channel",
    "channelid",
    "channel_id",
    "circuit",
    "unit",
    "network",
)


@dataclass(frozen=True)
class LmsInspectionReport:
    schema: str = "helix.lms_inspection.v1"
    source_path: str = ""
    file_size_bytes: int = 0
    xml_root: str = ""
    probable_channel_count: int = 0
    channel_tag_count: int = 0
    event_like_tag_count: int = 0
    unique_event_tag_count: int = 0
    probable_duration_seconds: float = 0.0
    timing_density_events_per_second: float = 0.0
    effect_hints: dict[str, int] = field(default_factory=dict)
    common_tags: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def _intish(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"-?\d+", text)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def _duration_from_values(values: Iterable[int]) -> float:
    max_value = max(values, default=0)
    if max_value <= 0:
        return 0.0
    # LOR LMS commonly stores timing in centiseconds. If the value is small,
    # keep the centisecond interpretation anyway because legacy songs usually
    # exceed 1000 centiseconds.
    return round(max_value / 100.0, 3)


def _extract_time_values(root: ET.Element) -> list[int]:
    values: list[int] = []
    for element in root.iter():
        attrs = {str(key).lower(): value for key, value in element.attrib.items()}
        for attr in _TIME_ATTRS:
            value = _intish(attrs.get(attr))
            if value is not None and value >= 0:
                values.append(value)
        # Some LMS event text can be comma/space separated centisecond values.
        tag = _local_name(element.tag)
        if tag in {"effect", "event", "interval", "timing"} and element.text:
            for match in re.finditer(r"\b\d{2,}\b", element.text):
                values.append(int(match.group(0)))
    return values


def _element_text_blob(element: ET.Element) -> str:
    pieces = [_local_name(element.tag)]
    pieces.extend(str(key).lower() for key in element.attrib)
    pieces.extend(str(value).lower() for value in element.attrib.values())
    if element.text:
        pieces.append(element.text.lower())
    return " ".join(pieces)


def _count_effect_hints(root: ET.Element) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for element in root.iter():
        blob = _element_text_blob(element)
        for label, tokens in _EFFECT_HINTS.items():
            if any(token in blob for token in tokens):
                counts[label] += 1
    return dict(sorted(counts.items()))


def _probable_channels(root: ET.Element) -> tuple[int, int]:
    channel_tag_count = 0
    ids: set[str] = set()
    max_numeric = 0
    for element in root.iter():
        tag = _local_name(element.tag)
        attrs = {str(key).lower(): value for key, value in element.attrib.items()}
        looks_like_channel = "channel" in tag or any(key in attrs for key in _CHANNEL_ATTRS)
        if not looks_like_channel:
            continue
        channel_tag_count += 1
        key = attrs.get("name") or attrs.get("id") or attrs.get("channel") or attrs.get("channelid") or attrs.get("circuit")
        if key is not None:
            ids.add(str(key))
        for attr in _CHANNEL_ATTRS:
            value = _intish(attrs.get(attr))
            if value is not None:
                max_numeric = max(max_numeric, value)
    probable = max(len(ids), max_numeric, channel_tag_count)
    return probable, channel_tag_count


def _event_like_count(root: ET.Element) -> tuple[int, int]:
    event_tags: Counter[str] = Counter()
    for element in root.iter():
        tag = _local_name(element.tag)
        blob = _element_text_blob(element)
        if tag in {"effect", "event", "channel", "timing", "interval"} or any(token in blob for tokens in _EFFECT_HINTS.values() for token in tokens):
            event_tags[tag] += 1
    return sum(event_tags.values()), len(event_tags)


def inspect_lms(path: str | Path) -> LmsInspectionReport:
    source = Path(path)
    warnings: list[str] = []
    if not source.exists():
        return LmsInspectionReport(source_path=str(source), warnings=[f"Missing LMS file: {source}"])

    try:
        root = ET.parse(source).getroot()
    except ET.ParseError as exc:
        return LmsInspectionReport(
            source_path=str(source),
            file_size_bytes=source.stat().st_size,
            warnings=[f"Could not parse LMS XML: {exc}"],
        )

    tag_counts = Counter(_local_name(element.tag) for element in root.iter())
    common_tags = dict(tag_counts.most_common(15))
    probable_channels, channel_tag_count = _probable_channels(root)
    event_count, unique_event_tags = _event_like_count(root)
    times = _extract_time_values(root)
    duration = _duration_from_values(times)
    if probable_channels == 0:
        warnings.append("No obvious channel definitions found.")
    if duration == 0.0:
        warnings.append("No obvious LMS timing/duration values found.")
    density = round(event_count / duration, 4) if duration > 0 else 0.0

    return LmsInspectionReport(
        source_path=str(source),
        file_size_bytes=source.stat().st_size,
        xml_root=_local_name(root.tag),
        probable_channel_count=probable_channels,
        channel_tag_count=channel_tag_count,
        event_like_tag_count=event_count,
        unique_event_tag_count=unique_event_tags,
        probable_duration_seconds=duration,
        timing_density_events_per_second=density,
        effect_hints=_count_effect_hints(root),
        common_tags=common_tags,
        warnings=warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a local Light-O-Rama LMS file for Helix legacy calibration.")
    parser.add_argument("lms_file")
    parser.add_argument("--output", help="Optional JSON output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = inspect_lms(Path(args.lms_file))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.to_json() + "\n", encoding="utf-8")
        print({"output": str(output)})
    else:
        print(report.to_json())
    return 0 if not any(item.startswith("Missing") or item.startswith("Could not parse") for item in report.warnings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
