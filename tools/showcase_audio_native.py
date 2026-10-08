"""Bind real Helix Prime placements to the verified native showcase XML schema."""
from __future__ import annotations

from copy import deepcopy
from collections import Counter, defaultdict
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase import write_layout


def prepare_template(g: Garden, folder: Path) -> Path:
    """A clean, layout-specific template; one zero-length library seed only.

    The engine reads native defaults/palette strings from the seed and removes
    its startup blip. No 24-second demonstration effects or timing survive.
    """
    write_layout(g, folder)
    path=folder/(g.slug+"_Showcase.xsq");root=ET.parse(path).getroot()
    for layer in root.findall('.//EffectLayer')+root.findall('.//SubModelEffectLayer'):
        for effect in list(layer):layer.remove(effect)
    root.find('head/comment').text='Clean Helix Prime music template; no demonstration choreography.'
    first=root.find('ElementEffects/Element/EffectLayer')
    ET.SubElement(first,'Effect',{'name':'On','startTime':'0','endTime':'1',
        'settings':'E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100',
        'palette':f'C_BUTTON_Palette1={g.palette[0]},C_CHECKBOX_Palette1=1'})
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
    return path


def native_music_xsq(raw: Path, output: Path, g: Garden, audio: Path, duration_s: float) -> dict:
    """Keep timings/families; correct duration, native references and targets.

    General engine flat model/submodel rows become direct SubModelEffectLayer
    children. RGB palettes come from each target's authored color. Control-only
    groups/targets are excluded; mixed groups become equivalent pixel-only
    groups in this separate generated show, without changing model geometry.
    """
    source=ET.parse(raw).getroot()
    # Prime's numeric-name discovery can omit a negative-side member. For a
    # paired artistic RGB motif only, mirror its already audio-driven sibling
    # choreography. Keep attacks/durations/effect settings and give the copied
    # target its own authored palette. Never do this for physical instruments
    # or control fixtures, and never overwrite an independently routed target.
    source_rows={e.get('name'):e for e in source.findall('ElementEffects/Element')}
    mirrored=[]
    for model in g.models:
        if model.kind!='pixel' or '_-1' not in model.name:continue
        if not any(token in model.name for token in ('_CANDY_GARDEN_','_FRACTAL_SNOWFLAKE_','_CROWN_')):continue
        sibling_name=model.name.replace('_-1','_1',1)
        sibling=next((m for m in g.models if m.name==sibling_name and m.kind=='pixel' and m.display==model.display),None)
        row=source_rows.get(model.name);other=source_rows.get(sibling_name)
        if sibling is None or other is None or not other.findall('.//Effect'):continue
        if row is not None and row.findall('.//Effect'):continue
        copy=deepcopy(other);copy.set('name',model.name)
        if row is not None:source.find('ElementEffects').remove(row)
        source.find('ElementEffects').append(copy)
        mirrored.append({'source':sibling_name,'target':model.name,'effects':len(copy.findall('.//Effect'))})
    root=deepcopy(source)
    step=50;duration_ms=int(math.ceil(duration_s*1000/step)*step)
    for name,value in {'song':audio.stem,'comment':'Helix Prime full-song audio-driven showcase; native channel preview.',
                       'sequenceType':'Media','sequenceDuration':f'{duration_ms/1000:.3f}',
                       'sequenceTiming':'50 ms','mediaFile':audio.name}.items():
        head=root.find('head');node=head.find(name)
        if node is None:node=ET.SubElement(head,name)
        node.text=value
    models={m.name:m for m in g.models};pixel={m.name for m in g.models if m.kind=='pixel'}
    groups=ET.parse(output.parent/'xlights_rgbeffects.xml').getroot().find('modelGroups')
    members={e.get('name'):e.get('models','').split(',') for e in groups}
    def resolve(name,seen=frozenset()):
        if name in seen:return []
        if name in members:return [leaf for child in members[name] for leaf in resolve(child,seen|{name})]
        return [name] if name.split('/')[0] in pixel else []
    # Redefine only mixed generated-show groups, never physical node/channel XML.
    changed_groups=[]
    for node in groups:
        name=node.get('name');leaves=resolve(name)
        if leaves and any(not resolve(n) for n in members[name]):
            node.set('models',','.join(dict.fromkeys(leaves)));changed_groups.append(name)
    if changed_groups:
        layout=ET.parse(output.parent/'xlights_rgbeffects.xml')
        actual=layout.getroot().find('modelGroups')
        for node in actual:
            if node.get('name') in changed_groups:node.set('models',next(n.get('models') for n in groups if n.get('name')==node.get('name')))
        layout.write(output.parent/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
    elements=root.find('ElementEffects');displays=root.find('DisplayElements')
    elements.clear();displays.clear()
    db=root.find('EffectDB');palettes=root.find('ColorPalettes');db.clear();palettes.clear()
    setting_ids={};palette_ids={};parents={};layer_numbers=defaultdict(int);counts=Counter();skipped=Counter();identifier=1
    def palette(color):
        if color not in palette_ids:
            palette_ids[color]=len(palette_ids)
            ET.SubElement(palettes,'ColorPalette').text=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'
        return palette_ids[color]
    def setting(text):
        if text not in setting_ids:
            setting_ids[text]=len(setting_ids);ET.SubElement(db,'Effect').text=text
        return setting_ids[text]
    for row in source.findall('ElementEffects/Element'):
        name=row.get('name','');kind=row.get('type','model')
        if kind=='timing':
            elements.append(deepcopy(row));ET.SubElement(displays,'Element',{'type':'timing','name':name,'visible':'0','active':'0'});continue
        leaves=resolve(name)
        if not leaves:skipped['control_or_unresolved_targets']+=len(row.findall('.//Effect'));continue
        parent,sep,part=name.partition('/')
        if parent not in parents:
            parents[parent]=ET.SubElement(elements,'Element',{'type':'model','name':parent})
            ET.SubElement(displays,'Element',{'type':'model','name':parent,'visible':'1','collapsed':'1'})
        for original_layer in row:
            if original_layer.tag not in ('EffectLayer','SubModelEffectLayer'):continue
            sub=part if sep else original_layer.get('name') if original_layer.tag=='SubModelEffectLayer' else ''
            key=(parent,sub);number=layer_numbers[key];layer_numbers[key]+=1
            layer=ET.SubElement(parents[parent],'SubModelEffectLayer',{'name':sub,'layer':str(number)}) if sub else ET.SubElement(parents[parent],'EffectLayer')
            model=models.get(parent)
            color=g.palette[0]
            if model:
                nodes=model.submodels.get(sub,[]) if sub else []
                color=model.colors[nodes[0]-1] if nodes else model.colors[0]
            for original in original_layer.findall('Effect'):
                start=max(0,int(original.get('startTime','0')));end=min(duration_ms,int(original.get('endTime','0')))
                if end<=start:skipped['invalid_timing']+=1;continue
                effect_name=original.get('name','On');text=original.get('settings',original.text or '')
                # These engine choices need an actual native content source.
                if effect_name=='Pictures' and 'E_FILEPICKER_Pictures_Filename' not in text:
                    text+=',E_FILEPICKER_Pictures_Filename=assets/helix_crest.png'
                if effect_name=='Text' and 'E_TEXTCTRL_Text_Line1' not in text:
                    text+=',E_TEXTCTRL_Text_Line1=HELIX'
                attrs={'name':effect_name,'startTime':str(start),'endTime':str(end),
                       'ref':str(setting(text.strip(','))),'palette':str(palette(color)),'id':str(identifier)}
                ET.SubElement(layer,'Effect',attrs);identifier+=1;counts[effect_name]+=1
    root.find('nextid').text=str(identifier)
    ET.indent(root);ET.ElementTree(root).write(output,encoding='utf-8',xml_declaration=True)
    return {'duration_ms':duration_ms,'native_effects':sum(counts.values()),'effect_families':dict(counts),
            'skipped':dict(skipped),'mixed_groups_restricted_to_pixels':changed_groups,'source_events_retimed':False,
            'mirrored_rgb_motifs':mirrored}
