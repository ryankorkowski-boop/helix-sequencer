"""Sequence new review excerpts through Helix and actual native xLights."""
from __future__ import annotations
from core.engine_runner import run_variant
import argparse,copy,json,os,shutil,subprocess,time
from contextlib import redirect_stdout
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from core import effect_engine as engine
from core.audio_run_cache import AudioRunCache
from models.showcase_flavors import FLAVORS,build_flavor
from models.final_band_native import add_final_native_band
from tools.run_showcase_audio_batch import model_routes,digest
from tools.showcase_audio_native import prepare_template,native_music_xsq
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.build_helpers.ultimate_showcase import write_layout

IDS=['E01','E03','E05','E07','E09','E13','E14','E17','E19','E21']


def garden(key,bands=False):
    g=build_flavor(key)
    # Six houses with varied authored palettes around clear foreground stages.
    for i,(x,z) in enumerate([(-150,60),(-90,92),(-35,115),(40,115),(95,92),(150,60)]):
        c=g.palette[i%3];h=13+i%3*3
        g.poly(f'REVIEW_HOUSE_{i}_WALL',[(x-12,0,z),(x-12,h,z),(x+12,h,z),(x+12,0,z)],90,'REVIEW_HOUSES','neighborhood house',c)
        g.poly(f'REVIEW_HOUSE_{i}_ROOF',[(x-15,h,z),(x,h+9,z),(x+15,h,z)],70,'REVIEW_HOUSES','roofline',g.palette[(i+1)%3])
        for side in (-1,1):
            a=x+side*6;g.poly(f'REVIEW_HOUSE_{i}_WINDOW_{side}',[(a-2,4,z),(a-2,8,z),(a+2,8,z),(a+2,4,z),(a-2,4,z)],24,'REVIEW_HOUSES','window',g.palette[2])
    if bands:
        add_final_native_band(g,'REVIEW_SNOW',(-65,0,155),stage='glacier_pier')
        add_final_native_band(g,'REVIEW_ROCK',(65,0,155),rock=True,stage='circuit_garage')
    start=1
    for m in g.models:m.start=start;start+=m.channels
    return g


def add_bands(g,root,row,folder,native):
    from models.snowman_ensemble import build_ensemble
    from models.final_band_scene import FinalBandScene
    from tools.build_snowman_ensemble import NativeSequence,import_drummer
    from tools.final_band_performance import FinalBandPerformance
    from core.final_band_export import add_final_band_events
    audio=root/'07_Layouts_and_Sequences'/row['excerpt_id']/'audio.wav'
    dg=build_ensemble('band');ds=NativeSequence(dg,36,'audio.wav',row['filename']);seed=folder/'drum_seed.xsq';ds.write(seed)
    import_drummer(ds,seed,audio,root/'analysis'/row['excerpt_id']/'drums.json',folder/'drum_injected.xsq')
    drummer=folder/'canonical_drums.xsq';ds.write(drummer)
    pr=dict(id=row['excerpt_id'],path=str(audio),sha256=digest(audio),duration=36,drummer_xsq=str(drummer))
    perf=FinalBandPerformance(pr,FinalBandScene(),root/'analysis')
    seq=NativeSequence(g,36,'audio.wav',row['filename'])
    proof=add_final_band_events(seq,perf,drummer)
    tree=ET.parse(native);r=tree.getroot();db=r.find('EffectDB');pal=r.find('ColorPalettes')
    doff,poff=len(db),len(pal)
    for e in seq.root.find('EffectDB'):db.append(copy.deepcopy(e))
    for e in seq.root.find('ColorPalettes'):pal.append(copy.deepcopy(e))
    elements=r.find('ElementEffects')
    for e in seq.root.find('ElementEffects'):
        if not e.get('name','').startswith(('REVIEW_SNOW','REVIEW_ROCK')):continue
        if not e.findall('.//Effect'):continue
        old=elements.find(f"Element[@name='{e.get('name')}']")
        if old is not None:elements.remove(old)
        e=copy.deepcopy(e)
        for v in e.findall('.//Effect'):
            if v.get('ref') is not None:v.set('ref',str(int(v.get('ref'))+doff))
            if v.get('palette') is not None:v.set('palette',str(int(v.get('palette'))+poff))
        elements.append(e)
    ET.indent(r);tree.write(native,encoding='utf-8',xml_declaration=True)
    return proof


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--xlights',type=Path,required=True)
    p.add_argument('--ids',nargs='*');p.add_argument('--flavors',nargs='*');a=p.parse_args();root=a.root.resolve()
    rows={r['excerpt_id']:r for r in json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text())}
    for eid in a.ids or IDS:
        row=rows[eid];audio=root/'07_Layouts_and_Sequences'/eid/'audio.wav';cache=AudioRunCache(digest(audio))
        for i,f in enumerate(FLAVORS):
            if a.flavors and f.key not in a.flavors:continue
            bands=i==IDS.index(eid)%6 and IDS.index(eid)<8;g=garden(f.key,bands)
            folder=root/'07_Layouts_and_Sequences'/eid/f.key;folder.mkdir(parents=True,exist_ok=True)
            native=folder/'performance.xsq';receipt=folder/'native.json'
            face_sha=digest(Path(__file__).resolve().parents[1]/'models/final_band_scene.py')
            reuse_engine=False
            if receipt.exists() and native.with_suffix('.fseq').exists():
                old=json.loads(receipt.read_text())
                fseq=folder/old.get('fseq_file','performance.fseq')
                if old['audio_sha256']==digest(audio) and old['bands']==bands and old['xsq_sha256']==digest(native) and fseq.exists() and old['fseq_sha256']==digest(fseq):
                    if not bands or old.get('face_geometry_sha256')==face_sha:
                        print('CACHED_NATIVE',eid,f.key,flush=True);continue
                    reuse_engine=(folder/'engine_raw.xsq').exists()
            template=prepare_template(g,folder);media=folder/'audio.wav';shutil.copyfile(audio,media)
            raw=folder/'engine_raw.xsq'
            tuning=engine.RuntimeTuning(layout_file=folder/'xlights_rgbeffects.xml',template_guidance=False,
                workspace_history_enabled=False,learning_memory_enabled=False,matrix_intelligence=False,
                polish_enabled=False,variant_count=1,birdsong_enabled=False,birdsong_auto=False,
                audio_reactive_profile='showcase',audio_reactive_intensity=1.6,spatial_awareness=.85,
                chase_style='radial_out',model_overrides=model_routes(g),max_layers_per_prop=3)
            if not reuse_engine:
                with (folder/'engine.log').open('w') as log,redirect_stdout(log):
                    run_variant(engine.VARIANTS['v27.3'],template,media,raw,engine.base.UserProfile(),tuning=tuning,analysis_cache=cache)
            export=native_music_xsq(raw,native,g,media,36)
            bandproof=add_bands(g,root,row,folder,native) if bands else None
            with (folder/'native.log').open('w') as log:
                subprocess.run([str(a.xlights.resolve()),'--headless','-q','-s',str(folder),'-od',str(folder),str(native)],
                    env={**os.environ,'XL_NO_GPU_COMPUTE':'1'},stdout=log,stderr=log,check=True,timeout=600)
            snapshot=folder/'verified.fseq';shutil.copyfile(native.with_suffix('.fseq'),snapshot)
            frames,step=read_fseq(snapshot)
            if len(frames)!=720 or step!=50 or not frames.any():raise ValueError('Incomplete/dark native sequence')
            coverage={m.name:int(np.count_nonzero(frames[:,m.start-1:m.start-1+m.channels].max(axis=1))) for m in g.models if m.kind=='pixel'}
            controls=[m.name for m in g.models if m.kind!='pixel' and frames[:,m.start-1:m.start-1+m.channels].any()]
            if controls:raise ValueError(f'Control fixtures activated: {controls}')
            proof=dict(excerpt_id=eid,flavor=f.key,layout=g.title,bands=bands,frames=720,frame_ms=50,
                xsq_sha256=digest(native),fseq_file='verified.fseq',fseq_sha256=digest(snapshot),layout_sha256=digest(folder/'xlights_rgbeffects.xml'),
                audio_sha256=digest(audio),export=export,band_export=bandproof,active_model_frames=coverage,
                control_channels_dark=True,channel_animation=bool(np.any(frames[1:]!=frames[:-1])),
                xlights_version='2026.18',source_timestamps=row,analysis_cache_hits=cache.hits,face_geometry_sha256=face_sha if bands else None)
            receipt.write_text(json.dumps(proof,indent=2)+'\n')
            print('NATIVE_COMPLETE',eid,f.key,export['native_effects'],sum(v>0 for v in coverage.values()),len(coverage),flush=True)


if __name__=='__main__':main()
