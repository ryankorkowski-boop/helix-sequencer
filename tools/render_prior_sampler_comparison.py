"""Six simultaneous layouts from streamed native xLights FSEQ channel bytes."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw
from models.showcase_flavors import build_flavor
from tools.fseq_pixel_preview import FseqReader
from tools.showcase_audio_preview import NativeSongView
from tools.render_refined_helix_band import encoder,FONT,SMALL
from tools.build_prior_sampler_layouts import SAMPLER_SHA
from tools.render_intricate_band_samplers import sha
from tools.render_prior_sampler_band import TITLES


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audio',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--pilot',action='store_true')
    a=p.parse_args();assert sha(a.audio)==SAMPLER_SHA;root=a.output.resolve();rows=json.loads((root/'six_layouts/manifest.json').read_text())['runs'];assert len(rows)==6
    views=[];readers=[];iterators=[];gardens=[];proof=[]
    for row in rows:
        folder=root/'six_layouts'/row['folder'];fseq=(folder/row['xsq']).with_suffix('.fseq');g=build_flavor(row['flavor']);gardens.append(g)
        r=FseqReader(fseq);assert r.info.step_ms==50 and r.info.frames==3603
        for m in g.models:
            if m.kind=='pixel':
                assert r.offset_for_channel(m.start) is not None and r.offset_for_channel(m.start+m.channels-1) is not None
        views.append(NativeSongView(g,'SAME REAL SAMPLER',640,360,halo_scale=2));readers.append(r);iterators.append(r.iter_frames())
        proof.append(dict(layout=row['layout'],fseq_sha256=sha(fseq),xsq_sha256=sha(folder/row['xsq']),native_frames=r.info.frames,
            channels=r.info.channels,active_model_frames={m.name:0 for m in g.models if m.kind=='pixel'},control_activity=[]))
    duration=5 if a.pilot else sf.info(a.audio).duration
    movie=root/('Helix_Six_Layouts_Pilot.mp4' if a.pilot else 'Helix_Six_Layouts_Same_Real_Sampler.mp4');temp=movie.with_name(movie.stem+'.rendering.mp4')
    writer=encoder(temp,1920,900,20,a.audio,0,duration)
    try:
        for i in range(math.ceil(duration*20)):
            image=Image.new('RGB',(1920,900),'#07101C');draw=ImageDraw.Draw(image)
            draw.text((24,16),f'SIX HELIX LAYOUTS  |  {TITLES[min(5,i//600)]}  |  {i/20:06.2f}s',font=FONT,fill='#DDF5FF')
            for j,(view,it,g) in enumerate(zip(views,iterators,gardens)):
                packed=np.frombuffer(next(it),np.uint8)
                values=np.zeros(max(m.start-1+m.channels for m in g.models),np.uint8)
                offset=0
                for start,length in readers[j].info.ranges:
                    values[start:start+length]=packed[offset:offset+length]
                    offset+=length
                assert offset==len(packed)
                assert len(values)>=max(m.start-1+m.channels for m in g.models)
                for m in g.models:
                    active=bool(values[m.start-1:m.start-1+m.channels].any())
                    if m.kind=='pixel':proof[j]['active_model_frames'][m.name]+=int(active)
                    elif active and m.name not in proof[j]['control_activity']:proof[j]['control_activity'].append(m.name)
                x=(j%3)*640;y=60+(j//3)*410
                frame=view.frame(values)
                # Equal fit within each panel, with an unambiguous native source label.
                image.paste(frame,(x,y));draw.text((x+18,y+367),rows[j]['layout'],font=FONT,fill='#BFDCE8')
            draw.text((24,878),'ACTUAL XLIGHTS FSEQ COLORS  •  Original recovered WAV  •  Identical timing across all six',font=SMALL,fill='#AEC5D5')
            writer.stdin.write(image.tobytes())
            if i in (0,600,1200,1800,2400,3000,3500):image.save(root/f'Six_Layouts_Frame_{i:04}.png')
            if i%200==0:print('six layouts',i,math.ceil(duration*20),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
    if writer.wait():raise RuntimeError('Six-layout encoder failed')
    temp.replace(movie)
    assert all(not p['control_activity'] for p in proof),'Native RGB show activated control channels'
    movie.with_suffix('.verification.json').write_text(json.dumps(dict(audio_sha256=SAMPLER_SHA,seconds=duration,frames=math.ceil(duration*20),
        sha256=sha(movie),layouts=proof,source='actual native xLights2026.18 FSEQ',geometry='exact custom nodes; illustrative stock geometry'),indent=2)+'\n')


if __name__=='__main__':main()
