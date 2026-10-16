"""Finite native 3D worlds: note ladders, spiral groves and optical structures."""
from __future__ import annotations
import numpy as np
from models.showcase_flavors import build_flavor
from models.approved_concepts import Structures
from models.native_review_band import add_band, allocate

WORLDS = ('celestial_orrery','enchanted_grove','neon_circuit')
TITLES = ('Moiré Observatory','Spiral Village','Prismatic Fold')


def build_world(variant):
    g=build_flavor(WORLDS[variant]);g.title='Helix '+TITLES[variant];g.slug='Helix_3D_'+str(variant+1)
    s=Structures(g)
    # Exactly 88 independently addressable complete rungs, ordered A0..C8.
    g.dna('HX_MIDI_DOUBLE_HELIX',0,-7,96,11,8.8,528,'MIDI_CATHEDRAL')
    hero=g.models[-1];rungs=hero.submodels['RUNGS'];heights=hero.points[np.array(rungs)-1,1]
    unique=np.unique(np.round(heights,5))
    if len(unique)!=88:raise ValueError('Expected one complete rung per MIDI key')
    for pitch,h in zip(range(21,109),unique):
        hero.submodels[f'KEY_MIDI_{pitch:03d}']=[node for node,y in zip(rungs,heights) if abs(y-h)<1e-4]
    hero.details.update(midi_rungs=True,midi_range=[21,108],rung_count=88,
        note_source='absolute source MIDI or estimated keyboard NoteEvents; no modulo mapping')
    # Three spatially separated groves trace spirals rather than a regular grid.
    for group,(cx,cz) in enumerate(((-112,28),(100,21),(0,-110))):
        for k in range(8):
            a=k*2.399963+variant*.32;r=9+3.2*k
            tree=s.tree(cx+r*np.cos(a),cz+r*np.sin(a),18+k*2.1,5+k*.35,color=group)
            tree.zone=f'SPIRAL_GROVE_{group+1}';tree.details.update(grove=group+1,spiral_tree=True)
    # Separated depth planes, with spatially shifted density: interference is
    # actual XYZ structure and channel motion, never a postproduction shader.
    for plane in range(2):
        points=[];subs={}
        for j in range(23):
            y=np.linspace(9,55,36);x=-85+(j-11)*1.25+(y-30)*(.14 if plane else -.14)
            ids=list(range(len(points)+1,len(points)+len(y)+1));points.extend(np.c_[x,y,np.full(len(y),-36-plane*7)])
            subs[f'BAND_{j:02d}']=ids
        s.add('MOIRE_PLANE_'+str(plane),points,'MOIRE',plane,subs,dict(moire=True,plane=plane))
    # Successive frames diminish toward an off-axis vanishing point. Their
    # twist and depth are real; the review camera can move across the illusion.
    for k in range(9):
        z=-78+k*6;scale=1-.055*k;a=k*.12*(1 if variant%2 else -1)
        corners=np.array([[-19,-16],[19,-16],[19,16],[-19,16],[-19,-16]])*scale
        rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
        q=corners@rot.T
        m=s.path('PERSPECTIVE_PORTAL',np.c_[q[:4,0]+83,q[:4,1]+42,np.full(4,z)],'PERSPECTIVE',k%3,110,closed=True)
        m.details['forced_perspective']=True
    # A toroidal DNA crown and cross-axis infinity path retain earlier motifs.
    g.dna('HX_TOROIDAL_DNA',0,-70,0,26,5,240,'TOROIDAL_CROWN',y=67,ring=True)
    t=np.linspace(0,2*np.pi,220,endpoint=False)
    s.add('INFINITY_RIBBON',np.c_[55*np.sin(t),7*np.sin(2*t)+15,22*np.cos(t)+45],
        'BASS_PROMENADE',2,details=dict(infinity_ribbon=True))
    for side in (-1,1):
        x=side*145;z=75;w=21;h=15
        s.path('VILLAGE_HOUSE',[(x-w,0,z),(x-w,h,z),(x,h+12,z-10),(x+w,h,z),(x+w,0,z)],'VILLAGE',1,130,closed=True)
        s.path('HOUSE_ROOF_DEPTH',[(x-w,h,z),(x-w,h,z-22),(x,h+12,z-32),(x+w,h,z-22),(x+w,h,z)],'VILLAGE',2,110)
    add_band(g,position=(0,0,90))
    allocate(g)
    return g
