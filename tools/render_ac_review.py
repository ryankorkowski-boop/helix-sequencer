"""Native <=16-circuit band and independent AC MIDI rung demonstration."""
from pathlib import Path
import json,math,uuid
import numpy as np,moderngl
from PIL import Image,ImageDraw,ImageFont
from tools.render_spatial_comparison import PixelView
from tools.verify_spatial_native import geometry
from tools.build_helpers.ultimate_showcase_preview import read_fseq
from tools.render_refined_helix_band import encoder
from tools.render_approval_revision import sha
from core.output_provenance import brand_frame,stamp_mp4


def fitted(g):
    points=np.concatenate([m.points for m in g.models]);lo=points.min(0);hi=points.max(0);center=(lo+hi)/2;size=hi-lo
    def camera(w,h,t):
        angle=math.radians(5+7*np.sin(t/36*np.pi));direction=np.array((np.sin(angle)*.92,.27,np.cos(angle)*.92));direction/=np.linalg.norm(direction)
        distance=max(size[0]/(w/h),size[1])/(2*math.tan(math.radians(21)))*1.12+size[2]*.5
        eye=center+direction*distance;forward=center-eye;forward/=np.linalg.norm(forward)
        right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
        v=np.eye(4);v[:3,:3]=np.vstack((right,up,-forward));v[:3,3]=-v[:3,:3]@eye
        f=1/math.tan(math.radians(21));p=np.zeros((4,4));p[0,0]=f/(w/h);p[1,1]=f;p[2,2]=-1.0002;p[2,3]=-.2;p[3,2]=-1
        return (p@v).astype('f4')
    return camera


def render(root,eid='E14'):
    row=next(x for x in json.loads((root/'sources/selected_excerpts.json').read_text()) if x['excerpt_id']==eid)
    audio=root/'sources'/eid/'audio.wav';ctx=moderngl.create_standalone_context(backend='egl')
    band=geometry('AC16_Band');helix=geometry('AC_MIDI_Helix');left=PixelView(ctx,band,850,400);right=PixelView(ctx,helix,430,580)
    left.camera_callback=fitted(band);right.camera_callback=fitted(helix)
    a,step=read_fseq(root/'shows'/eid/'AC16_Band/Performance.fseq');b,_=read_fseq(root/'shows'/eid/'AC_MIDI_Helix/Performance.fseq')
    path=root/'videos'/'05_AC16_Band_and_88_Note_Helix.mp4';temp=path.with_name(path.stem+'.'+uuid.uuid4().hex+'.rendering.mp4')
    writer=encoder(temp,1280,720,20,audio,0,36);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    try:
        for i in range(720):
            image=Image.new('RGB',(1280,720),'#07111D');d=ImageDraw.Draw(image)
            d.text((18,16),'HELIX / AC16 CIRCUITS / NATIVE XLIGHTS OUTPUT',font=font,fill='#DBEFF6')
            d.text((18,51),'Seven snowmen: 10 / 9 / 11 / 15 / 15 / 14 / 14 circuits',font=small,fill='#AFCCD9')
            image.paste(left.frame(a[i],i/20),(0,86));image.paste(right.frame(b[i],i/20),(850,80));d=ImageDraw.Draw(image)
            d.text((880,82),'88 independent MIDI rungs',font=small,fill='#F2D4A4')
            d.text((880,107),'6 rung banks + 2 strand circuits',font=small,fill='#AFCCD9')
            for j,m in enumerate(band.models):
                y=492+j*22;d.text((18,y),m.details['review_role'].upper(),font=small,fill='#BBD8E4')
                for k in range(16):
                    value=int(a[i,m.start-1+k]) if k<m.channels else 0
                    color=(round(value*.40),round(value*.85),value) if value else '#102332'
                    d.rectangle((145+k*39,y,177+k*39,y+16),fill=color,outline='#294052')
            d.text((18,680),f'Source {row["start_seconds"]+i/20:06.2f}s / Actual dimmer values / Logical circuits; physical hardware not tested',font=small,fill='#A4C2D2')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            if i in (40,240,380,520,700):
                folder=root/'diagnostics'/path.stem;folder.mkdir(parents=True,exist_ok=True);image.save(folder/f'frame_{i:04}.jpg',quality=94)
    finally:writer.stdin.close();ctx.release()
    if writer.wait():raise RuntimeError('AC comparison encoder failed')
    temp.replace(path);stamp_mp4(path)
    receipt=dict(file=str(path.relative_to(root)),excerpt_id=eid,sha256=sha(path),excerpt_sha256=sha(audio),
        original_audio_sha256=row['sha256'],source_start=row['start_seconds'],source_end=row['end_seconds'],frames=720,fps=20,seconds=36,
        panels=2,all_panels_same_source_clock=True,native_xlights_rendered=True,
        source_fseq=[dict(file=str((root/'shows'/eid/name/'Performance.fseq').relative_to(root)),sha256=sha(root/'shows'/eid/name/'Performance.fseq')) for name in ('AC16_Band','AC_MIDI_Helix')],
        maximum_circuits_per_model=max(m.channels for m in band.models+helix.models),
        physical_hardware_tested=False,renderer_sha256=sha(Path(__file__)))
    path.with_suffix('.render.json').write_text(json.dumps(receipt,indent=2)+'\n');print('AC_VIDEO_COMPLETE',path,flush=True)

if __name__=='__main__':
    import sys
    render(Path(sys.argv[1]))
