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


def inspect_band_stage(layout):
    """Identify stage presets that the ordinary effect-level renderer cannot depict."""
    layout = Path(layout)
    root = ET.parse(layout).getroot()
    expected = ('drummer', 'bass', 'guitar', 'piano', 'lead', 'harmony')
    models = root.findall('./models/model')
    names = {m.get('name', '') for m in models}
    found = [role for role in expected
             if 'HX_SNOW_' + role.upper() in names]
    if 'HX_SNOWMAN_DRUMMER_V3' in names and 'drummer' not in found:
        found.insert(0, 'drummer')
    if not root.findall("./modelGroups/modelGroup[@name='HX_ZONE_BAND']") and len(found) != len(expected):
        return None
    missing = [role for role in expected if role not in found]
    missing_assets = set()
    for model in models:
        if not is_band_model(model):
            continue
        for attribute in ('CustomBkgImage', 'HelixVisualSource', 'HelixReferenceImage'):
            resource = model.get(attribute)
            if resource and not (layout.parent / resource).is_file():
                missing_assets.add(resource)
    return {'models': len(models), 'present_roles': found, 'missing_roles': missing,
            'missing_assets': sorted(missing_assets), 'backend': 'effect-level simulation'}


def band_stage_preview_error(report):
    if report is None:
        return None
    errors = []
    if report['missing_roles']:
        errors.append('Band stage missing canonical models: ' + ', '.join(report['missing_roles']))
    if report['missing_assets']:
        errors.append('Missing band assets: ' + ', '.join(report['missing_assets']))
    return '. '.join(errors) or 'Six-member band previews require the canonical 3D renderer.'
