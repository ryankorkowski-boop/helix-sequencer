import json,sys,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from tools.verify_recovery_media import verify
from tools.verify_showcase_luma import verify_mp4

root=Path(__file__).resolve().parent
config=json.loads((root/'optimized-review-config.json').read_text())
out=root/'helix/evidence/optimized_beta_20261029/media';out.mkdir(parents=True,exist_ok=True)
def intervals(mask,fps=10):
    cuts=np.r_[0,np.flatnonzero(np.diff(np.asarray(mask,dtype=np.int8)))+1,len(mask)]
    return [[round(a/fps,3),round(b/fps,3)] for a,b in zip(cuts[:-1],cuts[1:]) if mask[a]]
for item in config['movies']:
    p=root/'optimized-review-movies'/item['filename']
    if not p.is_file():continue
    receipt=out/(p.stem+'.json')
    from tools.phoneme_source import digest
    if receipt.exists() and json.loads(receipt.read_text()).get('sha256')==digest(p):continue
    print('VERIFYING',p.name,flush=True)
    r=verify(p,item['audio'],item['audio_sha256']);r['readability']=verify_mp4(p)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vf','fps=10,scale=320:180',
                                '-pix_fmt','gray','-f','rawvideo','-'])
    a=np.frombuffer(raw,np.uint8).reshape(-1,180,320)[:,24:164,8:312]
    blank=(a>20).mean((1,2))<.001
    static=np.abs(np.diff(a.astype(np.int16),axis=0)).mean((1,2))<.005
    r['blank_intervals_seconds']=intervals(blank)
    r['prolonged_blank_intervals']=[x for x in intervals(blank) if x[1]-x[0]>=1]
    r['prolonged_frozen_intervals']=[x for x in intervals(static) if x[1]-x[0]>=2]
    r['technical_media_checks_passed']=r['readability']['passed'] and not r['prolonged_blank_intervals'] and not r['prolonged_frozen_intervals']
    r.update(beta_acceptance=False,owner_approval=False,actual_playback_watched=False)
    receipt.write_text(json.dumps(r,indent=2)+'\n')
    print(p.name,r['technical_media_checks_passed'],r['readability']['measurements'],r['prolonged_blank_intervals'],r['prolonged_frozen_intervals'],flush=True)
    times=[0,.5,item['duration']*.25,item['duration']*.5,item['duration']*.75,item['duration']-.25]
    sheet=Image.new('RGB',(1440,570),(10,14,20));draw=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-vf','scale=480:270','-pix_fmt','rgb24','-f','rawvideo','-'])
        x=i%3*480;y=i//3*285;sheet.paste(Image.frombytes('RGB',(480,270),raw),(x,y));draw.text((x+8,y+271),f'{t:.2f} seconds',fill='white')
    sheet.save(out/(p.stem+'.jpg'),quality=93)
