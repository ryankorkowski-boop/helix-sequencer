"""Grade actual source frames and compose the ordered owner-review MP4."""
from pathlib import Path
import argparse
import concurrent.futures
import json
import shutil
import subprocess

from tools.build_current_comparison import NAMES
from tools.phoneme_source import digest
from tools.render_approval_collection import comparison
from tools.verify_showcase_luma import verify_mp4


def finish(work,audio,*,source_commit):
    work,audio=Path(work),Path(audio);manifest=json.loads((work/'layouts/Layout_Manifest.json').read_text())
    panels=work/'graded-panels';panels.mkdir(exist_ok=True)
    source_hash=digest(audio)
    def grade(item):
        number=item['number'];folder=work/'layouts'/f'{number:02}'
        current=json.loads((folder/'run_manifest.json').read_text());native=current.get('native_preview',{})
        if number==2:
            source=work/'panels/02_Canonical_3D_Snowman_Band.mp4';gamma=1.
            band=json.loads(source.with_suffix('.json').read_text())
            if band['source_audio_sha256']!=source_hash:raise ValueError('Foreign solid band soundtrack')
        else:
            if native.get('status')!='success':raise ValueError(f'Native view{number} failed')
            source=Path(native['mp4']);gamma=2.2 if number in (1,7,8,11) else 1.6
            if (native['mp4_sha256']!=digest(source) or native['xsq_sha256']!=digest(folder/'Performance.xsq')
                    or native['layout_sha256']!=digest(folder/'xlights_rgbeffects.xml')
                    or native['audio_sha256']!=source_hash):raise ValueError(f'Stale source view{number}')
        target=panels/f'{number:02}.mp4'
        if gamma==1:shutil.copyfile(source,target)
        else:
            tone='lutrgb='+':'.join(f"{c}='255*pow(val/255,{1/gamma})'" for c in ('r','g','b'))
            subprocess.run(['ffmpeg','-v','error','-y','-threads','1','-filter_threads','1','-i',str(source),
                            '-vf',tone,'-c:v','libx264','-preset','fast','-crf','18','-threads','1',
                            '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(target)],check=True)
        readable=verify_mp4(target)
        row=dict(number=number,name=item['name'],source=str(source),source_sha256=digest(source),
                 target=str(target),target_sha256=digest(target),display_gamma=gamma,
                 source_events_or_geometry_changed=False,readability=readable)
        print('PANEL_QC',number,readable['passed'],readable['measurements'],flush=True)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(grade,manifest))
    rows.sort(key=lambda row:row['number'])
    (work/'panel-verification.json').write_text(json.dumps(rows,indent=2)+'\n')
    failed=[row['number'] for row in rows if not row['readability']['passed']]
    if failed:raise ValueError('Unchanged panel visibility gates failed: '+str(failed))
    import soundfile as sf
    duration=sf.info(audio).duration
    target=work/'HELIX_REAL_AUDIO_12_LAYOUT_COMPARISON_REVIEW_CANDIDATE.mp4'
    comparison([Path(r['target']) for r in rows],
        [f'{i:02}  '+name for i,name in enumerate(NAMES,1)],target,audio,4,3,duration=duration)
    receipt=dict(source_commit=source_commit,source_audio_sha256=source_hash,audio=str(audio),
                 source_seconds=duration,file=str(target),sha256=digest(target),panels=rows,
                 layout_order=list(NAMES),owner_approved=False,full_comparison_verification='pending',
                 limitations=['Lead/backing are source-bound separated estimates; acoustic identity/lexical phones unverified',
                              'Canonical band uses continuous Helix solid3D; other11views use native xLights pixels',
                              'V3depth follows originalfront artwork; owner artistic approval pending'])
    (work/'comparison-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('COMPOSED',target,flush=True)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('work',type=Path);p.add_argument('audio',type=Path)
    p.add_argument('--source-commit',required=True);a=p.parse_args();finish(a.work,a.audio,source_commit=a.source_commit)
