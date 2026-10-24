"""Source-bound spatial motifs for native props, with explicit semantic roles.

Propagation is authored choreography of one measured event, never a new note.
No random source activity or whole-display beat/volume broadcast is introduced.
"""
from __future__ import annotations
import numpy as np


def role_for(model):
    explicit=model.details.get('musical_role')
    if explicit:return explicit
    name=model.name.upper();zone=model.zone.upper()
    if 'WINDOW' in name or zone=='SPIRALS':return 'harmony'
    if 'ROOF' in name or 'RIDGE' in name or zone in ('TREES','GROVE'):return 'guitarist'
    if 'MATRIX' in name or zone in ('MATRICES','HELIX','DNA','OPTICAL'):return 'keyboardist'
    if 'EAVE' in name or zone in ('DEPTH','CATHEDRAL'):return 'bassist'
    if 'CANE' in name:return 'keyboardist'
    if zone in ('ARCHES','SPINNER','SPINNERS','ACCENTS'):return 'drummer'
    return 'bassist'


def parts_for(model):
    if model.kind=='ac':return list(model.submodels)
    # Prefer physically coherent rows/strands over generic array sectors.
    for prefix in ('ROW_','STRAND_','RAY_','SECTOR_'):
        parts=[p for p in model.submodels if p.startswith(prefix)]
        if parts:return parts
    model.submodels.setdefault('ALL',list(range(1,len(model.points)+1)))
    return ['ALL']


def voice_events(cache,lane):
    # An unseparated sampler must not borrow the Phoneme recording's clock or
    # fabricate backing activity. Missing source evidence means abstention.
    if lane+'_energy' not in cache:return []
    energy=cache[lane+'_energy'];active=energy>0
    cuts=np.r_[0,np.flatnonzero(np.diff(active))+1,len(active)]
    return [dict(start_ms=int(a)*10,end_ms=int(b)*10,velocity=float(energy[a:b].max()),
                 kind='estimated_vocal_activity',source=lane)
            for a,b in zip(cuts[:-1],cuts[1:]) if active[a]]


def schedule(model,plan,cache,duration):
    role=role_for(model);parts=parts_for(model)
    source=(voice_events(cache,'estimated_backing') if role=='harmony' else
            voice_events(cache,'estimated_lead') if role=='lead' else plan['cues'].get(role,[]))
    center=np.mean(model.points,axis=0)
    depth_ms=int(model.details.get('propagation_delay_ms',0))
    phase=float(model.details.get('spatial_phase',0))
    direction=int(model.details.get('spatial_direction',1))
    result=[]
    for index,cue in enumerate(source):
        if cue.get('kind')=='chord_change':continue
        a,b=int(cue['start_ms']),int(cue['end_ms'])
        if b<=a:continue
        pitch=cue.get('pitch_midi')
        if pitch is not None:
            position=np.clip((float(pitch)-21)/87,0,1)
        elif role=='drummer':
            position={'kick':.1,'snare':.5,'hihat':.9,'cymbal':.75}.get(cue.get('kind'),.35)
        else:
            # Same phrase enters neighboring props at physical X positions;
            # no random event index is used to fake independence.
            position=np.clip((center[0]+100)/200,0,1)
        origin=int(round((position+phase)%1*(len(parts)-1)))
        level=float(np.clip(cue.get('velocity',cue.get('expression',{}).get('brightness',.7)),.05,1))
        steps=min(len(parts),3 if role in ('keyboardist','guitarist') else 2)
        for step in range(steps):
            part=parts[(origin+direction*step)%len(parts)]
            delay=depth_ms+step*50
            start=max(0,a+delay);end=min(duration,b+delay)
            if end<=start:continue
            result.append(dict(part=part,start_ms=start,end_ms=end,level=level*(.72**step),
                source_start_ms=a,source_end_ms=b,source_event=index,role=role,
                source_kind=cue.get('kind','pitched_note'),pitch_midi=pitch,
                propagation_delay_ms=delay))
    return result


def export_model(sequence,model,plan,cache,palette):
    events=schedule(model,plan,cache,sequence.duration)
    role=role_for(model)
    color=palette[{'guitarist':0,'bassist':1,'keyboardist':2,'drummer':2,'lead':0,'harmony':1}[role]]
    if model.kind=='ac':
        color={'Single Color Red':'#FF4040','Single Color Green':'#40FF60','Single Color White':'#FFFFFF'}[model.attrs['StringType']]
    native_effect='On'
    # Native Bars is applied only to a real 2-D sampled surface. The black
    # second palette creates traveling negative space rather than a full wash.
    matrix=any(p.startswith('ROW_') for p in model.submodels)
    for event in events:
        provenance={k:str(v) for k,v in dict(sourceRole=event['role'],sourceMethod='semantic_source_spatial_direction',
            sourceStartMs=event['source_start_ms'],sourceEndMs=event['source_end_ms'],
            sourceEventIndex=event['source_event'],sourcePitchMIDI=event['pitch_midi'],
            authoredPropagationMs=event['propagation_delay_ms']).items() if v is not None}
        sequence.effect(model,event['part'],event['start_ms'],event['end_ms'],color,
            round(event['level']*100),round(event['level']*12),provenance=provenance)
    # Group real note windows into sustained phrases for native matrix motion;
    # the effect ends at the final supported source event, with no release tail.
    if matrix and model.kind=='pixel' and events:
        windows=sorted({(e['source_start_ms'],e['source_end_ms']) for e in events})
        phrases=[]
        for a,b in windows:
            if phrases and a<=phrases[-1][1]+150:phrases[-1][1]=max(phrases[-1][1],b)
            else:phrases.append([a,b])
        model.submodels['SPATIAL_SURFACE']=sorted({n for p in parts_for(model) for n in model.submodels[p]})
        for a,b in phrases:
            if b-a<400:continue
            sequence.effect(model,'SPATIAL_SURFACE',a,b,color,provenance={
                'sourceRole':role,'sourceMethod':'source_phrase_native_Bars','sourceStartMs':str(a),'sourceEndMs':str(b)},
                settings='E_SLIDER_Bars_BarCount=2,E_TEXTCTRL_Bars_Cycles=1.0,E_CHOICE_Bars_Direction='+
                    ('Left' if model.details.get('spatial_direction',1)>0 else 'Right')+',E_CHECKBOX_Bars_Gradient=1',
                palette=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1,C_BUTTON_Palette2=#000000,C_CHECKBOX_Palette2=1',
                effect_name='Bars')
            native_effect='On + Bars'
    return dict(model=model.name,zone=model.zone,role=role,native_effects=native_effect,
        authored_propagation=True,source_events=len({e['source_event'] for e in events}),
        output_events=len(events),events=events,uncertainty='retained mixed-bus role estimates; not isolated instrument ground truth')
