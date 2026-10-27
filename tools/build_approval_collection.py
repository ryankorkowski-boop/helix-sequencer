"""Build all review layouts from one retained full-song production analysis."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from models.approval_layouts import build_layout, NAMES
from tools.build_snowman_ensemble import NativeSequence
from tools.build_helpers.ultimate_showcase import write_layout
from tools.phoneme_source import EXPECTED_SHA256, digest
from tools.phoneme_vocal_export import static_materials, export, FIXTURE
from tools.canonical_band_cues import export_instruments, export_drums, refresh_models
from models.band_sampler_logic import SHAPE_NAMES
from xlights.xml_io import materialize_native_effect_tables


def build(source, output, *, audio_name='Phoneme_Test_Hook.mp3', expected_sha256=EXPECTED_SHA256, vocal_fixture=FIXTURE, numbers=None,
          include_xylophonist=False, full_keyboard=False):
    numbers=tuple(range(1,len(NAMES)+1)) if numbers is None else tuple(numbers)
    if not numbers or len(set(numbers))!=len(numbers) or any(type(n) is not int or not 1<=n<=len(NAMES) for n in numbers):
        raise ValueError('Choose unique layout numbers in1..12')
    source,output=Path(source),Path(output)
    audio=source/'media'/audio_name
    if digest(audio)!=expected_sha256:raise ValueError('Original soundtrack mismatch')
    import soundfile as sf
    duration_ms=round(sf.info(audio).duration*1000)
    duration=duration_ms/1000
    vocal_receipt=json.loads((vocal_fixture/'diagnostic.json').read_text())
    if vocal_receipt.get('audio_sha256')!=expected_sha256 or digest(vocal_fixture/'acoustic_vocal_clocks.npz')!=vocal_receipt.get('clock_sha256'):
        raise ValueError('Vocal cache does not belong to the collection source')
    source_manifest=json.loads((source/'run_manifest.json').read_text())
    if source_manifest.get('audio_sha256')!=expected_sha256:
        raise ValueError('Production analysis source identity mismatch')
    plans=list((source/'sequence').glob('*.snowman_band.json'))
    if len(plans)!=1:raise ValueError('Expected one cached production analysis')
    plan=json.loads(plans[0].read_text())
    repo=Path(__file__).resolve().parents[1]
    export_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    export_hashes={name:digest(repo/name) for name in ('models/final_band_scene.py',
        'models/final_band_native.py','models/canonical_native_band.py','models/approval_layouts.py',
        'tools/build_approval_collection.py','tools/canonical_band_cues.py',
        'tools/source_spatial_direction.py','tools/phoneme_vocal_export.py')}
    manifest=[]
    for number in numbers:
        name=NAMES[number-1]
        folder=output/f'{number:02}_{name}'
        if folder.exists():raise FileExistsError(folder)
        g=build_layout(number,include_xylophonist=include_xylophonist,full_keyboard=full_keyboard)
        band=[m for m in g.models if m.details.get('review_role')]
        if band:
            # Static material export operates only on canonical performers.
            from types import SimpleNamespace
            static_materials(SimpleNamespace(models=band))
        write_layout(g,folder,include_demo=False,export_all_custom=True)
        (folder/'media').mkdir();shutil.copyfile(audio,folder/'media'/audio_name)
        sequence=NativeSequence(g,duration,'media/'+audio_name,g.title)
        sequence.duration=duration_ms
        sequence.root.find('head/sequenceDuration').text=f'{duration:.3f}'
        spatial_reports=[]
        for m in g.models:
            if m.details.get('review_role'):continue
            if m.details.get('generic_singer'):
                with np.load(vocal_fixture/'acoustic_vocal_clocks.npz',allow_pickle=False) as clocks:
                    source_lane=m.details['generic_singer']
                    shapes=clocks[source_lane+'_shapes'];energy=clocks[source_lane+'_energy']
                    values=np.where(energy>0,shapes,0)
                    cuts=np.r_[0,np.flatnonzero(np.diff(values))+1,len(values)]
                    for a,b in zip(cuts[:-1],cuts[1:]):
                        part='MOUTH_'+SHAPE_NAMES[int(values[a])]
                        if m.submodels.get(part):sequence.effect(m,part,int(a)*10,min(duration_ms,int(b)*10),g.palette[2],85)
                for part in ('OUTLINE','BASE','BODY','EYES'):
                    if m.submodels.get(part):sequence.effect(m,part,0,duration_ms,g.palette[0],45)
                continue
            is_helix=bool(m.details.get('keyboard_pitch_rungs'))
            if is_helix:
                for role,part,color in [('guitarist','STRAND_A',g.palette[0]),('bassist','STRAND_B',g.palette[1])]:
                    sequence.effect(m,part,0,duration_ms,color,18)
                    for cue in plan['cues'][role]:
                        sequence.effect(m,part,cue['start_ms'],cue['end_ms'],color,95,25,
                                        provenance={'sourceRole':role,'sourceMethod':'retained_production_plan'})
                for cue in plan['cues']['keyboardist']:
                    pitch=round(cue['pitch_midi']);part=f'KEY_MIDI_{pitch:03d}'
                    if part in m.submodels:sequence.effect(m,part,cue['start_ms'],cue['end_ms'],g.palette[2],100,25,
                        provenance={'sourceRole':'keyboardist','sourcePitchMIDI':str(pitch)})
                continue
            from tools.source_spatial_direction import export_model
            with np.load(vocal_fixture/'acoustic_vocal_clocks.npz',allow_pickle=False) as clocks:
                spatial_reports.append(export_model(sequence,m,plan,clocks,g.palette))
        # The general prop loop may have created ALL lanes after the layout was
        # serialized; write actual final submodel definitions before compiling.
        write_layout(g,folder,include_demo=False,export_all_custom=True)
        if band:
            from types import SimpleNamespace
            instrument_report=export_instruments(sequence.root,SimpleNamespace(models=band),plan)
            instrument_report['drummer']=export_drums(sequence.root,SimpleNamespace(models=band),plan)
            (folder/'instrument_export.json').write_text(json.dumps(instrument_report,indent=2)+'\n')
            vocals=export(sequence.root,folder/'xlights_rgbeffects.xml',SimpleNamespace(models=band), fixture=vocal_fixture, expected_sha256=expected_sha256)
            (folder/'vocal_lane_diagnostic.json').write_text(json.dumps(vocals,indent=2)+'\n')
        materialize_native_effect_tables(sequence.root)
        refresh_models(g,folder/'xlights_rgbeffects.xml')
        path=folder/(name+'.xsq');sequence.write(path)
        # Camera framing is derived from real final model bounds.
        camera_models=band if number==7 else g.models
        points=np.concatenate([m.points for m in camera_models]);low,high=points.min(0),points.max(0);center=(low+high)/2
        span=high-low;distance=max(span[0]*(.80 if number==7 else .95),span[1]*(1.70 if number==7 else 2.0),55)
        if number==8:
            # Foreground band depth must be included: a house-sized camera
            # crops the lower four performers through perspective magnification.
            distance=span[2]/2+max(span[0]*.78,span[1]*1.6,55)
        if number==11:
            # Stand outside the near depth plane; a width/height-only camera
            # can crop the corridor entrance while its far structures fit.
            distance=span[2]/2+max(span[0]*.95,span[1]*1.85,55)
        # Native small-layout proof needs readable bulbs and stage occupancy;
        # source nodes, channel values and event clocks remain unchanged.
        if number in (1,5,6):distance*=.92 if number==1 else .82
        if number in (9,10):distance*=.82
        if number==11:distance*=.86
        tree_xml=ET.parse(folder/'xlights_rgbeffects.xml')
        for camera in tree_xml.findall('Viewpoints/*'):
            for key,value in dict(angleX=0 if number in (8,11) else 8 if number not in (10,12) else 18,angleY=12 if number==10 else 0,
                    distance=-distance,panx=-center[0],pany=-center[1],panz=-center[2]).items():camera.set(key,str(value))
        tree_xml.write(folder/'xlights_rgbeffects.xml',encoding='utf-8',xml_declaration=True)
        if number in (1,5,8):
            from tools.native_residential_context import add_context
            add_context(folder)
        item=dict(number=number,name=name,folder=str(folder.resolve()),xsq=path.name,
                  source_audio_sha256=expected_sha256,source_analysis_sha256=digest(plans[0]),
                  source_commit=source_manifest['source_commit'],source_duration_seconds=duration,audio_name=audio_name,
                  export_source_commit=export_commit,export_source_module_sha256=export_hashes,
                  model_count=len(g.models),channels=sum(m.channels for m in g.models),
                  canonical_members=len(band),native_render_status='not_started',
                  native_limits=['Stationary native geometry; no geometric helix rotation claimed',
                                 'AC16/64/256 use exact circuit budgets; physical wiring not tested'])
        (folder/'Spatial_Event_Provenance.json').write_text(json.dumps(spatial_reports,indent=2)+'\n')
        (folder/'run_manifest.json').write_text(json.dumps(dict(schema='helix.run_manifest.v1',warnings=[],**item),indent=2)+'\n')
        manifest.append(item)
        print('BUILT',number,name,item['channels'],flush=True)
    (output/'Layout_Manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--audio-name',default='Phoneme_Test_Hook.mp3')
    p.add_argument('--expected-sha256',default=EXPECTED_SHA256)
    p.add_argument('--vocal-fixture',type=Path,default=FIXTURE)
    p.add_argument('--layouts',type=int,nargs='+',help='Build only these layouts; default all12. Use7 12 for the two pilot shows.')
    p.add_argument('--include-xylophonist',action='store_true')
    p.add_argument('--full-keyboard',action='store_true')
    a=p.parse_args();build(a.source,a.output,audio_name=a.audio_name,
        expected_sha256=a.expected_sha256,vocal_fixture=a.vocal_fixture,numbers=a.layouts,
        include_xylophonist=a.include_xylophonist,full_keyboard=a.full_keyboard)
