"""Connected source-art drummer with time-dependent anticipation/contact/recovery.

The original body, surfaces and shaft pixels are retained. Articulated sleeve
contours use neutral wire colors consistent with the original arm artwork. This is an opt-in
Helix compositor; the approved v7 compositor remains the comparison baseline.
"""
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance,ImageChops
from models.band_motion_refinement import elbow_2d,smoothstep
from tools.drummer_v3_visual_masks import (load_spec,exact_geometry,target_surface_key,
    compose_emissive,strike_transform,refine_actuator_to_source_art,build_zone_mask,idle_art_key)
from tools.render_drummer_v3_preview import SOURCE,TARGETS

@dataclass(frozen=True)
class BandLighting:
    idle_body: float=1.20
    idle_instrument: float=.40
    idle_arm: float=.58
    strike: float=1.35
    def __post_init__(self):
        if any(not 0<=v<=2 for v in (self.idle_body,self.idle_instrument,self.idle_arm,self.strike)):
            raise ValueError('brightness must be in [0,2]')

class ArticulatedDrummer:
    def __init__(self, hits, lighting=BandLighting()):
        self.source=Image.open(SOURCE).convert('RGBA');self.spec=load_spec();self.lighting=lighting
        self.geometry=exact_geometry(self.source,self.spec);self.masks=self.geometry['masks']
        self.scale=np.array(self.source.size)-1
        self.zones={z['id']:z for z in self.spec['zones']};self.hits=sorted(hits,key=lambda e:e['time'])
        self.last_joints={};self.motion_rejections=[];self.hand_reassignments=[]
        # Keep the photographed torso/scarf/head and independently lit kit.
        # Remove static ready arms: the dynamic arms below own those pixels.
        idle=self.masks[idle_art_key()].copy()
        for side in ('LEFT','RIGHT'):
            alpha=self.geometry['actuators'][side+'_ARM_STICK'].getchannel('A')
            idle=Image.composite(Image.new('RGBA',idle.size,(0,0,0,255)),idle,alpha)
        if '__torso_shoulders__' in self.masks:
            idle=Image.composite(Image.new('RGBA',idle.size,(0,0,0,255)),idle,self.masks['__torso_shoulders__'])
        d=ImageDraw.Draw(idle)
        for points in [[(.453,.432),(.440,.440),(.425,.445)],[(.570,.434),(.588,.443),(.603,.452)]]:
            d.line([tuple(np.array(p)*self.scale) for p in points],fill=(168,176,174,255),width=4,joint='curve')
        self.masks=deepcopy(self.masks);self.masks[idle_art_key()]=idle
        shaft=self.zones['SNARE_ARM_STICK']['strike']
        self.shaft= self.source.copy()
        self.shaft.putalpha(refine_actuator_to_source_art(self.source,build_zone_mask(self.source.size,shaft['source_stick'])))
        self.shaft_spec=shaft
        self.roots={'left':np.array((.425,.445))*self.scale,'right':np.array((.603,.452))*self.scale}
        self.rest={'left':np.array((.362,.473))*self.scale,'right':np.array((.671,.476))*self.scale}
        self.lengths={'left':(39.,39.),'right':(39.,39.)}
        self.targets={}
        for item in self.spec['lighting_targets']:
            name='HX_SNOWMAN_DRUMMER_V3_'+item['id']
            acts=[self.zones[a] for a in item['actuators'] if self.zones[a].get('strike')]
            for zone in acts:
                strike=zone['strike'];side=strike['striking_arm']
                self.targets[name,side]=(np.asarray(strike['contact'])*self.scale,np.asarray(strike['grip'])*self.scale)
        self.targets[TARGETS[1],'right']=(np.asarray(self.zones['SNARE_RIGHT_ARM_STICK']['strike']['contact'])*self.scale,
            np.asarray(self.zones['SNARE_RIGHT_ARM_STICK']['strike']['grip'])*self.scale)
        # The old foot lane does not create an extra arm: hats have a supported
        # right-hand contact on the actual hi-hat surface in this new compositor.
        pts=np.asarray(self.zones['HI_HAT_SURFACE']['commands'][0]['points'])*self.scale
        tip=np.array((pts[:,0].mean(),pts[:,1].min()+3))
        self.targets[TARGETS[2],'right']=(tip,tip+(-44,-22))
        # Resolve physically impossible same-hand travel without deleting a
        # polyphonic detector event or inventing a different drum identity.
        requested=self.hits;self.hits=[];last={}
        for event in requested:
            preferred=event['side'];choices=[preferred]
            if event['target']==TARGETS[1]:choices.append('right' if preferred=='left' else 'left')
            selected=None
            for side in choices:
                if (event['target'],side) not in self.targets:continue
                tip,grip=self.targets[event['target'],side]
                direction=(tip-grip)/np.linalg.norm(tip-grip);wrist=tip-direction*55
                distance=np.linalg.norm(wrist-self.roots[side])
                if not 0<distance<sum(self.lengths[side]):continue
                previous=last.get(side)
                if previous and event['time']-previous['time']<.35:
                    allowed=400*max(0,event['time']-previous['time'])+6
                    if np.linalg.norm(wrist-previous['wrist'])>allowed:continue
                selected=side;break
            if selected is None:
                self.motion_rejections.append(dict(event,reason='same_hand_travel_unplayable'));continue
            planned=dict(event,side=selected)
            if selected!=preferred:self.hand_reassignments.append(dict(time=event['time'],target=event['target'],source_hand=preferred,rendered_hand=selected))
            self.hits.append(planned);last[selected]=dict(time=event['time'],wrist=wrist)
        self.body_mask=Image.new('L',self.source.size,0)
        ImageDraw.Draw(self.body_mask).polygon([(int(x*self.scale[0]),int(y*self.scale[1])) for x,y in
            [( .36,.25),(.66,.25),(.66,.47),(.60,.55),(.41,.55),(.34,.46)]],fill=255)
        for target in TARGETS:self.body_mask=ImageChops.subtract(self.body_mask,self.masks[target_surface_key(target)])

    def _pose(self,side,time):
        lane=[e for e in self.hits if e['side']==side and (e['target'],side) in self.targets]
        previous=next((e for e in reversed(lane) if e['time']<=time),None)
        following=next((e for e in lane if e['time']>time),None)
        ready=self.rest[side].copy();direction=np.array((.8 if side=='left' else -.8,.6));ready_angle=np.arctan2(direction[1],direction[0])
        def target(event):
            contact,grip=self.targets[event['target'],side]
            strike_direction=(contact-grip)/np.linalg.norm(contact-grip)
            return contact-strike_direction*55,np.arctan2(strike_direction[1],strike_direction[0])
        wrist=ready.copy();angle=ready_angle;gain=0.;lift=0.
        if previous and following and following['time']-previous['time']<=.35:
            phase=(time-previous['time'])/(following['time']-previous['time']);weight=smoothstep(phase)
            start,a=target(previous);end,b=target(following)
            wrist=start*(1-weight)+end*weight
            delta=(b-a+np.pi)%(2*np.pi)-np.pi;angle=a+weight*delta
            gain=previous.get('velocity',1)*(1-weight)+following.get('velocity',1)*weight
            lift=6*np.sqrt(gain)*np.sin(np.pi*phase)
        elif following and following['time']-time<.14:
            weight=smoothstep(1-(following['time']-time)/.14);end,b=target(following)
            wrist=ready*(1-weight)+end*weight
            delta=(b-ready_angle+np.pi)%(2*np.pi)-np.pi;angle=ready_angle+weight*delta
            gain=weight*following.get('velocity',1);lift=5*np.sqrt(gain)*np.sin(np.pi*weight)
        elif previous and time-previous['time']<.25:
            weight=smoothstep((time-previous['time'])/.25);start,a=target(previous)
            wrist=start*(1-weight)+ready*weight
            delta=(ready_angle-a+np.pi)%(2*np.pi)-np.pi;angle=a+weight*delta
            gain=(1-weight)*previous.get('velocity',1);lift=8*np.sqrt(gain)*np.sin(np.pi*weight)
        wrist[1]-=lift;tip=wrist+55*np.array((np.cos(angle),np.sin(angle)))
        # Reach is validated; contacts are never silently clamped to a fake drum.
        shoulder=self.roots[side];upper,lower=self.lengths[side]
        elbow=elbow_2d(shoulder,wrist,upper,lower,-1 if side=='left' else 1)
        self.last_joints[side]=dict(shoulder=shoulder.copy(),elbow=elbow,wrist=wrist.copy(),tip=tip.copy(),gain=gain)
        return shoulder,elbow,wrist,tip,gain

    def frame(self,time,active=(),cymbal_levels=None):
        # Surface lighting never holds an arm aloft during cymbal decay.
        masked=dict(self.masks)
        for target in TARGETS:
            masked[target]=masked[target_surface_key(target)]
            from tools.drummer_v3_visual_masks import target_actuator_key,target_variant_key
            masked[target_actuator_key(target)]=Image.new('L',self.source.size,0)
            key=target_variant_key(target,'right');masked[key]=masked[target_surface_key(target)]
            masked[target_actuator_key(key)]=Image.new('L',self.source.size,0)
        lit=compose_emissive(self.source,masked,active,idle_brightness=self.lighting.idle_instrument,
            active_brightness=self.lighting.strike,idle_overlay_mask=self.body_mask,idle_overlay_brightness=self.lighting.idle_body,
            cymbal_levels=cymbal_levels)
        for side in ('left','right'):
            shoulder,elbow,wrist,tip,gain=self._pose(side,time)
            brightness=self.lighting.idle_arm+(self.lighting.strike-self.lighting.idle_arm)*gain
            arm=Image.new('RGBA',self.source.size,(0,0,0,0));d=ImageDraw.Draw(arm)
            # Thin connected neutral wire sleeves retain the snowman's art style.
            points=[tuple(shoulder),tuple(elbow),tuple(wrist)]
            color=tuple(min(255,round(v*min(brightness,1.35))) for v in (148,155,155))+(255,)
            d.line(points,fill=color,width=5,joint='curve')
            for p in (shoulder,elbow,wrist):d.ellipse((p[0]-2.5,p[1]-2.5,p[0]+2.5,p[1]+2.5),fill=color)
            highlight=tuple(min(255,round(v*brightness)) for v in (195,200,198))+(255,)
            d.line([(x,y-1) for x,y in points],fill=highlight,width=1)
            # Repose original gold shaft pixels; no neon replacement stick.
            transform=dict(source_grip=self.shaft_spec['source_grip'],source_tip=self.shaft_spec['source_tip'],
                           grip=(wrist/self.scale).tolist(),contact=(tip/self.scale).tolist())
            shaft=self.shaft.transform(self.source.size,Image.Transform.AFFINE,strike_transform(transform,self.source.size),Image.Resampling.BICUBIC)
            alpha=shaft.getchannel('A');shaft=ImageEnhance.Brightness(shaft).enhance(brightness);shaft.putalpha(alpha)
            arm=Image.alpha_composite(arm,shaft);lit=Image.alpha_composite(lit.convert('RGBA'),arm)
        return lit
