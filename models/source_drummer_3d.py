"""Closed dimensional V3 components with the unchanged canonical front view.

Source XY and materials come from drummerbg.png and its authored masks. Depth
extends behind that face; no kit is mirrored, rearranged or replaced. The same
source-clock articulated skeleton drives the 3D arms and the 2D compositor.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import hashlib

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
import trimesh

from models.band_performance_scene import matrix, line_matrix
from tools.drummer_v3_visual_masks import load_spec, exact_geometry, idle_art_key
from tools.render_drummer_v3_preview import SOURCE, TARGETS

CROP = (99, 124, 494, 380)
SOURCE_SHA256 = '643e1bfb7fb0b245cb7400010a80f9f75037f8a5554adde7bde8cba7a53374fa'


def closed_component(mask, image, depth, *, stride=2):
    """Close an occupied source-cell surface, including its back and side walls.

    All front vertices stay at z=0. The rear has rounded depth, so an
    orthographic front projection is identical for both dimensional variants.
    Native cell positions and source colors remain deterministic.
    """
    mask=np.asarray(mask,dtype=bool); image=np.asarray(image,dtype=np.uint8)
    if mask.shape!=image.shape[:2] or not np.isfinite(depth) or depth<=0:
        raise ValueError('Matching source mask/image and positive depth required')
    height,width=mask.shape
    xs=np.arange(0,width+stride,stride).clip(max=width)
    ys=np.arange(0,height+stride,stride).clip(max=height)
    xs=np.unique(xs);ys=np.unique(ys)
    cx=((xs[:-1]+xs[1:])/2).astype(int).clip(max=width-1)
    cy=((ys[:-1]+ys[1:])/2).astype(int).clip(max=height-1)
    cells=np.argwhere(mask[np.ix_(cy,cx)])
    if not len(cells):raise ValueError('Empty canonical component')
    occupied={tuple(v) for v in cells};lookup={};corner_list=[];quads=[]
    for y,x in cells:
        quad=[]
        for dy,dx in ((0,0),(0,1),(1,1),(1,0)):
            gy,gx=y+dy,x+dx
            incident=[(gy-1,gx-1),(gy-1,gx),(gy,gx-1),(gy,gx)]
            present=[p for p in incident if p in occupied]
            diagonal=(len(present)==2 and present[0][0]!=present[1][0] and present[0][1]!=present[1][1])
            key=(gy,gx,(y,x) if diagonal else None)
            if key not in lookup:lookup[key]=len(corner_list);corner_list.append((gy,gx))
            quad.append(lookup[key])
        quads.append(quad)
    corners=np.asarray(corner_list)
    xy=np.c_[xs[corners[:,1]],ys[corners[:,0]]].astype(float)
    # Positive, gently rounded construction depth, entirely behind source XY.
    center=xy.mean(0);span=np.maximum(np.ptp(xy,axis=0)/2,1)
    radial=np.clip(np.sum(((xy-center)/span)**2,axis=1),0,1)
    rear=-depth*(.72+.28*np.sqrt(1-radial))
    vertices=np.vstack((np.c_[xy,np.zeros(len(xy))],np.c_[xy,rear]))
    n=len(xy); faces=[];edges={}
    for q in quads:
        faces.extend(((q[0],q[2],q[1]),(q[0],q[3],q[2]),
                      (q[0]+n,q[1]+n,q[2]+n),(q[0]+n,q[2]+n,q[3]+n)))
        for a,b in zip(q,q[1:]+q[:1]):
            key=tuple(sorted((a,b)))
            if key in edges:del edges[key]
            else:edges[key]=(a,b)
    for a,b in edges.values():faces.extend(((a,b,a+n),(b,b+n,a+n)))
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    # Source-image Y points down. Scene Y points up; reverse winding once.
    mesh.vertices[:,1]=height-mesh.vertices[:,1]
    if mesh.volume<0:mesh.invert()
    sampled=image[xy[:,1].astype(int).clip(max=height-1),xy[:,0].astype(int).clip(max=width-1),:3]
    colors=np.vstack((sampled,np.maximum(sampled*.35,5))).astype('u1')
    mesh.visual.vertex_colors=np.c_[colors,np.full(len(colors),255,dtype='u1')]
    return mesh


@lru_cache(maxsize=1)
def source_components():
    with SOURCE.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=SOURCE_SHA256:
            raise ValueError('Canonical drummer source changed')
    source=Image.open(SOURCE).convert('RGBA'); spec=load_spec()
    geometry=exact_geometry(source,spec)
    idle=geometry['masks'][idle_art_key()].convert('RGB')
    rgb=np.asarray(idle.crop(CROP)); components=[]
    occupied=np.zeros(rgb.shape[:2],dtype=bool)
    for slot,target in enumerate(TARGETS):
        zone=next(z for z in spec['zones'] if z['id']==spec['lighting_targets'][slot]['surface'])
        from tools.drummer_v3_visual_masks import build_zone_mask
        mask=np.asarray(build_zone_mask(source.size,zone).crop(CROP))>0
        occupied|=mask
        depth=60 if slot==0 else 30 if slot in (1,3,4,5) else 12
        components.append(dict(name=target,slot=5+slot,mesh=closed_component(mask,rgb,depth)))
    # The source body silhouette is independent of the kit, not a new snowman.
    body=Image.new('L',source.size);draw=ImageDraw.Draw(body)
    draw.polygon([(264,124),(342,124),(344,164),(339,171),(340,204),
                  (334,213),(341,251),(339,269),(262,277),(256,245),
                  (263,214),(259,202),(260,171)],fill=255)
    mask=(np.asarray(body.crop(CROP))>0)&~occupied
    components.append(dict(name='V3_BODY',slot=-1,mesh=closed_component(mask,rgb,42)))
    hsv=np.asarray(idle.crop(CROP).convert('HSV'))
    support=(hsv[:,:,1]>70)&(hsv[:,:,2]>25)&~occupied&~(np.asarray(body.crop(CROP))>0)
    # The original foot gets a dynamic dimensional pedal below.
    support[220:252,275:332]=False
    support=binary_dilation(support,iterations=1)
    components.append(dict(name='V3_SUPPORTS',slot=-1,mesh=closed_component(support,rgb,7)))
    return tuple(components)


class SourceDrummer3D:
    def __init__(self,scene,hits=(),*,width=4.5,center=(0,2.26,-1.4)):
        from animation.articulated_source_drummer import ArticulatedDrummer
        self.scene=scene;self.width=width;self.scale=width/(CROP[2]-CROP[0])
        self.center=np.asarray(center,float);self.player=ArticulatedDrummer(hits,natural_arms=True,cache_lighting=True)
        self.meshes=[]
        for part in source_components():
            mesh=part['mesh'].copy();mesh.vertices*=self.scale
            mesh.vertices+=self.center+(-width/2,-(CROP[3]-CROP[1])*self.scale/2,0)
            self.meshes.append(dict(name=part['name'],mesh=mesh,slot=part['slot']))
        self.connector_ids=[]
        # These are the same short torso-to-shoulder bridges drawn by the
        # source compositor after moving its fixed shoulder roots outward.
        for side,points in [('left',[(.453,.432),(.440,.440),(.425,.445)]),
                            ('right',[(.570,.434),(.588,.443),(.603,.452)])]:
            for a,b in zip(points[:-1],points[1:]):
                self.connector_ids.append(len(scene.instances))
                scene.rod('V3_'+side+'_shoulder_attachment',self.point(np.asarray(a)*self.player.scale),
                          self.point(np.asarray(b)*self.player.scale),.031,'#A8B0AE')
        self.rigs={}
        for side in ('left','right'):
            first=len(scene.instances)
            scene.rod('V3_'+side+'_upper',(0,0,0),(0,1,0),.057,'#BDCBCD')
            scene.rod('V3_'+side+'_forearm',(0,0,0),(0,1,0),.045,'#BDCBCD')
            scene.sphere('V3_'+side+'_grip',(0,0,0),(.057,.046,.055),'#9DB2BC')
            scene.rod('V3_'+side+'_stick',(0,0,0),(0,1,0),.016,'#C69B52')
            self.rigs[side]=tuple(range(first,first+4))
        self.foot=len(scene.instances)
        scene.sphere('V3_HIHAT_FOOT',(0,0,0),(.16,.055,.09),'#96642C')
        self.pedal=len(scene.instances)
        scene.rod('V3_HIHAT_PEDAL',(0,0,0),(0,1,0),.025,'#94ACBB')
        self.beater=len(scene.instances)
        scene.rod('V3_KICK_BEATER',(0,0,0),(0,1,0),.022,'#A8B6BC')
        self.pose(0)

    def point(self,pixel,z=.025):
        pixel=np.asarray(pixel)
        return self.center+((pixel[0]-(CROP[0]+CROP[2])/2)*self.scale,
                            ((CROP[1]+CROP[3])/2-pixel[1])*self.scale,z)

    def pose(self,time):
        for side,ids in self.rigs.items():
            shoulder,elbow,wrist,tip,gain=self.player._pose(side,time)
            a,b,c,d=ids;s,e,w,t=[self.point(p) for p in (shoulder,elbow,wrist,tip)]
            for index,p,q,radius in ((a,s,e,.057),(b,e,w,.045),(d,w,t,.016)):
                self.scene.instances[index]['matrix']=line_matrix(p,q,radius)
            self.scene.instances[c]['matrix']=matrix(w,(.057,.046,.055))
        hat=any(0<=time-h['time']<.11 for h in self.player.foot_hits)
        heel=self.point(np.array((.638,.710))*self.player.scale)
        toe=self.point(np.array((.697,.735))*self.player.scale)+(0,0 if hat else .06,0)
        self.scene.instances[self.foot]['matrix']=matrix((heel+toe)/2,(.16,.055,.09))
        self.scene.instances[self.pedal]['matrix']=line_matrix(heel-(0,.025,0),toe-(0,.025,0),.025)
        kick=any(0<=time-h['time']<.10 for h in self.player.kick_hits)
        root=self.point((290,368),-.04)
        tip=self.point((290,337),-.02 if kick else -.30)
        self.scene.instances[self.beater]['matrix']=line_matrix(root,tip,.022)

    def proof(self):
        return dict(source_sha256=SOURCE_SHA256,projection='same source XY / orthographic front',
                    source_crop=CROP,closed_components=[dict(name=p['name'],watertight=bool(p['mesh'].is_watertight),
                        depth=float(np.ptp(p['mesh'].vertices[:,2])),vertices=len(p['mesh'].vertices)) for p in self.meshes],
                    source_clock_skeleton=True,planar_billboard=False,detector_or_mapping_changed=False)
