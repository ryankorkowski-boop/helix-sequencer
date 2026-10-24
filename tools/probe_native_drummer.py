"""Native connectivity proof for the unchanged canonical drummer geometry.

This four-second Animation sequence is a wiring test, not a musical performance.
No target stage or new artwork concept is chosen by this probe.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np

from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.render_drummer_v3_preview import TARGETS, _expand_ranges

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel'


def write(root: ET.Element, path: Path) -> None:
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def probe(output: Path, executable: Path) -> dict:
    if output.exists():
        raise FileExistsError(f'Refusing to replace existing probe: {output}')
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    (output / 'models').mkdir()
    (output / 'source').mkdir()
    shutil.copy2(SOURCE, output / 'models' / SOURCE.name)
    for name in ('drummer_idle.png', 'drummerbg.png'):
        shutil.copy2(SOURCE.parent.parent / 'source' / name, output / 'source' / name)
    source = ET.parse(SOURCE).getroot()
    layout = ET.parse(ROOT / 'showcase/Helix_Aurora/xlights_rgbeffects.xml').getroot()
    layout.find('models').clear()
    layout.find('modelGroups').clear()
    layout.find('views').clear()
    attrs = {**source.attrib, 'DisplayAs': 'Custom', 'StartChannel': '1', 'Controller': '',
             'LayoutGroup': 'Default', 'parm3': '1', 'StartSide': 'B', 'Dir': 'L',
             'versionNumber': '7', 'ModelBrightness': '100',
             'CustomBkgImage': 'source/drummer_idle.png', 'HelixVisualSource': 'source/drummerbg.png',
             'WorldPosX': '0', 'WorldPosY': '36', 'WorldPosZ': '0',
             'ScaleX': '1', 'ScaleY': '1', 'ScaleZ': '1'}
    model = ET.SubElement(layout.find('models'), 'model', attrs)
    submodels = {}
    for original in source.findall('subModels/subModel'):
        sub = deepcopy(original)
        sub.set('layout', 'horizontal')
        model.append(sub)
        submodels[sub.get('name')] = _expand_ranges(sub.get('line0', ''))
    write(layout, output / 'xlights_rgbeffects.xml')
    shutil.copy2(ROOT / 'showcase/Helix_Aurora/xlights_networks.xml', output / 'xlights_networks.xml')
    sequence = ET.parse(ROOT / 'showcase/Helix_Aurora/Helix_Aurora_Showcase.xsq').getroot()
    for tag in ('DisplayElements', 'ElementEffects', 'EffectDB', 'ColorPalettes'):
        sequence.find(tag).clear()
    for name, value in {'sequenceDuration': '4.000', 'sequenceType': 'Animation', 'mediaFile': '',
                        'comment': 'Canonical drummer native connectivity test; no musical performance.'}.items():
        sequence.find('head/' + name).text = value
    ET.SubElement(sequence.find('EffectDB'), 'Effect').text = 'E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100'
    ET.SubElement(sequence.find('ColorPalettes'), 'ColorPalette').text = 'C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
    name = source.get('name')
    ET.SubElement(sequence.find('DisplayElements'), 'Element', {'type': 'model', 'name': name, 'visible': '1', 'collapsed': '0'})
    parent = ET.SubElement(sequence.find('ElementEffects'), 'Element', {'type': 'model', 'name': name})
    for i, target in enumerate(TARGETS):
        layer = ET.SubElement(parent, 'SubModelEffectLayer', {'name': target, 'layer': '0'})
        ET.SubElement(layer, 'Effect', {'name': 'On', 'ref': '0', 'palette': '0',
                                      'startTime': str(i * 500), 'endTime': str((i + 1) * 500)})
    xsq = output / 'Drummer_Connectivity_Only.xsq'
    write(sequence, xsq)
    with (output / 'native_render.log').open('w') as log:
        subprocess.run([str(executable.resolve()), '--headless', '-q', '-s', str(output.resolve()),
                        '-od', str(output.resolve()), str(xsq.resolve())], stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
    frames, step = read_fseq(xsq.with_suffix('.fseq'))
    if len(frames) != 80 or step != 50 or frames.shape[1] != 96 * 72 * 3:
        raise ValueError('Unexpected native drummer frame/channel dimensions')
    rows = []
    for i, target in enumerate(TARGETS):
        rgb = frames[i * 10 + 5].reshape(-1, 3)
        lit = set((np.flatnonzero(rgb.max(axis=1)) + 1).tolist())
        if lit != submodels[target] or not np.all(rgb[list(n - 1 for n in lit)] == 255):
            raise ValueError(f'Native submodel did not match canonical target nodes: {target}')
        rows.append({'target': target, 'canonical_nodes': len(lit), 'native_nodes_match_exactly': True})
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != original_hash:
        raise ValueError('Canonical model source changed')
    result = {'schema': 'helix.native_drummer_connectivity.v1', 'source_xmodel_sha256': original_hash,
              'source_geometry_and_node_ranges_unchanged': True, 'native_frames': 80, 'frame_ms': step,
              'pixels': 6912, 'channels': 20736, 'visual_and_logical_submodels': len(submodels),
              'targets': rows, 'native_render': 'success', 'musical_performance': False,
              'output_absolute_path': str(output.resolve()), 'physical_output_networks': 0,
              'limits': 'Connectivity only. Stage placement, song-bound analysis, body keepalive and musical acceptance are separate.'}
    (output / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--xlights', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.output, args.xlights), indent=2))
