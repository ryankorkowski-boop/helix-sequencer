"""Pinned-source native wiring diagnostics; no commercial music is bundled."""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, sys, wave
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path.cwd()))
from models.infinite_symphony_showcase import build_megagarden, mega_manifest
from core.keyboard_rung_export import export_keyboard_rungs
from core.drummer_physical_wiring import compile_contact_intervals, DRUM_CIRCUITS
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import read_fseq, _font


def write(root, path):
    ET.indent(root); ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def render(executable, folder, sequence):
    with (folder/'native_render.log').open('w') as log:
        subprocess.run([str(executable), '--headless', '-q', '-s', str(folder),
                        '-od', str(folder), str(sequence)], stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=600)
    return read_fseq(sequence.with_suffix('.fseq'))


def giant_probe(out, executable):
    folder=out/'Infinite_Symphony_Layout'; folder.mkdir(parents=True)
    garden=build_megagarden(); manifest=mega_manifest(garden); write_layout(garden,folder)
    source=folder/(garden.slug+'_Showcase.xsq'); root=ET.parse(source).getroot()
    for layer in root.findall('.//EffectLayer')+root.findall('.//SubModelEffectLayer'):
        layer.clear()
    root.find('head/comment').text='Native rung connectivity diagnostic, not a musical showcase'
    root.find('head/sequenceDuration').text='2.400'
    write(root,source)
    cues=[dict(pitch=21,start=.1,end=.3),dict(pitch=108,start=.4,end=.65),
          dict(pitch=60,start=.8,end=1.2),dict(pitch=64,start=.8,end=1.2),
          dict(pitch=67,start=1.3,end=1.6),dict(pitch=72,start=1.8,end=2.2)]
    sequence=folder/'Native_Keyboard_Rung_Diagnostic.xsq'
    report=export_keyboard_rungs(source,folder/'xlights_rgbeffects.xml',sequence,cues,duration=2.4)
    frames,step=render(executable,folder,sequence)
    assert len(frames)==48 and step==50
    assert frames.shape[1]==manifest['channel_count'],(frames.shape,manifest['channel_count'])
    hero=garden.models[-1]; checks=[]
    for time in (.15,.5,.9,1.4,1.9,2.3):
        expected=set()
        for c in cues:
            if c['start']<=time<c['end']:
                expected.update(hero.submodels[f"KEY_MIDI_{c['pitch']:03d}"])
        rgb=frames[round(time*1000/step),hero.start-1:hero.start-1+hero.channels].reshape(-1,3)
        actual=set((np.flatnonzero(rgb.max(axis=1))+1).tolist())
        assert actual==expected,(time,len(actual),len(expected))
        checks.append(dict(time=time,exact_native_rung_nodes=len(actual)))
    report.update(native_playback_verified=True,frames=len(frames),frame_ms=step,
                  channels=frames.shape[1],checks=checks,layout=manifest,
                  claim='Native headless import and addressable rung output; no complete band/music show')
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def physical_probe(out, executable):
    folder=out/'Physical_Drummer_Diagnostic';folder.mkdir()
    hits=[dict(time=.2+i*.06,target='kick') for i in range(8)]
    hits += [dict(time=1,target='snare',side='left'),dict(time=1.06,target='snare',side='right'),
             dict(time=1.4,target='cymbal_left'),dict(time=1.6,target='cymbal_right'),
             dict(time=1.8,target='tom_high'),dict(time=2,target='tom_mid'),
             dict(time=2.2,target='tom_floor'),dict(time=2.4,target='hi_hat')]
    plan=compile_contact_intervals(hits,duration=3)
    root=ET.parse(out/'Infinite_Symphony_Layout/xlights_rgbeffects.xml').getroot()
    models=root.find('models');models.clear();root.find('modelGroups').clear()
    for c in DRUM_CIRCUITS:
        ET.SubElement(models,'model',dict(name=c.key,DisplayAs='Single Line',
            StringType='Single Color White',StartChannel=str(c.channel),Controller='',
            LayoutGroup='Default',StartSide='B',Dir='L',parm1='1',parm2='1',parm3='1',
            versionNumber='7',WorldPosX=str(c.channel*3),WorldPosY='0',WorldPosZ='0',
            ScaleX='1',ScaleY='1',ScaleZ='1'))
    write(root,folder/'xlights_rgbeffects.xml')
    (folder/'xlights_networks.xml').write_text('<Networks/>')
    root=ET.parse(out/'Infinite_Symphony_Layout/Native_Keyboard_Rung_Diagnostic.xsq').getroot()
    for tag in ['ColorPalettes','EffectDB','DisplayElements','ElementEffects']:
        root.find(tag).clear()
    head=root.find('head')
    for name,value in {'sequenceDuration':'3.000','sequenceTiming':'10 ms',
                       'sequenceType':'Media','mediaFile':'Diagnostic_Only.wav',
                       'comment':'Synthetic source-authored native circuit timing diagnostic, not a song transcription'}.items():
        head.find(name).text=value
    ET.SubElement(root.find('ColorPalettes'),'ColorPalette').text='C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
    identifier=1
    for c in DRUM_CIRCUITS:
        ET.SubElement(root.find('DisplayElements'),'Element',name=c.key,type='model',visible='1',collapsed='1')
        parent=ET.SubElement(root.find('ElementEffects'),'Element',name=c.key,type='model')
        layer=ET.SubElement(parent,'EffectLayer')
        for e in plan['circuits'][c.key]:
            ref=len(root.find('EffectDB'));bright=round(e['brightness']*100)
            ET.SubElement(root.find('EffectDB'),'Effect').text=f'E_TEXTCTRL_Eff_On_Start={bright},E_TEXTCTRL_Eff_On_End={bright}'
            ET.SubElement(layer,'Effect',name='On',ref=str(ref),palette='0',id=str(identifier),
                startTime=str(round(e['start']*1000)),endTime=str(round(e['end']*1000)))
            identifier+=1
    root.find('nextid').text=str(identifier)
    sequence=folder/'Physical_Drummer_Diagnostic.xsq';write(root,sequence)
    sr=22050;y=np.zeros(sr*3,np.float32);rng=np.random.default_rng(146)
    for h in hits:
        t=np.arange(round(sr*.10))/sr
        sound=np.sin(2*np.pi*65*t)*np.exp(-t*45) if h['target']=='kick' else rng.uniform(-.4,.4,len(t))*np.exp(-t*35)
        start=round(h['time']*sr);y[start:start+len(t)]+=.5*sound
    with wave.open(str(folder/'Diagnostic_Only.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(y,-1,1)*32767).astype('<i2').tobytes())
    frames,step=render(executable,folder,sequence)
    assert len(frames)==300 and step==10 and frames.shape[1]==12,(frames.shape,step)
    kick=frames[:,8]>0;starts=np.flatnonzero(kick & ~np.r_[False,kick[:-1]])*step/1000
    assert len(starts)==8 and np.allclose(starts,[h['time'] for h in hits[:8]],atol=.01),starts
    assert np.all(frames[:,9]>0) and len(set(frames[:,9]))==1
    for side,contact,idle in [('left',1,10),('right',0,11)]:
        assert not np.any((frames[:,contact]>0)&(frames[:,idle]>0)),side
    movie=folder/'Native_Physical_Channel_Diagnostic.mp4'
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720',
        '-r','100','-i','-','-i',str(folder/'Diagnostic_Only.wav'),'-t','3','-c:v','libx264',
        '-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(movie)]
    p=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i,values in enumerate(frames):
            image=Image.new('RGB',(1280,720),(8,14,25));draw=ImageDraw.Draw(image)
            draw.text((35,24),'HELIX NATIVE PHYSICAL CHANNEL DIAGNOSTIC',font=_font(28),fill='white')
            draw.text((35,68),'Synthetic calibration audio · 8 rapid kicks · actual xLights FSEQ',font=_font(21),fill='#9FCCE4')
            for j,c in enumerate(DRUM_CIRCUITS):
                x=35+(j%4)*310;y=140+(j//4)*170;v=int(values[j]);color=(v,v,v)
                draw.rounded_rectangle((x,y,x+275,y+110),radius=12,fill=color,outline='#42748B',width=2)
                draw.text((x+10,y+120),f'{c.channel:02d}  {c.key}',font=_font(17),fill='#D7E9F4')
            draw.text((35,675),f'{i/100:.2f}s · Circuit mapping, not mechanical movement or a complete band',font=_font(20),fill='#AEC4D7')
            p.stdin.write(image.tobytes())
    finally:p.stdin.close()
    assert p.wait()==0
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True)
    report={'native_frames':len(frames),'frame_ms':step,'channels':12,'rapid_kick_onsets':starts.tolist(),
            'eight_independent_kicks_verified':True,'body_dim_native_value':int(frames[0,9]),
            'snare_idle_exclusion_verified':True,'tom_contact_pose_exported':False,
            'controller_addresses_assigned':False,'complete_band_verified':False,'synthetic_diagnostic':True}
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (folder/'channel_map.json').write_text(json.dumps([dict(channel=c.channel,key=c.key,physical_string=c.physical_string) for c in DRUM_CIRCUITS],indent=2)+'\n')
    return report


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--xlights',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    giant=giant_probe(out,a.xlights.resolve());physical=physical_probe(out,a.xlights.resolve())
    from validation.ctb16pc_native_proof import probe as ctb_probe
    ctb16pc=ctb_probe(out,a.xlights.resolve(),render)
    from validation.final_band_native_proof import probe
    bands=probe(out,a.xlights.resolve(),render)
    from validation.six_layout_native_proof import probe as six_probe
    six=six_probe(out,a.xlights.resolve(),render)
    from validation.original_kick_native_proof import probe as kick_probe
    original_kicks=kick_probe(out,a.xlights.resolve(),render)
    result={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'xlights_version':'2026.18','layout_native_import_verified':True,
        'rung_output_verified':True,'physical':physical,'ctb16pc':ctb16pc,'final_band_output':bands,
        'six_real_sampler_layouts_verified':len(six),'full_song_showcase_complete':False,
        'original_sampler_opening_kicks':original_kicks,
        'music_rights_cleared':False,'files':{str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in out.rglob('*') if p.is_file()}}
    (out/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))


if __name__=='__main__':main()
