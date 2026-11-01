"""Checkpoint the twelve current native views in one owned X11 session."""
from pathlib import Path
import argparse
import json
import os
import time

from tools.native_preview import preview_run
from tools.phoneme_source import digest


def render(layouts,xlights,numbers):
    layouts=Path(layouts);items=json.loads((layouts/'Layout_Manifest.json').read_text())
    results=[]
    for number in numbers:
        item=next(row for row in items if row['number']==number)
        folder=layouts/f'{number:02}';manifest=folder/'run_manifest.json'
        current=json.loads(manifest.read_text());receipt=current.get('native_preview',{})
        movie=Path(receipt.get('mp4') or '/nonexistent')
        valid=(receipt.get('status')=='success' and movie.is_file()
               and receipt['mp4_sha256']==digest(movie)
               and receipt['xsq_sha256']==digest(folder/'Performance.xsq')
               and receipt['layout_sha256']==digest(folder/'xlights_rgbeffects.xml'))
        print('NATIVE_VIEW_START',number,item['name'],time.time(),flush=True)
        if not valid:
            receipt=preview_run(folder,xsq=folder/'Performance.xsq',
                audio=folder/'media'/item.get('audio_name','Helix_Starred_New_Review.wav'),xlights=xlights)
        row=dict(number=number,name=item['name'],status=receipt['status'],
                 movie=receipt.get('mp4'),warnings=receipt.get('warnings',[]))
        results.append(row)
        (layouts.parent/'native-view-progress.json').write_text(json.dumps(results,indent=2)+'\n')
        # The task container runs the renderer with its Ubuntu runtime. Return
        # only generated output ownership to the shared workspace user.
        if os.getuid()==0:
            for parent,dirs,files in os.walk(folder):
                os.chown(parent,1000,1000)
                for name in files:os.chown(Path(parent)/name,1000,1000)
        print('NATIVE_VIEW_DONE',json.dumps(row),flush=True)
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('layout_root',type=Path)
    p.add_argument('--xlights',required=True);p.add_argument('--layouts',dest='numbers',type=int,nargs='+',default=list(range(1,13)))
    a=p.parse_args();result=render(a.layout_root,a.xlights,a.numbers)
