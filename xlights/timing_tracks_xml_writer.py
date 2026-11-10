"""Export separate Helix timing tracks to xLights-facing XML.

This preserves independent timing lanes such as energy, beats, lyrics, vocals,
buildups, and drops instead of flattening them into one track.
"""

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from tools.audio_timing_tracks import TimingTrackSet


def build_timing_tracks_xml(track_set: TimingTrackSet) -> ET.Element:
    """Build XML preserving every timing track separately."""

    root = ET.Element("HelixTimingTracks", {"version": "1", "source": "helix-audio-intelligence"})

    for track in track_set.tracks:
        track_el = ET.SubElement(
            root,
            "TimingTrack",
            {
                "name": track.name,
                "kind": track.kind,
                "source": track.source,
                "count": str(len(track.segments)),
            },
        )

        for index, segment in enumerate(track.segments):
            ET.SubElement(
                track_el,
                "TimingMark",
                {
                    "id": str(index + 1),
                    "start": f"{float(segment.start):.3f}",
                    "end": f"{float(segment.start) + float(segment.duration):.3f}",
                    "duration": f"{float(segment.duration):.3f}",
                    "section": str(segment.section),
                    "eventType": str(segment.event_type),
                    "energy": f"{float(segment.energy):.3f}",
                    "beatStrength": f"{float(segment.beat_strength):.3f}",
                    "onsetDensity": f"{float(segment.onset_density):.3f}",
                    "bassEnergy": f"{float(segment.bass_energy):.3f}",
                    "vocalPresence": f"{float(segment.vocal_presence):.3f}",
                },
            )

    return root


def write_timing_tracks_xml(track_set: TimingTrackSet, output_path: str | Path) -> Path:
    """Write separate timing tracks to XML."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    root = build_timing_tracks_xml(track_set)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path
