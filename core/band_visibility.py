"""Filter band performers in a private show copy, preserving circuit addresses."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PERFORMER = re.compile(
    r'^HX_SNOW_(?:DRUMMER|BASS|GUITAR|PIANO|LEAD|HARMONY)(?:$|_)|'
    r'^HX_SNOWMAN_(?:DRUMMER|BASSIST|GUITARIST|KEYBOARDIST|XYLOPHONIST|SINGER)(?:$|_)',
    re.IGNORECASE)


def is_band_model(model):
    return bool(PERFORMER.match(model.get('name', '')) or
                model.get('HelixPerformerRole') or model.get('HelixBandRole'))


def apply(layout, template=None, *, enabled=True):
    """Enabled preserves input bytes; disabled retains scenery/unrelated faces."""
    report = dict(enabled=bool(enabled), removed_models=[], removed_empty_groups=[], removed_template_rows=0)
    if enabled:
        return report
    layout = Path(layout)
    tree = ET.parse(layout)
    models = tree.find('models')
    if models is None:
        raise ValueError('Band switch requires an xLights layout with a models element')
    removed = {model.get('name') for model in models if is_band_model(model)}
    if not removed:
        return report
    for model in list(models):
        if model.get('name') in removed:
            models.remove(model)
    report['removed_models'] = sorted(removed)
    groups = tree.find('modelGroups')
    if groups is not None:
        changed = True
        while changed:
            changed = False
            for group in list(groups):
                names = [name.strip() for name in group.get('models', '').split(',') if name.strip()]
                retained = [name for name in names if name.split('/', 1)[0] not in removed]
                group.set('models', ','.join(retained))
                if names and not retained:
                    name = group.get('name')
                    removed.add(name); report['removed_empty_groups'].append(name)
                    groups.remove(group); changed = True
    tree.write(layout, encoding='utf-8', xml_declaration=True)
    if template is not None and Path(template).is_file():
        template = Path(template)
        sequence = ET.parse(template)
        for section in ('DisplayElements', 'ElementEffects'):
            container = sequence.find(section)
            if container is not None:
                for element in list(container):
                    if element.get('name', '').split('/', 1)[0] in removed:
                        container.remove(element)
                        report['removed_template_rows'] += 1
        sequence.write(template, encoding='utf-8', xml_declaration=True)
    return report
