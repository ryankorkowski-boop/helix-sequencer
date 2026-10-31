"""Connected source-art drummer with time-dependent anticipation/contact/recovery.

The original body, surfaces and shaft pixels are retained. Articulated sleeve
contours use neutral wire colors consistent with the original arm artwork. This is an opt-in
Helix compositor; the approved v7 compositor remains the comparison baseline.
"""
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
import os
import numpy as np
from PIL import Image,ImageDraw,ImageEnhance,ImageChops
from models.band_motion_refinement import elbow_2d,smoothstep,EventLane
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
    def __init__(self, hits, lighting=BandLighting(), natural_arms=False, cache_lighting=None):
        self.natural_arms=natural_arms
        # Opt-in review acceleration. Cached pixels never include moving arms;
        # static source artwork/masks must remain unchanged while enabled.
        self.cache_lighting=(os.environ.get('HELIX_CACHE_STATIC_KIT')=='1') if cache_lighting is None else bool(cache_lighting)
        self._kit_cache={}
        self.source=Image.open(SOURCE).convert('RGBA');self.spec=load_spec();self.lighting=lighting
        self.geometry=exact_geometry(self.source,self.spec);self.masks=self.geometry['masks']
        self.scale=np.array(self.source.size)-1
        self.zones={z['id']:z for z in self.spec['zones']};self.hits=sorted(hits,key=lambda e:e['time'])
        self.last_joints={};self.motion_rejections=[];self.hand_reassignments=[]
        self.motion_adjustments={}
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
        # One fixed skeleton throughout anticipation, contact and recovery.
        self.lengths={'left':(39.,39.),'right':(30.,55.) if natural_arms else (39.,39.)}
        self.targets={}
        for item in self.spec['lighting_targets']:
            name='HX_SNOWMAN_DRUMMER_V3_'+item['id']
            acts=[self.zones[a] for a in item['actuators'] if self.zones[a].get('strike')]
            for zone in acts:
                strike=zone['strike'];side=strike['striking_arm']
                self.targets[name,side]=(np.asarray(strike['contact'])*self.scale,np.asarray(strike['grip'])*self.scale)
        self.targets[TARGETS[1],'right']=(np.asarray(self.zones['SNARE_RIGHT_ARM_STICK']['strike']['contact'])*self.scale,
            np.asarray(self.zones['SNARE_RIGHT_ARM_STICK']['strike']['grip'])*self.scale)
        # HI-HAT IS FOOT ONLY. Preserve the authentic HI_HAT source cues,
        # but do not route any of them to a stick/arm target.
        # Foot compression and hi-hat closure share the same time gate.
        self.hi_hat_target=TARGETS[2]
        self.foot_hits=[h for h in self.hits if h['target']==self.hi_hat_target]
        self.foot_lanes=EventLane(self.foot_hits)
        self.foot_contact_window=.11
        # Preserve the authored foot pixels, inside the visible source crop.
        self.foot_mask=build_zone_mask(self.source.size,self.zones['HI_HAT_FOOT'])
        self.foot_art=self.source.copy()
        self.foot_art.putalpha(refine_actuator_to_source_art(self.source,self.foot_mask))
        self.kick_hits=[h for h in self.hits if h['target']==TARGETS[0]]
        # Resolve physically impossible same-hand travel without deleting a
        # polyphonic detector event or inventing a different drum identity.
        requested=[h for h in self.hits if h['target'] not in (self.hi_hat_target,TARGETS[0])]
        self.hits=[];last={}
        for event in requested:
            preferred=event['side'];choices=[preferred]
            if event['target']==TARGETS[1]:choices.append('right' if preferred=='left' else 'left')
            selected=None
            for side in choices:
                if (event['target'],side) not in self.targets:continue
                tip,grip=self.targets[event['target'],side]
                direction=(tip-grip)/np.linalg.norm(tip-grip);wrist=tip-direction*55
                distance=np.linalg.norm(wrist-self.roots[side])
                upper,lower=self.lengths[side]
                if not abs(upper-lower)+1e-5<distance<upper+lower-1e-5:continue
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
        self.lanes={side:EventLane(e for e in self.hits if e['side']==side and (e['target'],side) in self.targets) for side in ('left','right')}
        self.body_mask=Image.new('L',self.source.size,0)
        ImageDraw.Draw(self.body_mask).polygon([(int(x*self.scale[0]),int(y*self.scale[1])) for x,y in
            [( .36,.25),(.66,.25),(.66,.47),(.60,.55),(.41,.55),(.34,.46)]],fill=255)
        for target in TARGETS:self.body_mask=ImageChops.subtract(self.body_mask,self.masks[target_surface_key(target)])

    def _pose(self,side,time):
        previous,following=self.lanes[side].neighbors(time)
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
        if self.natural_arms:
            # Wrist-led rebound: lift the shaft as well as the forearm. The
            # offset is zero at a strike, preserving the exact drum contact.
            angle+=(-1 if side=='left' else 1)*.055*lift
            tip=wrist+55*np.array((np.cos(angle),np.sin(angle)))
        shoulder=self.roots[side];upper,lower=self.lengths[side]
        # Rebound can leave the reachable annulus even when both contacts
        # are valid. Constrain only the transit wrist, never a source contact.
        delta=wrist-shoulder;distance=float(np.linalg.norm(delta))
        lo=abs(upper-lower)+1e-4;hi=upper+lower-1e-4
        if not lo<=distance<=hi:
            at_contact=previous is not None and abs(time-previous['time'])<1e-8
            if at_contact:
                raise ValueError('Invalid scheduled drum contact')
            direction=delta/max(distance,1e-12)
            if distance<1e-12:
                direction=(ready-shoulder)/np.linalg.norm(ready-shoulder)
            wrist=shoulder+direction*np.clip(distance,lo,hi)
            tip=wrist+55*np.array((np.cos(angle),np.sin(angle)))
            self.motion_adjustments[side,round(time,6)]='transit_reach_constraint'
        bend=-1 if side=='left' or (side=='right' and self.natural_arms) else 1
        elbow=elbow_2d(shoulder,wrist,upper,lower,bend)
        self.last_joints[side]=dict(shoulder=shoulder.copy(),elbow=elbow,wrist=wrist.copy(),tip=tip.copy(),gain=gain)
        return shoulder,elbow,wrist,tip,gain

    def frame(self,time,active=(),cymbal_levels=None):
        # Surface lighting never holds an arm aloft during cymbal decay.
        active=tuple(sorted(set(active)))
        cache_key=(active,None if cymbal_levels is None else tuple(sorted(cymbal_levels.items())),
                   self.lighting.idle_instrument,self.lighting.strike,self.lighting.idle_body)
        cached=self._kit_cache.get(cache_key) if self.cache_lighting else None
        if cached is not None:
            lit=cached.copy()
        else:
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
            if self.cache_lighting:
                if len(self._kit_cache)>=24:self._kit_cache.pop(next(iter(self._kit_cache)))
                self._kit_cache[cache_key]=lit.copy()
        # Foot artwork and physical pedal share a continuous source-clock pose.
        # The old overlay was at y=.855, below the authored visible crop (.755).
        previous,following=self.foot_lanes.neighbors(time)
        age=time-previous['time'] if previous is not None else float('inf')
        down=float(1-smoothstep(np.clip((age-.025)/.085,0,1))) if 0<=age<.11 else 0.
        # Lift toward the next source strike, never fabricate an extra onset.
        heel=np.array((.638,.710))*self.scale
        toe=np.array((.697,.735))*self.scale
        angle=8.*(1-down)
        foot=self.foot_art.rotate(angle,resample=Image.Resampling.BICUBIC,center=tuple(heel))
        # Erase the stationary copy before placing the moving original pixels.
        lit=Image.composite(Image.new('RGBA',self.source.size,(0,0,0,255)),lit,self.foot_mask)
        pedal=Image.new('RGBA',self.source.size,(0,0,0,0));brush=ImageDraw.Draw(pedal)
        pedal_y=float(toe[1]-4*(1-down))
        brush.line([tuple(heel+(0,9)),(float(toe[0]+3),pedal_y+5)],fill=(148,172,187,255),width=3)
        lit=Image.alpha_composite(lit.convert('RGBA'),pedal)
        lit=Image.alpha_composite(lit,foot)
        self.last_hi_hat_foot_down=bool(0<=age<self.foot_contact_window)
        self.last_hi_hat_pedal_pose=dict(depression=down,heel=heel.tolist(),toe=[float(toe[0]),pedal_y],source_time=None if previous is None else previous['time'])
        for side in ('left','right'):
            shoulder,elbow,wrist,tip,gain=self._pose(side,time)
            brightness=self.lighting.idle_arm+(self.lighting.strike-self.lighting.idle_arm)*gain
            arm=Image.new('RGBA',self.source.size,(0,0,0,0));d=ImageDraw.Draw(arm)
            # Thin connected neutral wire sleeves retain the snowman's art style.
            points=[tuple(shoulder),tuple(elbow),tuple(wrist)]
            color=tuple(min(255,round(v*min(brightness,1.35))) for v in (148,155,155))+(255,)
            if self.natural_arms:
                # Rounded, tapered snow sleeves with shaded volume and a
                # distinct grip replace the old uniform wire skeleton.
                sleeve=tuple(min(255,round(v*(.70+.30*gain))) for v in (190,205,209))+(255,)
                shadow=(65,82,90,255)
                for a,b,width in ((shoulder,elbow,10),(elbow,wrist,8)):
                    d.line([tuple(a),tuple(b)],fill=shadow,width=width+3)
                    d.line([tuple(a),tuple(b)],fill=sleeve,width=width)
                    for p in (a,b):
                        r=width/2;d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=sleeve)
                d.line([tuple(shoulder+(0,-2)),tuple(elbow+(0,-2)),tuple(wrist+(0,-2))],fill=(227,236,231,255),width=2)
                direction=(tip-wrist)/55
                d.line([tuple(wrist-direction*9),tuple(tip)],fill=(198,155,82,255),width=3)
            else:
                d.line(points,fill=color,width=5,joint='curve')
                for p in (shoulder,elbow,wrist):d.ellipse((p[0]-2.5,p[1]-2.5,p[0]+2.5,p[1]+2.5),fill=color)
                highlight=tuple(min(255,round(v*brightness)) for v in (195,200,198))+(255,)
                d.line([(x,y-1) for x,y in points],fill=highlight,width=1)
            # Repose original gold shaft pixels; no neon replacement stick.
            transform=dict(source_grip=self.shaft_spec['source_grip'],source_tip=self.shaft_spec['source_tip'],
                           grip=(wrist/self.scale).tolist(),contact=(tip/self.scale).tolist())
            shaft=self.shaft.transform(self.source.size,Image.Transform.AFFINE,strike_transform(transform,self.source.size),Image.Resampling.BICUBIC)
            alpha=shaft.getchannel('A');shaft=ImageEnhance.Brightness(shaft).enhance(brightness);shaft.putalpha(alpha)
            arm=Image.alpha_composite(arm,shaft)
            if self.natural_arms:
                # The hand wraps around the shaft; it must be drawn in front.
                d=ImageDraw.Draw(arm);d.ellipse((wrist[0]-5,wrist[1]-4,wrist[0]+5,wrist[1]+4),fill=(157,178,188,255))
                d.arc((wrist[0]-4,wrist[1]-3,wrist[0]+4,wrist[1]+3),20,150,fill=(233,236,225,255),width=2)
            lit=Image.alpha_composite(lit.convert('RGBA'),arm)
        return lit

