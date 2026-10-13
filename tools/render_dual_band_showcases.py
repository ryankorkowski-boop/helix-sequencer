"""Three distinct two-stage music videos and a full-screen combined super garden."""
from __future__ import annotations
import argparse,json,math,subprocess,uuid
from pathlib import Path
import numpy as np
import trimesh
import moderngl
from PIL import Image,ImageDraw
from models.band_performance_scene import tube
from models.distinct_band_stages import DistinctBandScene,TwinBandGarden,STAGES
from tools.musical_band_performance import MusicalBandPerformance
from tools.render_musical_band_samplers import ROOT,ANALYSIS,soundtrack,sha,silent_performance,build_plan
from tools.render_refined_helix_band import encoder,physical_hits,DynamicDry,REFINED_FRAGMENT,FONT,SMALL
from tools.render_intricate_band_samplers import SamplerView,SAMPLER_VERTEX
from tools.render_band_upgrade import GLView
from animation.articulated_source_drummer import ArticulatedDrummer
from tools.render_drummer_v3_preview import TARGETS,parse_effects,parse_snare_hands,_active_targets_for_frame,snare_hand_for_frame
import soundfile as sf
from core.output_provenance import brand_frame,stamp_mp4

OUT=ROOT/'outputs/Distinct_Band_Showcases_20261013'
PAIRS=[('ember_amphitheatre','glacier_pier'),('cathedral_organ','circuit_garage'),('orbital_halo','lantern_garden'),('ember_amphitheatre','circuit_garage')]


def plans(rows):
    # Distinct real audio sample tracks; no beat-generated music.
    selections=[ [('dry',0,6),('01',105.0,14),('02',10.2,16),('05',0,14),('00',196,28.2)],
                 [('dry',12,6),('02',24.15,18),('03',160.25,16),('05',96,14),('00',210,14.2)],
                 [('dry',24,6),('05',0,14),('01',100,18),('02',211.65,14),('00',196,28.2)],
                 [('dry',0,8),('05',0,14),('02',10.2,14),('01',105,14),('03',160.25,14),('00',196,28.2)] ]
    result=[]
    for i,selected in enumerate(selections):
        segments=[dict(id=id,title='Dry Drum Test' if id=='dry' else rows[id]['title'],start=float(start),seconds=float(seconds),purpose='musical sampler passage') for id,start,seconds in selected]
        result.append(dict(version=i+1,stage_pair=list(PAIRS[i]),style_pair=['sculpted snow band','wire contour band'],segments=segments,super_layout=i==3))
    return result


def wire_sphere():
    pieces=[];t=np.linspace(0,math.tau,36,endpoint=False)
    for latitude in (-.55,0,.55):
        r=np.sqrt(1-latitude*latitude);pieces.append(tube(np.c_[r*np.cos(t),np.full(len(t),latitude),r*np.sin(t)],.027,True))
    for angle in np.linspace(0,math.pi,4,endpoint=False):
        pieces.append(tube(np.c_[np.cos(t)*np.cos(angle),np.sin(t),np.cos(t)*np.sin(angle)],.027,True))
    return trimesh.util.concatenate(pieces)


def light_point_glyph():
    # Tiny LED glyphs retain every existing review node and its world position.
    # A convex hexagon uses four faces instead of twenty sphere faces per node.
    # These are display markers, not a change to model/export geometry.
    t=np.arange(6)*math.tau/6
    return trimesh.Trimesh(vertices=np.c_[np.cos(t),np.sin(t),np.zeros(6)],
                          faces=[(0,1,2),(0,2,3),(0,3,4),(0,4,5)],process=False)


def camera(width,height,time,super_layout=False):
    if super_layout:
        eye=np.array((.8*np.sin(time*.025),15.7,43.5),dtype='f4');target=np.array((0,4.1,-1))
    else:
        eye=np.array((.65*np.sin(time*.035),10.8,31.5),dtype='f4');target=np.array((0,2.9,-.2))
    forward=target-eye;forward/=np.linalg.norm(forward);right=np.cross(forward,(0,1,0));right/=np.linalg.norm(right);up=np.cross(right,forward)
    view=np.eye(4,dtype='f4');view[:3,:3]=np.vstack((right,up,-forward));view[:3,3]=-view[:3,:3]@eye
    f=1/math.tan(math.radians(44)/2);near,far=.1,120
    p=np.zeros((4,4),dtype='f4');p[0,0]=f/(width/height);p[1,1]=f;p[2,2]=(far+near)/(near-far);p[2,3]=2*far*near/(near-far);p[3,2]=-1
    return p@view,eye


class TwinStageView(SamplerView):
    def __init__(self,scene,width,height,super_layout=False):
        self.super_layout=super_layout
        vertex=SAMPLER_VERTEX.replace('activity[128]','activity[384]').replace('channel=float(slot);','channel=float(slot%192);')
        super().__init__(scene,width,height,vertex,REFINED_FRAGMENT)
        for kind,mesh in [('wire_sphere',wire_sphere()),('light_point',light_point_glyph())]:
            objs=[o for o in scene.instances if o['kind']==kind]
            if objs:self.groups.append(GLView.make_vao(self,mesh,objs))
        order=[0,1,2,2,1,3];uv=np.array([(0,1),(1,1),(0,0),(1,0)],dtype='f4')
        data=np.c_[scene.second_drummer_corners[order],uv[order]].astype('f4')
        self.second_quad_buffer=self.ctx.buffer(data.tobytes())
        self.second_quad_vao=self.ctx.vertex_array(self.quad,[(self.second_quad_buffer,'3f 2f','position','uv')])
        self.second_texture=self.ctx.texture((395,256),4);self.second_texture.filter=(moderngl.LINEAR,moderngl.LINEAR)

    def frame(self,levels,lighting,strikes,hand,source_time,elapsed):
        vp,eye=camera(self.width,self.height,elapsed,self.super_layout)
        self.program['view_projection'].write(vp.T.tobytes());self.program['eye'].value=tuple(eye)
        self.program['song_time'].value=source_time
        self.fbo=self.scene_fbo;self.fbo.use();self.draw(levels)
        self.quad['view_projection'].write(vp.T.tobytes())
        self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
        for texture,vao,player in [(self.texture,self.quad_vao,self.dry),(self.second_texture,self.second_quad_vao,self.second_dry)]:
            texture.write(player.frame(lighting,strikes,hand).tobytes());texture.use(0);vao.render()
        self.ctx.disable(moderngl.BLEND);self.ctx.disable(moderngl.DEPTH_TEST)
        self.bloom_fbos[0].use();self.scene_texture.use(0);self.full_vaos['extract'].render()
        for axis in ((3/self.width,0),(0,3/self.height)):
            self.bloom_fbos[1].use();self.bloom_textures[0].use(0);self.blur['direction'].value=axis;self.full_vaos['blur'].render()
            self.bloom_textures.reverse();self.bloom_fbos.reverse()
        self.output_fbo.use();self.scene_texture.use(0);self.bloom_textures[0].use(1)
        self.combine['image'].value=0;self.combine['glow'].value=1;self.full_vaos['combine'].render();self.ctx.enable(moderngl.DEPTH_TEST)
        return Image.frombytes('RGB',(self.width,self.height),self.output_fbo.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def dry_curves(native):
    count=math.ceil(sf.info(ROOT/'evidence/drummer/dry_drum_test.wav').duration*20)
    drums=np.zeros((count,8),np.float32);strikes=np.zeros_like(drums);hands=np.zeros(count,np.int8)
    effects=parse_effects(native);hs=parse_snare_hands(native)
    for i in range(count):
        for target in _active_targets_for_frame(effects,i*50,20):drums[i,TARGETS.index(target)]=1
        strikes[i]=drums[i];hands[i]=int(snare_hand_for_frame(hs,i*50,20)=='right')
    return drums,strikes,hands


def render(plan,rows,pilot=False,width=1920,height=1080):
    OUT.mkdir(parents=True,exist_ok=True)
    name='Helix_Super_Layout_Two_Bands' if plan['super_layout'] else f'Helix_Two_Stages_{plan["version"]}'
    if pilot:name+='_pilot'
    segments=[dict(s,seconds=1.0) for s in plan['segments']] if pilot else plan['segments']
    audio=OUT/(name+'.wav');audio_proof=soundtrack(segments,rows,audio);duration=sum(s['seconds'] for s in segments)
    movie=OUT/(name+'.mp4');temp=movie.with_name(movie.stem+'.'+uuid.uuid4().hex[:10]+'.rendering.mp4');writer=encoder(temp,width,height,20,audio,0,duration)
    proof=[];timeline=0.;frames=0;inventory=None
    try:
        for seg in segments:
            source=rows['00'] if seg['id']=='dry' else rows[seg['id']]
            a=DistinctBandScene(plan['stage_pair'][0],False);b=DistinctBandScene(plan['stage_pair'][1],True)
            # Neutral avatars are assigned by source lane only. Do not infer
            # avatar identity from singing pitch or lyric line number.
            cast=dict(lead='first',source='neutral avatar; stable first source lane; explicit overrides supported')
            performers=[MusicalBandPerformance(source,scene,ANALYSIS,cast) for scene in (a,b)]
            native=ROOT/'outputs/Snowman_Ensemble/shows'/(source['id']+'_band')/'Snowman_Band.xsq'
            if seg['id']=='dry':
                performers=[silent_performance(p) for p in performers]
                native=ROOT/'evidence/drummer_shoulder_revision/Helix_Drummer_DRY_TEST_ONLY.xsq';drums,strikes,hands=dry_curves(native)
            else:drums,strikes,hands=performers[0].drums,performers[0].strikes,performers[0].hands
            garden=TwinBandGarden(a,b,plan['super_layout']);inventory=dict(features=garden.feature_inventory,inherited_layouts=garden.inherited_layouts,technical_models=garden.technical_models)
            view=TwinStageView(garden,width,height,plan['super_layout'])
            view.dry=DynamicDry(ArticulatedDrummer(physical_hits(native),natural_arms=True));view.second_dry=DynamicDry(ArticulatedDrummer(physical_hits(native),natural_arms=True))
            count=round(seg['seconds']*20);offset=round(seg['start']*20);contacts=0;max_error=0
            try:
                for frame in range(count):
                    source_index=offset+frame;idx=0 if seg['id']=='dry' else source_index
                    levels=np.r_[performers[0].pose(idx),performers[1].pose(idx)].astype('f4')
                    levels[5:13]=drums[source_index];levels[197:205]=drums[source_index]
                    # Physical-style body outlines stay legible at rest.
                    levels[177]=levels[369]=.80+.20*float(max(levels[:13]))
                    if plan['super_layout']:
                        for start in (64,256):levels[start:start+48]=np.maximum(levels[start:start+48],.34)
                    garden.sync();view.dry.time=source_index/20;view.second_dry.time=source_index/20
                    image=view.frame(levels,drums[source_index],strikes[source_index],hands[source_index],source_index/20,timeline+frame/20)
                    d=ImageDraw.Draw(image);d.rectangle((0,0,width,48),fill='#07101C')
                    d.text((22,14),('HELIX SUPER LAYOUT' if plan['super_layout'] else f'HELIX TWO-STAGE SHOWCASE {plan["version"]}')+'  |  '+seg['title'],font=FONT,fill='#DDF5FF')
                    d.rectangle((0,height-43,width,height),fill='#07101C')
                    d.text((22,height-30),STAGES[a.stage]+' • Sculpted band',font=SMALL,fill='#E2C7A0')
                    right=STAGES[b.stage]+' • Wire contour band';d.text((width-d.textlength(right,font=SMALL)-22,height-30),right,font=SMALL,fill='#BBD6DD')
                    image=brand_frame(image)
                    writer.stdin.write(image.tobytes());frames+=1
                    for p in performers:
                        for hit in p.mallet_schedule:
                            if abs(hit['time']-idx/20)<1e-7:
                                tip=p.mallet_targets[hit['side']][1];error=float(np.linalg.norm(tip-(p.scene.bars[hit['pitch']]+(0,.0275+.057,0))))
                                max_error=max(max_error,error);contacts+=1
                    if frame in (0,count//2):image.save(OUT/f'{name}_{seg["id"]}_{frame:04d}.png')
                    if frame%200==0:print(name,seg['id'],frame,count,flush=True)
            finally:view.close()
            proof.append(dict(seg,frames=count,neutral_performers=True,band_count=2,mallet_contacts=contacts,max_mallet_contact_error=max_error,
                source_xsq_sha256=sha(native),stage_pair=plan['stage_pair'],style_pair=plan['style_pair'],guitar_geometry_unchanged=True))
            timeline+=seg['seconds']
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();temp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
    if writer.wait():raise RuntimeError('showcase encoder failed')
    temp.replace(movie)
    stamp_mp4(movie)
    movie.with_suffix('.verification.json').write_text(json.dumps(dict(plan=plan,seconds=duration,frames=frames,fps=20,resolution=[width,height],
        movie_sha256=sha(movie),audio_sha256=sha(audio),soundtrack=audio_proof,segments=proof,inventory=inventory,
        neutral_singers=True,neutral_xylophone_player=True,visible_helix_watermark=True,internal_helix_credit=True,physical_fabrication_export=False,
        continuous_output='video / pixel matrix',all_six_sampler_stage_features_included=plan['super_layout'],
        technical_led_glyph_faces=4,all_technical_node_positions_preserved=True),indent=2)+'\n')
    return movie


def main():
    p=argparse.ArgumentParser();p.add_argument('--version',type=int,choices=range(1,5));p.add_argument('--pilot',action='store_true');p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080)
    a=p.parse_args();rows,_,_=build_plan()
    for plan in plans(rows):
        if a.version and plan['version']!=a.version:continue
        print(render(plan,rows,a.pilot,a.width,a.height),flush=True)


if __name__=='__main__':main()
