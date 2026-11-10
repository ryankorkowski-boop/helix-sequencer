"""Private GUI show preparation and canonical performance export.

No detector is replaced. The retained engine band plan supplies every musical cue.
"""
from __future__ import annotations
import copy
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from core.band_visibility import apply, is_band_model
from core.preview_geometry import custom_nodes, node_ranges


def prepare(layout, template, output, root, *, enabled=True):
    """Keep input files immutable; Band on adds the packaged canonical cast."""
    folder = Path(tempfile.mkdtemp(prefix='show-', dir=_workspace(output)))
    target, seed = folder/'xlights_rgbeffects.xml', folder/'template.xsq'
    shutil.copy2(layout, target)
    shutil.copy2(template, seed)
    network = Path(layout).parent/'xlights_networks.xml'
    if network.is_file():
        shutil.copy2(network, folder/network.name)
    assets = Path(layout).parent/'assets'
    if assets.is_dir():
        shutil.copytree(assets, folder/'assets')
    report = configure(target, seed, root, enabled=enabled)
    return target, seed, report


def _workspace(output):
    folder = Path(output).resolve()/'.helix_gui_workspace'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def configure(layout, template, root, *, enabled=True):
    if not enabled:
        return apply(layout, template, enabled=False)
    tree = ET.parse(layout)
    models = tree.find('models')
    if models is None:
        raise ValueError('Band selection requires an xLights models element')
    existing = [m for m in models if is_band_model(m)]
    replaced = []
    if existing:
        if any(m.get('CustomModel') or m.get('CustomModelCompressed') or m.get('PointData') for m in existing):
            return dict(enabled=True, added_models=[], existing_models=[m.get('name') for m in existing])
        # Historical built-in band stubs contain no authored nodes. Keeping them
        # made Band on a no-op and left only approximate rectangles in previews.
        replaced = apply(layout, template, enabled=False)['removed_models']
        tree = ET.parse(layout)
        models = tree.find('models')
    from core.gui_options import resolve_layout
    sampler = ET.parse(resolve_layout(Path(root), 'layout_sampler'))
    band = [copy.deepcopy(m) for m in sampler.findall('models/model') if m.get('HelixGuiBand') == 'canonical-v1']
    if len(band) != 6:
        raise ValueError('Packaged canonical band must have six members')
    from core.controller_parser import layout_channel_count
    end = layout_channel_count(Path(layout))
    for m in models:
        if not m.get('StartChannel', '1').isdigit():
            raise ValueError('Add band requires absolute channel addresses; choose the bundled sampler or a band-enabled layout')
        nodes = custom_nodes(m)
        if nodes:
            channels = max(n for n,_ in nodes) * (3 if 'RGB' in m.get('StringType','').upper() else 1)
            end = max(end, int(m.get('StartChannel','1')) + channels - 1)
    # Place the cast beside the original display, keeping every imported circuit fixed.
    from tools.preview_renderer import parse_models
    bounds = parse_models(Path(layout)).bounds
    points = [p for m in band for _,p in custom_nodes(m)]
    shift_x = bounds[2] + 8 - min(p[0] for p in points)
    shift_y = bounds[1] - min(p[1] for p in points)
    for m in band:
        m.set('WorldPosX', str(float(m.get('WorldPosX','0'))+shift_x))
        m.set('WorldPosY', str(float(m.get('WorldPosY','0'))+shift_y))
        m.set('StartChannel', str(end+1))
        end += max(n for n,_ in custom_nodes(m))*3
        models.append(m)
    tree.write(layout, encoding='utf-8', xml_declaration=True)
    return dict(enabled=True, added_models=[m.get('name') for m in band], replaced_missing_geometry_models=replaced)


def apply_performance(sequence, layout):
    """Bind GUI canonical surfaces to the exact variant's production plan."""
    layout_tree = ET.parse(layout)
    definitions = [m for m in layout_tree.findall('models/model') if m.get('HelixGuiBand') == 'canonical-v1']
    if not definitions and not layout_tree.findall('models/model[@HelixSamplerDetails]'):
        return None
    sequence = Path(sequence)
    plan_file = sequence.with_name(sequence.stem+'.snowman_band.json')
    if not plan_file.is_file():
        raise RuntimeError('Canonical GUI band requires this variant’s production band plan')
    plan = json.loads(plan_file.read_text())
    root = ET.parse(sequence).getroot()
    duration = round(float(root.findtext('head/sequenceDuration'))*1000)
    models = [SimpleNamespace(name=m.get('name'), details=json.loads(m.get('HelixBandDetails')),
                 submodels={s.get('name'): sorted(set().union(*(node_ranges(v) for k,v in s.attrib.items() if k.startswith('line'))))
                            for s in m.findall('subModel')}) for m in definitions]
    garden = SimpleNamespace(models=models)
    # Default comparison props use the same retained plan as the band, with
    # spatially distinct parts and actual fixed-color AC node assignments.
    import numpy as np
    from tools.source_spatial_direction import schedule, role_for, section_color
    from xlights.xsq_writer import add_effect, EffectTemplate
    for definition in layout_tree.findall('models/model'):
        metadata = definition.get('HelixSamplerDetails')
        if not metadata:
            continue
        data = json.loads(metadata)
        name = definition.get('name')
        model = SimpleNamespace(name=name, zone=data['zone'], kind=data['kind'], attrs=definition.attrib,
            details=data['details'], display=definition.get('DisplayAs'),
            points=np.asarray([p for _,p in custom_nodes(definition)]) if definition.get('DisplayAs')=='Custom' else
                   np.asarray([(float(definition.get('WorldPosX','0')),float(definition.get('WorldPosY','0')),0)]),
            submodels={s.get('name'): sorted(node_ranges(s.get('line0',''))) for s in definition.findall('subModel')})
        if role_for(model) == 'harmony':
            model.details['musical_role'] = 'keyboardist'
        elements = root.find('ElementEffects')
        for element in list(elements):
            if element.get('name','').split('/',1)[0] == name:
                elements.remove(element)
        layers = {}
        for event in schedule(model, plan, {}, duration):
            part = event['part']
            if part not in layers:
                element = ET.SubElement(elements,'Element',name=name+'/'+part,type='model')
                layers[part] = ET.SubElement(element,'EffectLayer')
            fixed = {'Single Color Red':'#FF0000','Single Color Green':'#00FF00','Single Color White':'#FFFFFF'}
            color = fixed.get(model.attrs.get('StringType')) or section_color(event['role'],event['section'],('#56D9FF','#BA83F4','#FFD18A'))
            level = round(event['level']*100)
            effect = add_effect(layers[part],event['start_ms'],event['end_ms'],'On',EffectTemplate(
                settings=f'E_TEXTCTRL_Eff_On_Start={level},E_TEXTCTRL_Eff_On_End={max(1,round(level*.12))}',
                palette=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'))
            effect.set('sourceMethod','gui_sampler_retained_band_plan')
            effect.set('sourceStartMs',str(event['source_start_ms']))
            effect.set('sourceEndMs',str(event['source_end_ms']))
    from tools.canonical_band_cues import export_instruments, export_drums
    report = export_instruments(root, garden, plan) if models else {}
    if models:
        report['drummer'] = export_drums(root, garden, plan)
    from xlights.xsq_writer import add_effect, EffectTemplate
    from tools.build_helpers.ultimate_showcase import _ranges
    effects = root.find('ElementEffects')
    displays = root.find('DisplayElements')
    for model, definition in zip(models, definitions):
        if model.details['review_role'] in ('lead','harmony'):
            # Retain only independently generated native Faces; decorative body effects
            # would also illuminate every mutually exclusive mouth/arm pose.
            for element in list(effects):
                if element.get('name','').split('/',1)[0] != model.name:
                    continue
                for layer in list(element):
                    for effect in list(layer):
                        if effect.tag == 'Effect' and effect.get('name','').lower() != 'faces':
                            layer.remove(effect)
        for part, nodes in model.submodels.items():
            if part.startswith('STATIC_RGB_') and nodes:
                name = model.name+'/'+part
                element = ET.SubElement(effects,'Element',name=name,type='model')
                ET.SubElement(displays,'Element',name=name,type='model',visible='1')
                layer = ET.SubElement(element,'EffectLayer')
                add_effect(layer,0,duration,'On',EffectTemplate(
                    settings='E_TEXTCTRL_Eff_On_Start=65,E_TEXTCTRL_Eff_On_End=65',
                    palette='C_BUTTON_Palette1=#'+part.removeprefix('STATIC_RGB_')+',C_CHECKBOX_Palette1=1'))
            if not any(s.get('name') == part for s in definition.findall('subModel')):
                ET.SubElement(definition,'subModel',name=part,layout='horizontal',type='ranges',line0=_ranges(nodes))
    from xlights.xml_io import materialize_native_effect_tables
    materialize_native_effect_tables(root)
    ET.ElementTree(root).write(sequence, encoding='utf-8', xml_declaration=True)
    layout_tree.write(layout, encoding='utf-8', xml_declaration=True)
    sequence.with_suffix('.gui_band.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
