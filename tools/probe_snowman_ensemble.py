"""Native wiring/visual probe, explicitly not a musical performance."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from models.snowman_ensemble import build_ensemble
from models.helixville4_vocal_phonemes import PHONEME_NAMES
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.build_snowman_ensemble import NativeSequence,add_performers,import_drummer,PerformanceView,check_native


def probe(root,xlights):
    row=next(r for r in json.loads((root/'sources.json').read_text()) if r['id']=='04')
    analysis=json.loads((root/'analysis/04/instruments.json').read_text())
    vocals={'mouths':[dict(start_ms=i*150,end_ms=(i+1)*150,phoneme=shape) for i,shape in enumerate(PHONEME_NAMES)],'words':[],'lines':[]}
    evidence=[]
    for variant in ('band','faces'):
        g=build_ensemble(variant);g.concept_id='1';folder=root/'geometry_probe'/variant;write_layout(g,folder)
        for name in ('drummer_idle.png','drummerbg.png'):shutil.copy2(Path('fixtures/band_geometry/source')/name,folder/'assets'/name)
        seq=NativeSequence(g,4,row['path'],'Native connectivity probe');seed=folder/'seed.xsq';seq.write(seed)
        import_drummer(seq,seed,Path(row['path']),root/'analysis/04/drums.json',folder/'injected.xsq')
        mouths=add_performers(seq,analysis,vocals);path=folder/'probe.xsq';seq.write(path)
        with (folder/'render.log').open('w') as log:
            subprocess.run([str(xlights),'--headless','-q','-s',str(folder),'-od',str(folder),str(path)],stdout=log,stderr=log,check=True,timeout=200)
        frames,step=read_fseq(path.with_suffix('.fseq'));coverage=check_native(g,frames,mouths,analysis)
        view=PerformanceView(g,{**row,'title':'Four-second wiring probe / no musical claims'},vocals)
        for i in (0,8,20,50):view.timed_frame(frames[i],i*50).save(folder/f'probe_{i}.png')
        result=dict(variant=variant,native_frames=len(frames),frame_ms=step,coverage=coverage,
                    all_seven_native_mouth_shapes_verified=True,musical_performance=False)
        (folder/'connectivity.json').write_text(json.dumps(result,indent=2)+'\n');evidence.append(result)
        print('PROBE_READY',variant,frames.shape,step,flush=True)
    return evidence


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--xlights',type=Path,required=True)
    a=p.parse_args();probe(a.root.resolve(),a.xlights.resolve())
