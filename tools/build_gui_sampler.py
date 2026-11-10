"""Build the portable comparison sampler from existing native layout generators."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import json
from models.approval_layouts import build_layout
from models.ultimate_showcase import Garden
from models.showcase_flavors import _move
from tools.phoneme_vocal_export import static_materials
from tools.build_helpers.ultimate_showcase import model_xml


def build(output):
    g = Garden(title='Layout sampler with canonical band')
    panels = ((1, '16 channel AC', -60, 55), (2, '64 channel AC', 60, 55),
              (4, 'RGB arches and trees', -60, -15), (7, 'Canonical six-member band', 60, -15))
    for number, title, x, y in panels:
        scene = build_layout(number, full_keyboard=True)
        band = [m for m in scene.models if m.details.get('review_role')]
        if band:
            from types import SimpleNamespace
            static_materials(SimpleNamespace(models=band))
        points = np.concatenate([m.points for m in scene.models])
        center = (points.min(0) + points.max(0)) / 2
        factor = min(100 / max(np.ptp(points[:, 0]), 1), 48 / max(np.ptp(points[:, 1]), 1))
        for m in scene.models:
            _move(m, center, (x, y, 0), factor)
            if not m.details.get('review_role'):
                m.name = f'SAMPLE_{number}_' + m.name
            m.attrs['HelixSamplerPanel'] = title
            if not m.details.get('review_role'):
                m.attrs['HelixSamplerDetails'] = json.dumps(dict(zone=m.zone, kind=m.kind, details=m.details), separators=(',', ':'))
            if m.details.get('review_role'):
                m.attrs['HelixBandRole'] = m.details['review_role']
                m.attrs['HelixGuiBand'] = 'canonical-v1'
                # Preserve contact poses and original key metadata without runtime mesh generation.
                m.attrs['HelixBandDetails'] = json.dumps(m.details, separators=(',', ':'))
            g.models.append(m)
    root = ET.Element('xrgb')
    models = ET.SubElement(root, 'models')
    start = 1
    for m in g.models:
        m.start = start
        start += m.channels
        models.append(model_xml(m))
    ET.SubElement(root, 'modelGroups')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output, encoding='utf-8', xml_declaration=True)
    return len(g.models)


if __name__ == '__main__':
    print(build(Path(__file__).resolve().parents[1] / 'showcase/Layout_Sampler/xlights_rgbeffects.xml'))
