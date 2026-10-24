"""Clearly labeled solid OpenGL visualization of the same retained source cues.

This is supplemental to native xLights exports, never a replacement for them.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import ImageDraw,ImageFont
from models.final_band_scene import FinalBandScene
from models.band_performance_scene import matrix,line_matrix,TUNINGS
from models.band_motion_refinement import elbow_3d
from models.band_sampler_logic import SHAPE_NAMES
from models.expressive_band_face import lip_ring_mesh
from models.keyboard_motion_plan import plan_keyboard_hands
from models.band_instrument_logic import event_curves
from music.note_events import NoteEvent
from tools.phoneme_vocal_export import FIXTURE
from tools.phoneme_source import digest, EXPECTED_SHA256
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX
from tools.render_refined_helix_band import REFINED_FRAGMENT,encoder,DynamicDry
from animation.articulated_source_drummer import ArticulatedDrummer


def render(source, output):
    source,output=Path(source),Path(output)
    audio=source/'media/Phoneme_Test_Hook.mp3'
    if digest(audio)!=EXPECTED_SHA256:raise ValueError('Original source mismatch')
    plan_path=next((source/'sequence').glob('*.snowman_band.json'))
    plan=json.loads(plan_path.read_text())['cues']
    scene=FinalBandScene();n=698
    keys={int(o['name'].rsplit('_',1)[1]):o['matrix'][:3,3].copy() for o in scene.instances if o['name'].startswith('piano_key_')}
    notes=[NoteEvent(c['start_ms']/1000,c['end_ms']/1000,round(c['pitch_midi']),max(.01,min(1,c['velocity'])),source='retained_harmonic_polyphony') for c in plan['keyboardist'] if round(c['pitch_midi']) in keys]
    held,vel,attack,phase=event_curves(notes,n,6,release=0)
    rigs={r['side']:r for r in scene.rigs if r['role']=='piano'}
    wrists,assignments,motion=plan_keyboard_hands(held,vel,keys,rigs,max_step=.030,max_acceleration=.010,anticipation_frames=12)
    events={role:[] for role in ('bass','guitar')}
    for role,key in [('bass','bassist'),('guitar','guitarist')]:
        for c in plan[key]:
            if role=='guitar' and c['kind']=='chord_change':continue
            pitch=round(c.get('pitch_midi',40));possible=[(s,pitch-open_pitch,pitch) for s,open_pitch in enumerate(TUNINGS[role]) if 0<=pitch-open_pitch<=24]
            route=min(possible,key=lambda x:abs(x[1]-4)) if possible else None
            events[role].append((c,route))
    hits=[];unresolved=0
    for j,c in enumerate(plan['drummer']):
        target={'kick':'KICK','snare':'SNARE','hihat':'HI_HAT','cymbal':'CYMBAL_RIGHT'}.get(c['kind'])
        if target is None:unresolved+=1;continue
        hits.append(dict(time=c['start_ms']/1000,target='HX_SNOWMAN_DRUMMER_V3_'+target,
                         side='left' if c['kind']=='snare' and j%2 else 'right',velocity=c.get('velocity',1)))
    player=ArticulatedDrummer(hits,natural_arms=True,cache_lighting=True)
    view=SamplerView(scene,1280,720,SAMPLER_VERTEX.replace('activity[128]','activity[192]'),REFINED_FRAGMENT)
    view.groups.append(view.make_vao(lip_ring_mesh(),[o for o in scene.instances if o['kind']=='lip_ring']))
    view.dry=DynamicDry(player)
    cache=np.load(FIXTURE/'acoustic_vocal_clocks.npz',allow_pickle=False)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    output.parent.mkdir(parents=True,exist_ok=True)
    writer=encoder(output,1280,720,20,audio,0,34.88)
    try:
        for i in range(n):
            t=i/20;levels=np.zeros(192,'f4');levels[177]=.7
            for k,role in enumerate(('lead','harmony')):
                lane='estimated_lead' if k==0 else 'estimated_backing';j=min(i*5,len(cache[lane+'_energy'])-1)
                energy=float(cache[lane+'_energy'][j]);shape=SHAPE_NAMES[int(cache[lane+'_shapes'][j])] if energy else 'REST'
                scene.update_singer_mouth(role,shape,energy);levels[3+k]=energy*.6
                # Match the restrained native aperture scale, preserving clocks.
                for part in ('cavity','lips','tongue','teeth'):
                    item=scene.instances[scene.expressive_mouths[role][part]]
                    item['matrix'][:3,:2]*=.42
            for role,first in [('bass',13),('guitar',17)]:
                active=[(c,r) for c,r in events[role] if c['start_ms']<=t*1000<c['end_ms']]
                route=next((r for c,r in active if r),None)
                gain=max((float(c.get('expression',{}).get('brightness',.8)) for c,r in active),default=0)
                if route:levels[first+route[0]]=gain
                elif active:levels[first:first+(4 if role=='bass' else 6)]=gain*.6
                levels[int(role=='guitar')]=gain*.5
                for string in range(len(scene.strings[role])):scene.vibrate(role,string,float(levels[first+string]),t)
                for rig in [r for r in scene.rigs if r['role']==role]:
                    hand=rig['hand'].copy()
                    if active and rig['side'] in ('pluck','strum'):
                        age=(t*1000-active[-1][0]['start_ms'])/1000
                        hand[1]-=.18*gain*max(0,1-age/.2)
                    if route and rig['side']=='finger':hand=scene.guitar_contact(route[0],route[1]) if role=='guitar' else scene.bass_contact(route[0],route[1])
                    shoulder=rig['shoulder'];elbow=elbow_3d(shoulder,hand,*rig['link_lengths'],(-.8,-.2,.8))
                    a,b,c=rig['ids'];scene.instances[a]['matrix']=line_matrix(shoulder,elbow,.046);scene.instances[b]['matrix']=line_matrix(elbow,hand,.046);scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            for pitch,value in zip(held[i],vel[i]):
                if pitch>=0:levels[23+int(pitch)-48]=value
            for rig in rigs.values():
                hand=wrists[rig['side']][i];shoulder=rig['shoulder'];elbow=elbow_3d(shoulder,hand,*rig['link_lengths'],(-.8 if rig['side']=='left' else .8,-.2,.8))
                a,b,c=rig['ids'];scene.instances[a]['matrix']=line_matrix(shoulder,elbow,.046);scene.instances[b]['matrix']=line_matrix(elbow,hand,.046);scene.instances[c]['matrix']=matrix(hand,(.10,.075,.08))
            lighting=np.zeros(8,'f4');strikes=np.zeros(8,'f4')
            for h in hits:
                age=t-h['time']
                if 0<=age<.30:
                    target=h['target'].rsplit('_V3_',1)[1];index={'KICK':0,'SNARE':1,'HI_HAT':2,'CYMBAL_RIGHT':7}[target]
                    lighting[index]=max(lighting[index],h['velocity']*math.exp(-age/.10));strikes[index]=float(age<.05)
            levels[5:13]=lighting
            levels[64:112]=max(float(levels[:3].max()),float(lighting.max()))*.65
            view.dry.time=t
            image=view.frame(levels,lighting,strikes,int(i%2),t,t)
            draw=ImageDraw.Draw(image);draw.rectangle((0,0,1280,43),fill='#07111E')
            draw.text((16,12),'SOLID 3D RECOVERY DIAGNOSTIC | OpenGL | approved band identity unverified',font=font,fill='white')
            writer.stdin.write(image.tobytes())
            if i in (160,360,560):image.save(output.with_name(output.stem+f'_{i:04}.png'))
            if i%100==0:print('SOLID_FRAME',i,n,flush=True)
    finally:
        writer.stdin.close();view.close();cache.close()
    if writer.wait():raise RuntimeError('Solid visualization encoder failed')
    output.with_suffix('.json').write_text(json.dumps(dict(renderer='OpenGL; NOT native xLights',
        geometry='FinalBandScene',source_audio_sha256=EXPECTED_SHA256,source_plan_sha256=digest(plan_path),
        vocal_clocks='same retained two-stage source estimates as native collection',
        keyboard_motion=motion,unlocalized_tom_events_omitted=unresolved,
        cymbal_location='right-side staging assumption; source side unverified',owner_visual_approval='rejected; approved reference still missing'),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();render(a.source,a.output)
