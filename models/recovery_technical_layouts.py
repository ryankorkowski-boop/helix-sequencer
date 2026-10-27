"""Explicit depth, lattice and architectural structures for native review.

Dimensions are proposed design feet, not verified fabrication instructions.
Nothing here claims stationary lights physically rotate or move.
"""
import math
import numpy as np


def enrich(g,number):
    from models.approval_layouts import structures,house,tree
    if number==9:
        for side in (-1,1):
            g.dna('CATHEDRAL_SIDE_HELIX_'+str(side),side*31,-17,52,7,3.5,600,'CATHEDRAL')
            g.models[-1].details.update(musical_role='guitarist' if side<0 else 'bassist',
                spatial_direction=side,spatial_phase=.25 if side<0 else .75)
            for z in (-35,-15,5,25):
                m=g.poly('CATHEDRAL_RIB_'+str(side)+'_'+str(z),
                    [(side*45,0,z),(side*45,36,z),(side*27,54,z),(0,65,z)],180,
                    'CATHEDRAL','Depth-separated nave rib',g.palette[1])
                m.details.update(musical_role='drummer',percussion_component='kick' if side<0 else 'snare',
                                 propagation_delay_ms=int((25-z)*3))
        for y in (8,24,40):
            m=structures(g).ring('CATHEDRAL_ORBIT',(0,y,-10),17,17,'DNA',plane='xz',count=220)
            m.details.update(musical_role='keyboardist',spatial_phase=y/64)
    if number==10:
        # The original five optical planes all followed keys, and all five
        # rings followed the sparse backing voice. Give the existing shapes
        # distinct instrumental ownership without adding notes or geometry.
        planes=[m for m in g.models if 'MOIRE_LAYER' in m.name]
        for m,role,component in zip(planes,('keyboardist','drummer','bassist','drummer','guitarist'),
                                     (None,'kick',None,'snare',None)):
            m.details['musical_role']=role
            if component:m.details['percussion_component']=component
        rings=[m for m in g.models if 'SPIRAL_WAVE' in m.name]
        for m,role,component in zip(rings,('bassist','guitarist','keyboardist','drummer','drummer'),
                                    (None,None,None,'hihat','cymbal')):
            m.details['musical_role']=role
            if component:m.details['percussion_component']=component
        # Slightly different line frequencies and angles produce a visible
        # geometric beat pattern when the camera projects the stacked planes.
        for layer,(spacing,angle,z) in enumerate(((5.2,-3,-1),(5.6,3,2),(6.0,-1,5))):
            points=[];subs={}
            for line,y in enumerate(np.arange(0,53,spacing)):
                q=np.c_[np.linspace(-42,42,240),np.full(240,y),np.zeros(240)]
                t=math.radians(angle);x=q[:,0].copy()
                q[:,0]=x*math.cos(t)-(q[:,1]-26)*math.sin(t)
                q[:,1]=26+x*math.sin(t)+(q[:,1]-26)*math.cos(t)
                q[:,2]=z
                subs[f'ROW_{line:02}']=list(range(len(points)+1,len(points)+len(q)+1));points.extend(q)
            m=g.custom('MOIRE_LINE_LATTICE_'+str(layer),points,'OPTICAL',
                'Superposed line lattice; distinct angular/spatial frequency',
                [g.palette[layer]]*len(points),subs,details=dict(
                    musical_role=('keyboardist','bassist','harmony')[layer],
                    spatial_phase=layer/3,spatial_direction=1 if layer%2==0 else -1,
                    line_spacing_ft=spacing,angle_degrees=angle,depth_plane_ft=z,
                    optical_interaction='projected superposition; rendered verification required'))
            m.attrs['PixelSize']='3'
        for side in (-1,1):
            for ring in range(7):
                m=structures(g).ring('MOIRE_RADIAL_LATTICE',(side*20,26,8+ring*.35),
                    9+ring*1.6,9+ring*1.6,'SPIRALS',plane='xy',count=240,tilt=side*3)
                m.details.update(musical_role='guitarist' if side<0 else 'lead',
                                 spatial_phase=ring/7,spatial_direction=side)
    if number==11:
        for depth in range(8):
            scale=1-.075*depth;z=36-depth*17;w=90*scale;h=54*scale
            m=g.poly('PERSPECTIVE_BOX_'+str(depth),
                [(-w/2,0,z),(-w/2,h,z),(w/2,h,z),(w/2,0,z),(-w/2,0,z)],480,
                'DEPTH','Nested camera-facing depth portal',g.palette[depth%3])
            for sector,nodes in enumerate(np.array_split(np.arange(1,len(m.points)+1),8)):
                m.submodels[f'SECTOR_{sector:02}']=nodes.tolist()
            role=('drummer','keyboardist','drummer','bassist','guitarist','drummer','keyboardist','bassist')[depth]
            m.details.update(musical_role=role,propagation_delay_ms=depth*50,
                spatial_direction=1,spatial_phase=depth/16,depth_index=depth)
            if role=='drummer':m.details['percussion_component']={0:'kick',2:'snare',5:'hihat'}[depth]
        for side in (-1,1):
            for level in (0,20,40):
                m=g.poly('PERSPECTIVE_RAIL_'+str(side)+'_'+str(level),
                    [(side*45,level,36),(side*21,level*.475,-83)],280,
                    'DEPTH','Converging perspective rail',g.palette[0])
                m.details.update(musical_role='keyboardist')
    if number==12:
        for side in (-1,1):
            g.dna('ULTIMATE_TWIN_HELIX_'+str(side),side*82,-24,85,16,4.0,900,'DNA')
            g.models[-1].details.update(musical_role='keyboardist' if side<0 else 'bassist',spatial_direction=side)
            for x in (side*48,side*116):tree(g,x,-55,58,14)
        for layer in range(4):
            m=structures(g).mesh('ULTIMATE_ABSTRACT_SURFACE',(-25+layer*16,2,-58+layer*12),
                48,54,'MATRICES',layer%3,wave=5,yaw=-18+layer*12)
            m.details.update(musical_role=('keyboardist','guitarist','bassist','harmony')[layer],
                             spatial_phase=layer/4,spatial_direction=1 if layer%2 else -1)
    return g
