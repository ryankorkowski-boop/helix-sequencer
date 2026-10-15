"""Stream real native FSEQ into six-panel and embedded-stage review movies."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from tools.showcase_review_native import IDS,garden
from models.showcase_flavors import FLAVORS
from tools.fseq_pixel_preview import FseqReader
from tools.showcase_audio_preview import NativeSongView
from tools.render_refined_helix_band import encoder
from core.output_provenance import brand_frame,stamp_mp4


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class StreamView:
    def __init__(self,folder,g,width,height,title,fseq_file='performance.fseq'):
        self.reader=FseqReader(folder/fseq_file)
        if self.reader.info.frames!=720 or self.reader.info.step_ms!=50:raise ValueError('Native timing mismatch')
        self.view=NativeSongView(g,title,width,height,halo_scale=2,pitch=-18)
        # The outer review compositor owns readable labels. Remove only static
        # text from this base, before native light pixels are composited.
        background=np.asarray(self.view.base).copy()
        for lo,hi in [(0,round(height*.16)),(round(height*.90),height)]:
            background[lo:hi]=background[lo:hi,:1]
        self.view.base=Image.fromarray(background)
        self.view.scene_base=self.view.base.crop(self.view.box)
        indexes=self.view.sorted_rgb_indices
        # Sparse FSEQ offsets are packed; absent ranges remain exactly dark.
        flat=[self.reader.offset_for_channel(int(i)+1) for i in indexes.ravel()]
        self.view.sorted_rgb_indices=np.array([self.reader.info.channels if x is None else x for x in flat]).reshape(indexes.shape)
        self.frames=iter(self.reader.iter_frames())
    def frame(self):
        values=np.frombuffer(next(self.frames),np.uint8)
        return self.view.frame(np.r_[values,np.uint8(0)])


def render(root,eid,mode):
    row=next(r for r in json.loads((root/'05_Source_Excerpt_Manifests/selected_excerpts.json').read_text()) if r['excerpt_id']==eid)
    category='03_Six_Layout_Comparisons' if mode=='comparison' else '02_Bands_Inside_Layouts'
    out=root/category;out.mkdir(parents=True,exist_ok=True);j=IDS.index(eid)
    name=f'{j+1:02d}_{eid}_'+('Six_Layouts' if mode=='comparison' else FLAVORS[j%6].title.replace(' & ','_and_').replace(' ','_')+'_Bands')
    movie=out/(name+'.mp4');receipt=movie.with_suffix('.render.json')
    if movie.exists() and receipt.exists():
        old=json.loads(receipt.read_text())
        if old['sha256']==sha(movie) and old.get('renderer_sha256')==sha(Path(__file__)):return
    choices=list(enumerate(FLAVORS)) if mode=='comparison' else [(j%6,FLAVORS[j%6])]
    views=[];proofs=[]
    for i,f in choices:
        folder=root/'07_Layouts_and_Sequences'/eid/f.key
        proof=json.loads((folder/'native.json').read_text());g=garden(f.key,proof['bands'])
        if proof['audio_sha256']!=sha(root/'07_Layouts_and_Sequences'/eid/'audio.wav'):raise ValueError('Native soundtrack hash mismatch')
        for key,path in [('xsq_sha256','performance.xsq'),('fseq_sha256',proof.get('fseq_file','performance.fseq')),('layout_sha256','xlights_rgbeffects.xml')]:
            if proof[key]!=sha(folder/path):raise ValueError('Changed native input: '+key)
        width,height=(640,450) if mode=='comparison' else (1920,1080)
        views.append(StreamView(folder,g,width,height,Path(row['filename']).stem,proof.get('fseq_file','performance.fseq')));proofs.append(proof)
    tmp=movie.with_suffix('.rendering.mp4');audio=root/'07_Layouts_and_Sequences'/eid/'audio.wav'
    writer=encoder(tmp,1920,1080,20,audio,0,36)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28)
    label=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    began=time.monotonic()
    try:
        for k in range(720):
            if mode=='comparison':
                image=Image.new('RGB',(1920,1080),'#07101b')
                for i,view in enumerate(views):
                    panel=view.frame();d=ImageDraw.Draw(panel)
                    d.rectangle((0,0,640,34),fill='#0b1928');d.text((12,6),FLAVORS[i].title+(' + Bands' if proofs[i]['bands'] else ''),font=label,fill='#e1f3ff')
                    image.paste(panel,((i%3)*640,90+(i//3)*450))
                d=ImageDraw.Draw(image);d.text((30,26),'HELIX  /  SIX WORLDS  /  '+Path(row['filename']).stem,font=font,fill='#e2f1ff')
                d.text((30,1020),f'{eid}   •   One source excerpt, six simultaneous native xLights sequences   •   {row["start_seconds"]+k/20:06.2f}s source',font=label,fill='#b0cbde')
            else:
                image=views[0].frame();d=ImageDraw.Draw(image)
                d.rectangle((0,0,1920,62),fill='#07101b');d.text((30,18),'HELIX  /  '+FLAVORS[j%6].title+'  /  TWO BAND STAGES',font=font,fill='#e2f1ff')
                d.rectangle((0,1022,1920,1080),fill='#07101b');d.text((30,1035),Path(row['filename']).stem+f'   •   {row["start_seconds"]+k/20:06.2f}s source',font=label,fill='#b0cbde')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            if k in (40,240,480,700):image.save(out/(name+f'_{k:04d}.jpg'),quality=92)
            if k%240==0:print('LAYOUT_FRAMES',mode,eid,k,round(k/max(time.monotonic()-began,.01),2),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();tmp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
    if writer.wait():raise RuntimeError('Native layout encoder failed')
    tmp.replace(movie)
    detail_proof=None
    if mode=='embedded':
        matches=[p for cat in ('01_Standalone_Bands','04_Lyric_Band_Videos') for p in (root/cat).glob(f'*_{eid}_*.mp4') if '.rendering.' not in p.name]
        if len(matches)!=1:raise ValueError('Exactly one completed stage-detail movie is required: '+eid)
        detail=matches[0];combined=movie.with_suffix('.detail.mp4')
        filters="[1:v]crop=1280:638:0:44,scale=860:428[detail];[0:v][detail]overlay=530:76:shortest=1,drawbox=x=528:y=74:w=864:h=432:color=0x688297:t=2[v]"
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-i',str(detail),'-filter_complex',filters,'-map','[v]','-map','0:a:0',
            '-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(combined)],check=True)
        combined.replace(movie);detail_proof=dict(file=str(detail.relative_to(root)),sha256=sha(detail),same_excerpt_id=eid,inset='new source-timed stage closeup; native band props remain in the larger scene')
    stamp_mp4(movie)
    proof=dict(file=str(movie.relative_to(root)),category=category,excerpt_id=eid,sha256=sha(movie),bytes=movie.stat().st_size,
        seconds=36,fps=20,resolution=[1920,1080],source_start=row['start_seconds'],source_sha256=row['sha256'],excerpt_wav_sha256=sha(audio),
        native_layouts=[{k:p[k] for k in ['flavor','bands','xsq_sha256','fseq_sha256','layout_sha256','frames','frame_ms']} for p in proofs],
        renderer_sha256=sha(Path(__file__)),
        stage_closeup=detail_proof,
        all_panels_same_audio_and_start=True,native_xlights_channel_playback=True,stock_model_projection_approximate=True,
        band_pose_output='stationary addressable RGB poses; continuous mesh animation in standalone movies',render_seconds=round(time.monotonic()-began,2))
    receipt.write_text(json.dumps(proof,indent=2)+'\n');print('LAYOUT_COMPLETE',name,proof['render_seconds'],flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--mode',choices=['comparison','embedded'],required=True);p.add_argument('--ids',nargs='*');a=p.parse_args()
    for eid in a.ids or (IDS if a.mode=='comparison' else IDS[:8]):render(a.root.resolve(),eid,a.mode)


if __name__=='__main__':main()
