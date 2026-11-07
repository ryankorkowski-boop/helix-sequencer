"""Make the original AC circuits legible without rewriting musical events.

The master sequence is authored against the original physical layout first.
Only its native preview geometry changes: each virtual bulb still samples the
same single original circuit. No demonstration or replacement effects exist.
"""
from pathlib import Path
import argparse
import copy
import json
import xml.etree.ElementTree as ET

import numpy as np

from core.model_parser import parse_layout
from tools.build_source_ac_review import geometry
from tools.build_helpers.ultimate_showcase import write_layout
from tools.phoneme_source import digest


def prepare(source: Path, sequence: Path, output: Path) -> dict:
    source, sequence, output = map(Path, (source, sequence, output))
    if source.resolve() == (output / 'xlights_rgbeffects.xml').resolve():
        raise ValueError('Original physical layout must remain separate and read-only')
    source_sha, sequence_sha = digest(source), digest(sequence)
    original = {m.name: m for m in parse_layout(source).models.values() if not m.is_submodel}
    garden = geometry(source)
    garden.title = "Greg's original 256-channel AC layout"
    expected = {m.name for m in garden.models}
    source_groups = ET.parse(source).find('modelGroups')
    group_names = {e.get('name') for e in source_groups} if source_groups is not None else set()
    names = {e.get('name') for e in ET.parse(sequence).findall('./ElementEffects/Element')
             if e.get('type') == 'model' and any(True for _ in e.iter('Effect'))}
    if names - expected - group_names:
        raise ValueError('Sequence references models outside the original AC circuits')
    write_layout(garden, output, include_demo=False, export_all_custom=True)
    layout = output / 'xlights_rgbeffects.xml'
    tree = ET.parse(layout)
    if source_groups is not None:
        tree.getroot().remove(tree.find('modelGroups'))
        tree.getroot().append(copy.deepcopy(source_groups))
    points = np.concatenate([m.points for m in garden.models])
    low, high = points.min(0), points.max(0)
    center, span = (low + high) / 2, high - low
    for camera in tree.findall('./Viewpoints/*'):
        for key, value in dict(angleX=5, angleY=0,
                               distance=-max(span[0] * .85, span[1] * 1.7, 55),
                               panx=-center[0], pany=-center[1], panz=-center[2]).items():
            camera.set(key, str(value))
    tree.write(layout, encoding='utf-8', xml_declaration=True)
    rendered = {m.name: m for m in parse_layout(layout).models.values() if not m.is_submodel}
    for name, model in original.items():
        preview = rendered[name]
        if (preview.start_channel != model.start_channel
                or (model.color_family in {'red', 'green', 'white'}
                    and preview.color_family != model.color_family)
                or not preview.is_single_color()):
            raise ValueError('Preview changed physical circuit mapping: ' + name)
    if len(rendered) != 256 or digest(source) != source_sha or digest(sequence) != sequence_sha:
        raise ValueError('Original circuit inventory or source bytes changed')
    report = dict(schema='helix.drive-ac-preview.v1', physical_channels=256,
                  source_layout_sha256=source_sha, sequence_sha256=sequence_sha,
                  preview_layout_sha256=digest(layout), musical_effects_unchanged=True,
                  original_addresses_and_fixed_colors_preserved=True,
                  inherited_preview_color_fallbacks=[dict(name=m.name,
                      source_string_type=m.string_type, preview_string_type=rendered[m.name].string_type)
                      for m in original.values() if m.color_family not in {'red', 'green', 'white'}],
                  geometry='Existing virtual bulbs, source spiral circuits, fitted front camera',
                  owner_approved=False)
    (output / 'preview_mapping.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'sequence', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.sequence, args.output), indent=2))
