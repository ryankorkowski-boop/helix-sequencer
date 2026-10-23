"""Bind existing production musician cues to literal canonical native surfaces.

This adapter does not analyze audio, infer stems, transpose pitches or generate
events. Source detector confidence/limitations remain in the retained band plan.
"""
import xml.etree.ElementTree as ET
from xlights.xsq_writer import EffectTemplate, add_effect


def refresh_models(garden, layout):
    from tools.build_helpers.ultimate_showcase import model_xml
    tree=ET.parse(layout)
    models=tree.find('models')
    for child in list(models):models.remove(child)
    for model in garden.models:models.append(model_xml(model))
    tree.write(layout,encoding='utf-8',xml_declaration=True)


def export_instruments(root, garden, plan):
    duration = round(float(root.findtext('head/sequenceDuration')) * 1000)
    elements = root.find('ElementEffects')
    report = dict(source='retained production snowman_band plan', detected_instrument_identity_verified=False,
                  transposed_notes=0, models={})
    for model in garden.models:
        role = model.details.get('review_role')
        if role not in ('bass', 'guitar', 'piano'):
            continue
        # Dedicated surface lanes own performance; remove generic BODY/notes
        # placement so source strings and keys cannot be hidden by broad effects.
        for el in list(elements):
            if el.get('name') == model.name or el.get('name','').startswith(model.name+'/'):
                elements.remove(el)
        displays = root.find('DisplayElements')
        for el in list(displays):
            if el.get('name') == model.name or el.get('name','').startswith(model.name+'/'):
                displays.remove(el)
        # xLights needs the real parent model in DisplayElements even when
        # every musical effect is placed on a dedicated submodel row.
        ET.SubElement(displays,'Element',type='model',name=model.name,visible='1',collapsed='1')
        parent=ET.SubElement(elements,'Element',type='model',name=model.name)
        ET.SubElement(parent,'EffectLayer')
        layers, windows = {}, {}
        def cue(part, source, color, strength=1):
            if not model.submodels.get(part):
                return False
            a, b = int(source['start_ms']), min(duration, int(source['end_ms']))
            if not 0 <= a < b <= duration:
                raise ValueError('Invalid production musician clock')
            if part not in layers:
                el=ET.SubElement(elements,'Element',name=model.name+'/'+part,type='model')
                layers[part]=ET.SubElement(el,'EffectLayer')
            bright=round(max(.05,min(1,float(strength)))*100)
            e=add_effect(layers[part],a,b,'On',EffectTemplate(
                settings=f'E_TEXTCTRL_Eff_On_Start={bright},E_TEXTCTRL_Eff_On_End={max(3,round(bright*.28))}',
                palette=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'))
            e.set('sourceMethod','retained_production_band_plan')
            e.set('sourceStartMs',str(a)); e.set('sourceEndMs',str(b))
            windows.setdefault(part,[]).append((a,b))
            return True
        counts=dict(source_events=0, mapped_events=0, unmapped_pitch_events=0)
        key={'bass':'bassist','guitar':'guitarist','piano':'keyboardist'}[role]
        for source in plan.get('cues',{}).get(key,[]):
            counts['source_events']+=1
            level=source.get('velocity',source.get('expression',{}).get('brightness',.8))
            if role=='piano':
                pitch=float(source['pitch_midi'])
                if pitch != round(pitch):
                    counts['unmapped_pitch_events']+=1; continue
                parts=['NOTE_MIDI_'+str(round(pitch))]
            elif role=='bass':
                parts=['STRING_'+str(int(source.get('string_index',1))-1)]
            elif source.get('kind')=='chord_change':
                # A fret change alone is not an acoustic attack.
                continue
            elif source.get('kind')=='strum':
                parts=['STRING_'+str(i) for i in range(6)]
            else:
                pitch=source.get('pitch_midi',64)
                tuning=(40,45,50,55,59,64)
                possible=[i for i,p in enumerate(tuning) if 0 <= pitch-p <= 24]
                if not possible:
                    counts['unmapped_pitch_events']+=1; continue
                parts=['STRING_'+str(possible[-1])]
            mapped=any([cue(p,source,'#FFF1AD' if role!='piano' else '#81EDFF',level) for p in parts])
            counts['mapped_events']+=int(mapped)
            if not mapped:
                counts['unmapped_pitch_events']+=1
            if mapped:
                side = ('LEFT' if source.get('pitch_midi',60)<66 else 'RIGHT') if role=='piano' else ('STRUM' if role=='guitar' else 'PLUCK')
                cue('ARM_'+side+'_ACTIVE',source,'#C5D6DD',.9)
        # Rest complements keep source-timed contact and idle poses exclusive.
        for part in model.submodels:
            if not part.endswith('_IDLE') or not part.startswith('ARM_'):
                continue
            active=part.removesuffix('_IDLE')+'_ACTIVE'
            cursor=0
            for a,b in sorted(windows.get(active,[])):
                if a>cursor:cue(part,dict(start_ms=cursor,end_ms=a),'#BFA485',.65)
                cursor=max(cursor,b)
            if cursor<duration:cue(part,dict(start_ms=cursor,end_ms=duration),'#BFA485',.65)
        for part,nodes in list(model.submodels.items()):
            if not nodes or not part.startswith(('NOTE_MIDI_','STRING_')):continue
            alias='INSTRUMENT_IDLE_'+part
            model.submodels[alias]=list(nodes)
            cursor=0
            for a,b in sorted(windows.get(part,[])):
                if a>cursor:cue(alias,dict(start_ms=cursor,end_ms=a),'#A8C1CE',.22)
                cursor=max(cursor,b)
            if cursor<duration:cue(alias,dict(start_ms=cursor,end_ms=duration),'#A8C1CE',.22)
        report['models'][model.name]=counts
    report['limitations']=['Pitch outside the authored48–84 keyboard range is omitted, never octave-folded',
                          'Native two-pose arm banks use fixed shoulders; continuous contact motion unverified',
                          'Mixed-bus production instrument labels are estimates, not isolated-stem ground truth']
    return report
