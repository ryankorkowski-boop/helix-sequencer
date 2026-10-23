"""Build all review layouts from one retained full-song production analysis."""
import argparse
import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from models.approval_layouts import build_layout, NAMES
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from tools.phoneme_source import EXPECTED_SHA256, digest
from tools.phoneme_vocal_export import static_materials, export, FIXTURE
from tools.canonical_band_cues import export_instruments, refresh_models
from models.band_sampler_logic import SHAPE_NAMES
from xlights.xml_io import materialize_native_effect_tables


def build(source, output):
    source,output=Path(source),Path(output)
    audio=source/'media/Phoneme_Test_Hook.mp3'
    if digest(audio)!=EXPECTED_SHA256:raise ValueError('Original soundtrack mismatch')
    plans=list((source/'sequence').glob('*.snowman_band.json'))
    if len(plans)!=1:raise ValueError('Expected one cached production analysis')
    plan=json.loads(plans[0].read_text())
    manifest=[]
    for number,name in enumerate(NAMES,1):
        folder=output/f'{number:02}_{name}'
        if folder.exists():raise FileExistsError(folder)
        g=build_layout(number)
        band=[m for m in g.models if m.details.get('review_role')]
        if band:
            # Static material export operates only on canonical performers.
            from types import SimpleNamespace
            static_materials(SimpleNamespace(models=band))
        write_layout(g,folder,include_demo=False,export_all_custom=True)
        (folder/'media').mkdir();shutil.copyfile(audio,folder/'media/Phoneme_Test_Hook.mp3')
        sequence=NativeSequence(g,34.88,'media/Phoneme_Test_Hook.mp3',g.title)
        sequence.duration=34880
        sequence.root.find('head/sequenceDuration').text='34.880'
        for j,m in enumerate(g.models):
            if m.details.get('review_role'):continue
            if m.details.get('generic_singer'):
                with np.load(FIXTURE/'acoustic_vocal_clocks.npz',allow_pickle=False) as clocks:
                    source_lane=m.details['generic_singer']
                    shapes=clocks[source_lane+'_shapes'];energy=clocks[source_lane+'_energy']
                    values=np.where(energy>0,shapes,0)
                    cuts=np.r_[0,np.flatnonzero(np.diff(values))+1,len(values)]
                    for a,b in zip(cuts[:-1],cuts[1:]):
                        part='MOUTH_'+SHAPE_NAMES[int(values[a])]
                        if m.submodels.get(part):sequence.effect(m,part,int(a)*10,min(34880,int(b)*10),g.palette[2],85)
                for part in ('OUTLINE','BASE','BODY'):
                    if m.submodels.get(part):sequence.effect(m,part,0,34880,g.palette[0],45)
                continue
            is_helix=m.name=='HX_CENTER_KEYBOARD_HELIX'
            if is_helix:
                for role,part,color in [('guitarist','STRAND_A',g.palette[0]),('bassist','STRAND_B',g.palette[1])]:
                    sequence.effect(m,part,0,34880,color,18)
                    for cue in plan['cues'][role]:
                        sequence.effect(m,part,cue['start_ms'],cue['end_ms'],color,95,25,
                                        provenance={'sourceRole':role,'sourceMethod':'retained_production_plan'})
                for cue in plan['cues']['keyboardist']:
                    pitch=round(cue['pitch_midi']);part=f'KEY_MIDI_{pitch:03d}'
                    if part in m.submodels:sequence.effect(m,part,cue['start_ms'],cue['end_ms'],g.palette[2],100,25,
                        provenance={'sourceRole':'keyboardist','sourcePitchMIDI':str(pitch)})
                continue
            if m.kind=='ac':parts=list(m.submodels)
            else:
                parts=[p for p in m.submodels if p.startswith(('SECTOR_','RAY_','STRAND_','ROW_'))]
                if not parts:
                    parts=['ALL'];m.submodels['ALL']=list(range(1,len(m.points)+1))
            role=('guitarist','bassist','keyboardist')[j%3]
            cues=plan['cues'][role]
            active_windows={part:[] for part in parts}
            for k,cue in enumerate(cues):
                if role=='guitarist' and cue['kind']=='chord_change':continue
                part=parts[(round(cue.get('pitch_midi',k))+j)%len(parts)]
                color=g.palette[(j+k//8)%3]
                if m.kind=='ac':
                    color={'Single Color Red':'#FF4040','Single Color Green':'#40FF60','Single Color White':'#FFFFFF'}[m.attrs['StringType']]
                sequence.effect(m,part,cue['start_ms'],cue['end_ms'],color,100,45,
                    provenance={'sourceRole':role,'sourceMethod':'retained_production_plan'})
                active_windows[part].append((int(cue['start_ms']),int(cue['end_ms'])))
            # Static visibility is restricted to real source-event complements;
            # it is never counted as a note, onset, or instrumental activity.
            for part,windows in active_windows.items():
                color=m.colors[0] if m.kind!='ac' else {'Single Color Red':'#FF4040','Single Color Green':'#40FF60','Single Color White':'#FFFFFF'}[m.attrs['StringType']]
                cursor=0
                for a,b in sorted(windows):
                    if a>cursor:sequence.effect(m,part,cursor,a,color,30,30,provenance={'sourceRole':'nonmusical_idle_visibility'})
                    cursor=max(cursor,b)
                if cursor<34880:sequence.effect(m,part,cursor,34880,color,30,30,provenance={'sourceRole':'nonmusical_idle_visibility'})
        # The general prop loop may have created ALL lanes after the layout was
        # serialized; write actual final submodel definitions before compiling.
        write_layout(g,folder,include_demo=False,export_all_custom=True)
        if band:
            from types import SimpleNamespace
            export_instruments(sequence.root,SimpleNamespace(models=band),plan)
            vocals=export(sequence.root,folder/'xlights_rgbeffects.xml',SimpleNamespace(models=band))
            (folder/'vocal_lane_diagnostic.json').write_text(json.dumps(vocals,indent=2)+'\n')
            # Retain the original source drummer effects and their exact clocks.
            original=ET.parse(source/'Phoneme_Test_Hook_Helix.xsq').getroot()
            # Reuse source tables after normalizing the source to inline values.
            db=[e.text or '' for e in original.findall('EffectDB/Effect')]
            palettes=[e.text or '' for e in original.findall('ColorPalettes/ColorPalette')]
            for el in original.findall('ElementEffects/Element'):
                if not el.get('name','').startswith('HX_SNOW_DRUMMER'):continue
                copied=ET.fromstring(ET.tostring(el))
                for effect in copied.iter('Effect'):
                    if effect.get('ref','').isdigit():effect.set('settings',db[int(effect.attrib.pop('ref'))])
                    if effect.get('palette','').isdigit():effect.set('palette',palettes[int(effect.get('palette'))])
                target=sequence.root.find('ElementEffects')
                existing=target.find("Element[@name='%s']"%el.get('name'))
                if existing is not None:target.remove(existing)
                target.append(copied)
        materialize_native_effect_tables(sequence.root)
        refresh_models(g,folder/'xlights_rgbeffects.xml')
        path=folder/(name+'.xsq');sequence.write(path)
        # Camera framing is derived from real final model bounds.
        camera_models=band if number==7 else g.models
        points=np.concatenate([m.points for m in camera_models]);low,high=points.min(0),points.max(0);center=(low+high)/2
        span=high-low;distance=max(span[0]*(.80 if number==7 else .95),span[1]*(1.70 if number==7 else 2.0),55)
        tree_xml=ET.parse(folder/'xlights_rgbeffects.xml')
        for camera in tree_xml.findall('Viewpoints/*'):
            for key,value in dict(angleX=8 if number not in (10,11,12) else 18,angleY=0 if number not in (10,11) else 12,
                    distance=-distance,panx=-center[0],pany=-center[1],panz=-center[2]).items():camera.set(key,str(value))
        tree_xml.write(folder/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
        item=dict(number=number,name=name,folder=str(folder.resolve()),xsq=path.name,
                  source_audio_sha256=EXPECTED_SHA256,source_analysis_sha256=digest(plans[0]),
                  model_count=len(g.models),channels=sum(m.channels for m in g.models),
                  canonical_members=len(band),native_render_status='not_started',
                  native_limits=['Stationary native geometry; no geometric helix rotation claimed',
                                 'AC16/64/256 use exact circuit budgets; physical wiring not tested'])
        (folder/'run_manifest.json').write_text(json.dumps(dict(schema='helix.run_manifest.v1',warnings=[],**item),indent=2)+'\n')
        manifest.append(item)
        print('BUILT',number,name,item['channels'],flush=True)
    (output/'Layout_Manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();build(a.source,a.output)
