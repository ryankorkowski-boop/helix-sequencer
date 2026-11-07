"""Real-audio spiral/wave garden, matching XSQ, compressed FSEQ and preview."""
from __future__ import annotations
import json,math,struct,subprocess,uuid,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import zstandard
from models.flourish_showcase import build_flourish_garden,envelope
from tools.render_dual_band_showcases import plans,dry_curves
from tools.render_musical_band_samplers import ROOT,ANALYSIS,build_plan,soundtrack
from tools.render_refined_helix_band import encoder
from tools.build_helpers.ultimate_showcase import write_layout,_write_xml
from tools.build_helpers.ultimate_showcase_preview import _project,_base,_rgb,_font,read_fseq
from core.output_provenance import brand_frame,stamp_mp4,stamp_xml,write_manifest,sha256

OUT=ROOT/'outputs/Spiral_Symphony_20261013'


def source_curves(segments):
    energies=[];attacks=[];time=0.;proof=[]
    for segment in segments:
        n=round(segment['seconds']*20);offset=round(segment['start']*20)
        if segment['id']=='dry':
            _,strikes,_=dry_curves(ROOT/'evidence/drummer_shoulder_revision/Helix_Drummer_DRY_TEST_ONLY.xsq')
            signal=strikes[offset:offset+n].max(axis=1);energy=signal.copy()
            indices=np.flatnonzero((signal>0)&np.r_[True,signal[:-1]==0])
            source='native dry drum target events'
        else:
            with np.load(ANALYSIS/segment['id']/'performance_curves.npz') as curves:
                signal=np.maximum.reduce([curves[k][offset:offset+n] for k in ('guitar_attack','piano_attack','bass_attack')])
                energy=np.maximum.reduce([curves[k][offset:offset+n] for k in ('guitar_energy','piano_energy','bass_energy','vocal_energy')])
            indices,_=find_peaks(signal,height=.06,distance=3,prominence=.025)
            source='retained guitar, piano and bass source attacks; measured phrase energy'
        energies.extend(np.clip(energy,0,1));attacks.extend((time+i/20,float(np.clip(signal[i],.12,1))) for i in indices)
        proof.append(dict(segment,accepted_attack_count=len(indices),source=source))
        time+=segment['seconds']
    return np.asarray(energies,np.float32),attacks,proof


def write_music_xsq(g,levels,audio):
    root=ET.Element('xsequence',{'BaseChannel':'1','FixedPointTiming':'1','ModelBlending':'true'})
    head=ET.SubElement(root,'head');count=levels.shape[1]
    for k,v in dict(version='2026.18',author='Helix',song=g.title,comment='Source-driven musical flourishes; artistic path delays; control fixtures idle',
                    sequenceTiming='50 ms',sequenceType='Media',sequenceDuration=f'{count/20:.3f}',mediaFile=audio.name).items():ET.SubElement(head,k).text=v
    nextid=ET.SubElement(root,'nextid');palettes=ET.SubElement(root,'ColorPalettes');db=ET.SubElement(root,'EffectDB')
    displays=ET.SubElement(root,'DisplayElements');elements=ET.SubElement(root,'ElementEffects')
    palette_ids={};identifier=1
    for value in range(101):ET.SubElement(db,'Effect').text=f'E_TEXTCTRL_Eff_On_Start={value},E_TEXTCTRL_Eff_On_End={value}'
    for row,model in enumerate(g.models):
        if model.kind!='pixel':continue
        ET.SubElement(displays,'Element',{'type':'model','name':model.name,'visible':'1','collapsed':'1'})
        element=ET.SubElement(elements,'Element',{'type':'model','name':model.name});base=ET.SubElement(element,'EffectLayer')
        if model.details.get('double_helix'):
            layers=[(ET.SubElement(element,'SubModelEffectLayer',{'name':part,'layer':'0'}),model.colors[model.submodels[part][0]-1]) for part in ('STRAND_A','STRAND_B','RUNGS')]
        else:layers=[(base,model.colors[0])]
        values=levels[row];boundaries=np.r_[0,np.flatnonzero(np.diff(values))+1,count]
        for layer,color in layers:
            if color not in palette_ids:
                palette_ids[color]=len(palette_ids);ET.SubElement(palettes,'ColorPalette').text=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'
            for start,end in zip(boundaries[:-1],boundaries[1:]):
                ET.SubElement(layer,'Effect',{'name':'On','ref':str(int(values[start])),'palette':str(palette_ids[color]),
                    'startTime':str(start*50),'endTime':str(end*50),'id':str(identifier)});identifier+=1
    nextid.text=str(identifier);ET.SubElement(root,'DataLayers');ET.SubElement(root,'lastView').text='0'
    path=OUT/(g.slug+'.xsq');_write_xml(root,path);stamp_xml(path)
    return path,identifier-1


def write_fseq(g,levels):
    count=levels.shape[1];channels=sum(m.channels for m in g.models);chunks=[]
    compressor=zstandard.ZstdCompressor(level=5)
    for begin in range(0,count,100):
        frames=np.zeros((min(100,count-begin),channels),np.uint8)
        for row,model in enumerate(g.models):
            if model.kind!='pixel':continue
            colors=_rgb(model.colors).astype(np.float32)
            frames[:,model.start-1:model.start-1+model.channels]=(colors[None,:,:]*levels[row,begin:begin+len(frames),None,None]/100).astype(np.uint8).reshape(len(frames),-1)
        chunks.append((begin,compressor.compress(frames.tobytes())))
    offset=32+len(chunks)*8;header=bytearray(32);header[:4]=b'PSEQ'
    struct.pack_into('<HBBHII',header,4,offset,0,2,32,channels,count)
    header[18]=50;header[20]=1;header[21]=len(chunks)
    path=OUT/(g.slug+'.fseq')
    with path.open('wb') as stream:
        stream.write(header)
        for begin,chunk in chunks:stream.write(struct.pack('<II',begin,len(chunk)))
        for _,chunk in chunks:stream.write(chunk)
    return path


def render(g,frames,audio,segments,width=1920,height=1080):
    # Preproject fixed geometry once. Every video pixel comes from decoded FSEQ.
    points=np.concatenate([m.points for m in g.models if m.kind=='pixel'])
    addresses=np.concatenate([np.arange(m.start-1,m.start-1+m.channels).reshape(-1,3) for m in g.models if m.kind=='pixel'])
    p=_project(points,width,height,7,18);x,y=np.rint(p[:,0]).astype(int),np.rint(p[:,1]).astype(int)
    mask=(x>1)&(x<width-2)&(y>1)&(y<height-2);x,y,addresses=x[mask],y[mask],addresses[mask]
    background=_base(width,height,g.title);font=_font(18);large=_font(20)
    movie=OUT/(g.slug+'.mp4');temporary=movie.with_name(movie.stem+'.'+uuid.uuid4().hex[:10]+'.rendering.mp4')
    writer=encoder(temporary,width,height,20,audio,0,len(frames)/20);timeline=np.cumsum([s['seconds'] for s in segments])
    try:
        for i,channels in enumerate(frames):
            screen=np.zeros((height,width,3),np.uint8);colors=channels[addresses]
            for dx,dy,factor in ((0,0,1),(-1,0,.4),(1,0,.4),(0,-1,.4),(0,1,.4)):
                scaled=(colors*factor).astype('u1')
                for c in range(3):np.maximum.at(screen[:,:,c],(y+dy,x+dx),scaled[:,c])
            lights=Image.fromarray(screen);image=ImageChops.add(background,ImageChops.add(lights,lights.filter(ImageFilter.GaussianBlur(3))))
            draw=ImageDraw.Draw(image);seg=segments[min(len(segments)-1,int(np.searchsorted(timeline,i/20,side='right')))]
            draw.text((88,982),'FOUR SPIRAL RUNS  /  TWO WAVE PROMENADES  /  27 NATIVE MODEL FAMILIES',font=large,fill='#C8EDF2')
            draw.text((88,1023),seg['title']+'  |  Matching FSEQ playback • 50 ms frames • Audio in. Lights out.',font=font,fill='#739AAE')
            image=brand_frame(image);writer.stdin.write(image.tobytes())
            if i in (80,220,520,980,1500):image.save(OUT/f'preview_{i:04d}.jpg')
            if i%200==0:print('Spiral Symphony',i,len(frames),flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temporary.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
    if writer.wait():raise RuntimeError('Flourish encoding failed')
    subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(temporary)],check=True,capture_output=True)
    stamp_mp4(temporary);temporary.replace(movie);return movie


def main():
    OUT.mkdir(parents=True,exist_ok=True);g=build_flourish_garden();manifest=write_layout(g,OUT)
    rows,_,_=build_plan();segments=plans(rows)[3]['segments'];audio=OUT/(g.slug+'.wav');audio_proof=soundtrack(segments,rows,audio)
    energy,attacks,source_proof=source_curves(segments)
    levels=np.stack([np.rint(envelope(m,len(energy),attacks,energy)*100).astype('u1') if m.kind=='pixel' else np.zeros(len(energy),'u1') for m in g.models])
    xsq,effects=write_music_xsq(g,levels,audio);fseq=write_fseq(g,levels);frames,step=read_fseq(fseq)
    assert len(frames)==len(energy) and step==50
    for row,m in enumerate(g.models):
        if m.kind!='pixel':assert not frames[:,m.start-1:m.start-1+m.channels].any();continue
        expected=(_rgb(m.colors).astype(np.float32)[None,:,:]*levels[row,:,None,None]/100).astype('u1').reshape(len(frames),-1)
        assert np.array_equal(frames[:,m.start-1:m.start-1+m.channels],expected)
    movie=render(g,frames,audio,segments)
    proof=dict(seconds=len(frames)/20,frames=len(frames),fps=20,resolution=[1920,1080],segments=segments,soundtrack=audio_proof,
        source_analysis=source_proof,accepted_source_attacks=len(attacks),native_on_effects=effects,models=manifest['model_count'],
        flow_models=80,ordered_flow_groups=6,channel_count=frames.shape[1],fseq_full_roundtrip=True,preview_uses_decoded_fseq=True,
        xsq_fseq_brightness_contract='same integer brightness and palette; native app rendering still needs import verification',
        native_xlights_import_verified=False,controller_output_verified=False,control_fixtures_idle=True,
        visible_helix_watermark=True,internal_helix_credit=True,movie_sha256=sha256(movie),audio_sha256=sha256(audio))
    movie.with_suffix('.verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    (OUT/'README.txt').write_text('HELIX SPIRAL SYMPHONY\n\nOpen this extracted folder as a NEW xLights show. Open Helix_Spiral_Symphony.xsq for the 92.2-second real-audio showcase.\nThe MP4 is rendered from the decoded matching FSEQ. Six ordered flow groups contain 48 spiral and 32 wave models.\nAll 27 stock families are included; DMX/servo/AC control fixtures remain idle. No controller networks are configured.\nRetained source attacks launch artistic staggered runs; this is not a claim of instrument-perfect transcription.\nOriginal user assets are unchanged. Review native import and configure your own controllers before physical use.\nDesign feet and illustrative native-family review coordinates are not a fabrication plan. Music clearance is separate.\nMade with Helix | Audio in. Lights out.\n')
    for xml in OUT.glob('*.xml'):stamp_xml(xml)
    write_manifest(OUT,[xsq,fseq,movie,audio,OUT/'xlights_rgbeffects.xml',OUT/'xlights_networks.xml'])
    print(movie,flush=True)


if __name__=='__main__':main()
