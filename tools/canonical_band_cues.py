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


def export_drums(root, garden, plan):
    """Route known detected components; never turn every drum into a tom.

    Use retained tom-class evidence when present; abstain when it is absent.
    Cymbal side and snare hand remain staging assignments, not acoustic facts.
    """
    model=next(m for m in garden.models if m.details.get('review_role')=='drummer')
    duration=round(float(root.findtext('head/sequenceDuration'))*1000)
    elements=root.find('ElementEffects');displays=root.find('DisplayElements')
    for container in (elements,displays):
        for child in list(container):
            if child.get('name')==model.name or child.get('name','').startswith(model.name+'/'):
                container.remove(child)
    ET.SubElement(displays,'Element',type='model',name=model.name,visible='1',collapsed='1')
    ET.SubElement(ET.SubElement(elements,'Element',type='model',name=model.name),'EffectLayer')
    layers={};windows={};counts={};unresolved=[]
    def emit(part,a,b,color,level,end_level=None,source=None):
        if not model.submodels.get(part) or b<=a:return
        if part not in layers:
            el=ET.SubElement(elements,'Element',type='model',name=model.name+'/'+part)
            layers[part]=ET.SubElement(el,'EffectLayer')
        # An actual strike must rise above the25% nonmusical kit visibility.
        display_level=.25+.75*level if source is not None else level
        bright=round(max(.01,min(1,display_level))*100)
        effect=add_effect(layers[part],a,min(b,duration),'On',EffectTemplate(
            settings=f'E_TEXTCTRL_Eff_On_Start={bright},E_TEXTCTRL_Eff_On_End={bright if end_level is None else round(end_level*100)}',
            palette=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'))
        effect.set('sourceMethod','retained_production_drum_plan' if source else 'nonmusical_kit_visibility')
        if source:
            effect.set('sourceComponent',part);effect.set('sourceStartMs',str(a))
        windows.setdefault(part,[]).append((a,b))
    prefix='HX_SNOWMAN_DRUMMER_V3_'
    snare_index = 0
    for cue in plan.get('cues',{}).get('drummer',[]):
        component={'kick':'KICK','snare':'SNARE','hihat':'HI_HAT','cymbal':'CYMBAL_RIGHT'}.get(cue['kind'])
        if cue['kind']=='tom':
            # The production plan retains the detector's physical tom class.
            # Do not discard it merely because the top-level kind is "tom",
            # and use the same class/alias contract as the production mapper.
            from audio.drum_classification import DrumEvent
            from mapping.drum_mapper import tom_class_for_event
            event=DrumEvent(timestamp=cue['start_ms']/1000,
                velocity=cue.get('velocity',.8),confidence=cue.get('confidence',0),
                frequency_band_info=cue.get('frequency_band_info',{}),
                cluster_id=cue.get('cluster_id'),drum_type='tom',source=cue.get('source','retained_plan'))
            try:
                component='TOM_'+{'high':'HIGH','mid':'MID','floor':'FLOOR'}[tom_class_for_event(event)]
            except ValueError:
                pass
        if component is None:
            unresolved.append(dict(start_ms=cue['start_ms'],kind=cue['kind'],reason='No localized tom identity in retained source plan'))
            continue
        a,b=int(cue['start_ms']),min(duration,int(cue['end_ms']))
        level=max(.1,min(1,float(cue.get('velocity',.8))))
        parts=[prefix+component+'_SURFACE']
        if component=='HI_HAT':parts.append(prefix+'HI_HAT_FOOT')
        elif component not in ('KICK',):
            pose=('SNARE_RIGHT' if snare_index%2 else 'SNARE') if component=='SNARE' else component
            parts += [prefix+pose+'_ARM_STICK_WOOD',prefix+pose+'_ARM_STICK_NEUTRAL']
        if component=='SNARE':snare_index+=1
        for part in parts:
            emit(part,a,b,'#E8C883' if 'CYMBAL' in component or component=='HI_HAT' else '#BFEAFF',level,max(.03,level*.15),source=cue)
        counts[component]=counts.get(component,0)+1
    # Each kit surface remains visible through genuine event complements.
    for component in ('KICK','SNARE','HI_HAT','TOM_HIGH','TOM_MID','TOM_FLOOR','CYMBAL_LEFT','CYMBAL_RIGHT'):
        part=prefix+component+'_SURFACE';cursor=0
        original=list(windows.get(part,[]))
        for a,b in sorted(original):
            if a>cursor:emit(part,cursor,a,'#A8BECB',.25)
            cursor=max(cursor,b)
        if cursor<duration:emit(part,cursor,duration,'#A8BECB',.25)
    return dict(source='retained production band plan',component_events=counts,
        unresolved_events=unresolved,hi_hat_is_foot_only=True,
        cymbal_side='right-side staging assignment; source side unverified',
        snare_hand='alternating visualization assignment; source hand unverified',
        event_timing_preserved=True,independent_component_ground_truth_verified=False)


def export_instruments(root, garden, plan):
    duration = round(float(root.findtext('head/sequenceDuration')) * 1000)
    elements = root.find('ElementEffects')
    report = dict(source='retained production snowman_band plan', detected_instrument_identity_verified=False,
                  transposed_notes=0, models={})
    for model in garden.models:
        role = model.details.get('review_role')
        if role not in ('bass', 'guitar', 'piano', 'xylophone'):
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
        def cue(part, source, color, strength=1, *, musical=True):
            if not model.submodels.get(part):
                return False
            a, b = int(source['start_ms']), min(duration, int(source['end_ms']))
            if not 0 <= a < b <= duration:
                raise ValueError('Invalid production musician clock')
            if part not in layers:
                el=ET.SubElement(elements,'Element',name=model.name+'/'+part,type='model')
                layers[part]=ET.SubElement(el,'EffectLayer')
            level=max(.05,min(1,float(strength)))
            bright=round((.22+.78*level if musical else level)*100)
            e=add_effect(layers[part],a,b,'On',EffectTemplate(
                settings=f'E_TEXTCTRL_Eff_On_Start={bright},E_TEXTCTRL_Eff_On_End={max(3,round(bright*.28))}',
                palette=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'))
            e.set('sourceMethod','retained_production_band_plan' if musical else 'nonmusical_instrument_visibility')
            if musical:
                e.set('sourceStartMs',str(a)); e.set('sourceEndMs',str(b))
            windows.setdefault(part,[]).append((a,b))
            return True
        counts=dict(source_events=0, mapped_events=0, unmapped_pitch_events=0, unmapped_events=[])
        def unmapped(source,reason):
            counts['unmapped_pitch_events']+=1
            counts['unmapped_events'].append(dict(start_ms=source['start_ms'],end_ms=source['end_ms'],
                pitch_midi=source.get('pitch_midi'),string_index=source.get('string_index'),reason=reason))
        key={'bass':'bassist','guitar':'guitarist','piano':'keyboardist','xylophone':'xylophonist'}[role]
        if role=='xylophone' and key not in plan.get('cues',{}):
            # Owner requests both pitched performers. Shared note evidence is
            # explicit choreography, never a claim of an isolated mallet stem.
            key='keyboardist'
        counts['source_lane']=key
        counts['arm_contact_omissions']=[]
        last_mallet_side='RIGHT'
        for source in plan.get('cues',{}).get(key,[]):
            counts['source_events']+=1
            level=source.get('velocity',source.get('expression',{}).get('brightness',.8))
            if role in ('piano','xylophone'):
                pitch=float(source['pitch_midi'])
                if pitch != round(pitch):
                    unmapped(source,'Non-integer source MIDI pitch; no rounding/transposition'); continue
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
                    unmapped(source,'Pitch outside physical guitar string/fret range'); continue
                parts=['STRING_'+str(possible[-1])]
            mapped=any([cue(p,source,'#FFF1AD' if role!='piano' else '#81EDFF',level) for p in parts])
            counts['mapped_events']+=int(mapped)
            if not mapped:
                unmapped(source,'Authored instrument has no matching native note/string submodel')
            if mapped:
                if role=='xylophone':
                    pitch=round(source['pitch_midi'])
                    preferred='LEFT' if last_mallet_side=='RIGHT' else 'RIGHT'
                    candidates=[s for s in (preferred,last_mallet_side) if model.submodels.get(f'ARM_{s}_NOTE_{pitch}')]
                    if candidates:
                        side=candidates[0];last_mallet_side=side
                        cue(f'ARM_{side}_NOTE_{pitch}',source,'#C5D6DD',.9)
                        # Idle complements use the same real source windows.
                        windows.setdefault('ARM_'+side+'_ACTIVE',[]).append((int(source['start_ms']),min(duration,int(source['end_ms']))))
                    else:
                        counts['arm_contact_omissions'].append(dict(start_ms=source['start_ms'],pitch_midi=pitch,
                            reason='No reachable authored mallet contact pose'))
                else:
                    side = ('LEFT' if source.get('pitch_midi',60)<66 else 'RIGHT') if role=='piano' else ('STRUM' if role=='guitar' else 'PLUCK')
                    cue('ARM_'+side+'_ACTIVE',source,'#C5D6DD',.9)
        # Rest complements keep source-timed contact and idle poses exclusive.
        for part in model.submodels:
            if not part.endswith('_IDLE') or not part.startswith('ARM_'):
                continue
            active=part.removesuffix('_IDLE')+'_ACTIVE'
            cursor=0
            for a,b in sorted(windows.get(active,[])):
                if a>cursor:cue(part,dict(start_ms=cursor,end_ms=a),'#BFA485',.65,musical=False)
                cursor=max(cursor,b)
            if cursor<duration:cue(part,dict(start_ms=cursor,end_ms=duration),'#BFA485',.65,musical=False)
        for part,nodes in list(model.submodels.items()):
            if not nodes or not part.startswith(('NOTE_MIDI_','STRING_')):continue
            alias='INSTRUMENT_IDLE_'+part
            model.submodels[alias]=list(nodes)
            cursor=0
            for a,b in sorted(windows.get(part,[])):
                if a>cursor:cue(alias,dict(start_ms=cursor,end_ms=a),'#A8C1CE',.22,musical=False)
                cursor=max(cursor,b)
            if cursor<duration:cue(alias,dict(start_ms=cursor,end_ms=duration),'#A8C1CE',.22,musical=False)
        report['models'][model.name]=counts
    report['limitations']=['Pitch outside each authored instrument range is reported and omitted, never octave-folded',
                          'Native two-pose arm banks use fixed shoulders; continuous contact motion unverified',
                          'Mixed-bus production instrument labels are estimates, not isolated-stem ground truth']
    return report
