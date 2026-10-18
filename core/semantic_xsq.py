"""Compile semantic intents onto explicitly selected scenic RGB models.

Original model layers are retained byte-for-byte as XML subtrees. Physical
performers, submodels, groups, and control-only fixtures are never targets.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from typing import Mapping, Any

from core.lyric_evidence import number, probability
from helix_style.palette_engine import palette_for_emotion


PROTECTED = re.compile(r'drum|snare|kick|cymbal|hi.?hat|guitar|bass|keyboard|piano|xylo|mallet|singer|vocal|snowman|performer|\bhx_snow', re.I)


def append_direction(root: ET.Element, direction: Mapping[str, Any], targets: list[str],
                     *, parsed_layout: Any, duration_ms: int) -> dict:
    if len(targets) != len(set(targets)):
        raise ValueError('Semantic scenery targets must be unique')
    models = getattr(parsed_layout, 'models', {})
    for name in targets:
        model = models.get(name)
        if (model is None or getattr(model, 'is_submodel', False) or PROTECTED.search(name)
                or not model.is_pixel_model() or not model.is_rgb_capable()):
            raise ValueError('Semantic target must be a scenic RGB root model: '+name)
    elements = root.find('ElementEffects')
    if elements is None:
        raise ValueError('Sequence lacks ElementEffects')
    db, palettes = root.find('EffectDB'), root.find('ColorPalettes')
    native = db is not None and palettes is not None and any(e.get('ref') is not None for e in root.findall('.//Effect'))
    existing_ids = [int(e.get('id')) for e in root.findall('.//Effect') if str(e.get('id','')).isdigit()]
    next_id = max(existing_ids, default=0)+1
    layers, schedule, last_end, rejected = {}, [], {}, []
    for intent in direction.get('intents', []):
        confidence = probability(intent.get('metadata',{}).get('confidence',0))
        if confidence < .65 or not targets:
            continue
        start = max(0, round(number(intent['start'])*1000))
        end = min(duration_ms, round((number(intent['start'])+number(intent['duration']))*1000))
        if end <= start:
            continue
        emotion = intent['metadata']['emotion']
        valence = number(emotion.get('valence'))
        colors = palette_for_emotion('dark' if valence < -.15 else 'calm' if emotion['arousal'] < .4 else 'bright')
        intensity = min(.55, probability(intent['intensity']))
        count = max(1, min(len(targets), round(len(targets)*probability(intent.get('density_budget',.3)))))
        concept = intent['event_type'].removeprefix('semantic_')
        # A motif keeps its identity; negative passages retain spatial isolation.
        motif = intent['metadata']['motif']
        reverse = concept in ('winter','separation')
        ordered = list(reversed(targets)) if reverse else targets
        if concept in ('connection','resolution','hope'):
            ordered = sorted(targets, key=lambda name:abs(targets.index(name)-(len(targets)-1)/2))
        selected = ordered[:count]
        for index,name in enumerate(selected):
            # Traversal is inside the phrase; instrument timestamps never snap.
            offset = round((end-start)*.35*index/max(1,count))
            a,b=start+offset,end
            if b<=a:
                continue
            if a < last_end.get(name, -1):
                rejected.append(dict(model=name,start_ms=a,reason='overlapping_semantic_phrase'))
                continue
            element = next((e for e in elements if e.get('name')==name), None)
            if element is None:
                element = ET.SubElement(elements,'Element',{'type':'model','name':name})
            if name not in layers:
                layers[name]=ET.SubElement(element,'EffectLayer')
            # On envelopes are native on every RGB geometry; spatial motion is
            # expressed by the ordered prop activation, without guessed shaders.
            rising = concept in ('hope','connection','resolution','celebration')
            level=round(intensity*100)
            settings=f'E_TEXTCTRL_Eff_On_Start={max(8,level//3) if rising else level},E_TEXTCTRL_Eff_On_End={level if rising else 5}'
            color=colors[index%len(colors)]
            palette=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'
            attrs={'name':'On','startTime':str(a),'endTime':str(b),'id':str(next_id)};next_id+=1
            if native:
                attrs['ref']=str(len(db));ET.SubElement(db,'Effect').text=settings
                attrs['palette']=str(len(palettes));ET.SubElement(palettes,'ColorPalette').text=palette
            else:
                attrs['settings']=settings;attrs['palette']=palette
            ET.SubElement(layers[name],'Effect',attrs)
            last_end[name]=b
            schedule.append(dict(model=name,start_ms=a,end_ms=b,concept=concept,motif=motif,
                                 confidence=confidence,layer='semantic_scenery',source='semantic_story'))
    return dict(schema='helix.semantic_xsq.v1',effects=len(schedule),schedule=schedule,
                selected_targets=targets,instrument_layers_modified=False,rejected=rejected,
                limitations=['Native On envelopes and inter-prop traversal; no claim of particle/shader synthesis.'])
