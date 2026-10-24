"""Export final band cues onto actual native model/submodel identities."""
from __future__ import annotations

import numpy as np
from models.band_sampler_logic import SHAPE_NAMES
from music.unified_mallet import bar_pitch


def _runs(values):
    values = np.asarray(values)
    boundaries = np.r_[0, np.flatnonzero(np.diff(values))+1, len(values)]
    return [(int(a),int(b),int(values[a])) for a,b in zip(boundaries[:-1],boundaries[1:])]


def add_final_band_events(sequence, performance, drummer_source):
    """Use retained string, voice and note lanes; no beat/pulse substitutes.

    Native props use stationary addressable poses. Continuous GL animation can
    additionally be exported on a Video pixel matrix by the existing exporter.
    """
    import xml.etree.ElementTree as ET
    source=ET.parse(drummer_source).getroot()
    db=[e.text or '' for e in source.findall('EffectDB/Effect')]
    palettes=[e.text or '' for e in source.findall('ColorPalettes/ColorPalette')]
    report={'stages':{},'source_events_preserved':True,'controller_addresses_inferred':False,
            'output':'native stationary pixel poses','continuous_mesh_motion':False}
    n=performance.n
    for model in sequence.g.models:
        role=model.details.get('final_band_role')
        if not role: continue
        stage=model.details['stage']; stats=report['stages'].setdefault(stage,{})
        before=sequence.identifier
        if role=='drummer':
            for shade,color in [('BLUE','#308CC1'),('RED','#C83D31'),('GREEN','#52B766'),('GOLD','#DDB52E'),('NEUTRAL','#A8BAC6')]:
                if 'IDLE_'+shade in model.submodels:
                    sequence.effect(model,'IDLE_'+shade,0,sequence.duration,color,40)
            for parent in source.findall('ElementEffects/Element'):
                if not parent.get('name','').endswith('DRUMMER_V3'): continue
                for layer in parent.findall('SubModelEffectLayer'):
                    part=layer.get('name')
                    if part not in model.submodels: raise ValueError(f'Missing canonical drummer target: {part}')
                    for effect in layer.findall('Effect'):
                        ref=effect.get('ref'); palette=effect.get('palette')
                        sequence.effect(model,part,int(effect.get('startTime')),int(effect.get('endTime')),'#FFFFFF',
                            settings=db[int(ref)],palette=palettes[int(palette)],layer=1,
                            provenance={k:v for k,v in effect.attrib.items() if k.startswith('source')})
        else:
            sequence.effect(model,'BODY',0,sequence.duration,'#C5B69D',32)
            if role in ('bass','guitar'):
                for j in range(4 if role=='bass' else 6):
                    if 'STRING_'+str(j) not in model.submodels: continue
                    values=np.zeros(n,np.int16)
                    for i,routes in enumerate(performance.curves[role+'_routes']):
                        for route in routes:
                            if route[0]==j:
                                velocity=max((v for note,v in zip(performance.curves[role+'_notes'][i],performance.curves[role+'_note_levels'][i]) if note>=0),default=0)
                                values[i]=round(float(velocity)*100)
                    for a,b,value in _runs(values):
                        if value: sequence.effect(model,'STRING_'+str(j),a*50,b*50,'#CFC4A1',value)
                for rig in [r for r in performance.scene.rigs if r['role']==role]:
                    sequence.effect(model,'ARM_'+rig['side'].upper()+'_IDLE',0,sequence.duration,'#BEA182',35)
            elif role in ('lead','harmony'):
                k=int(role=='harmony')
                for a,b,value in _runs(performance.voice_lanes[:,k]):
                    sequence.effect(model,'MOUTH_'+SHAPE_NAMES[value],a*50,b*50,
                                    '#F67A73' if k==0 else '#A882D3',65 if value else 22)
                for side in ('LEFT','RIGHT'):
                    sequence.effect(model,'ARM_'+side+'_IDLE',0,sequence.duration,'#BEA182',35)
            elif role == 'piano':
                # Route only pitches with actual physical key submodels.
                # The visible keyboard has its own note geometry; do not
                # fabricate mallet poses or silently address hidden props.
                bars = performance.scene.bars
                first = min(bars)
                for pitch in bars:
                    part = f'NOTE_MIDI_{pitch}'
                    if part not in model.submodels or not model.submodels[part]:
                        continue
                    values = np.rint(performance._bar_levels[:, pitch-first]*100).astype(np.int16)
                    for a,b,value in _runs(values):
                        if value:
                            sequence.effect(model,part,a*50,b*50,'#D4B98A',value)
                for side in ('LEFT','RIGHT'):
                    part = f'ARM_{side}_IDLE'
                    if model.submodels.get(part):
                        sequence.effect(model,part,0,sequence.duration,'#BEA182',35)
            else:
                raise ValueError(f'Unsupported final-band role: {role}')
        stats[role]=sequence.identifier-before
    if len(report['stages'])!=2 or any(len(s)!=6 for s in report['stages'].values()):
        raise ValueError('Expected two complete six-performer native bands')
    return report
