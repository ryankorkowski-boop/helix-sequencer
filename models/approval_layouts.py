"""Twelve physically distinct native layouts for a shared source-timed review."""
import math
import numpy as np
from models.ultimate_showcase import Garden, build_ultimate_garden
from models.approved_concepts import Structures
from models.showcase_flavors import _move

def structures(g):
    s=Structures(g)
    s.serial=len(g.models)
    return s


NAMES = ('LOR_16_AC','LOR_64_AC','LOR_128_256_AC','Starter_RGB_Pixels',
         'Traditional_Christmas','Modern_Pixel_House','Snowman_Band_Stage',
         'Band_and_House','Double_Helix_Cathedral','Moire_Optical_Illusion',
         'Forced_Perspective','Ultimate_Helix_Showcase')


def house(g, x=0, z=0, scale=1, prefix='HOME'):
    def p(name,vertices,color=0):
        return g.poly(prefix+'_'+name,np.asarray(vertices)*scale+(x,0,z),100,'HOUSE',name,g.palette[color])
    p('EAVE',[(-30,22,0),(30,22,0)])
    p('ROOF',[(-33,22,0),(0,40,-3),(33,22,0)],2)
    p('RIDGE',[(0,40,-3),(0,40,-18)],2)
    for side in (-1,1):
        p('WINDOW_'+str(side),[(side*16-5,8,1),(side*16-5,17,1),(side*16+5,17,1),(side*16+5,8,1),(side*16-5,8,1)],1)
    p('DOOR',[(-4,0,1),(-4,13,1),(4,13,1),(4,0,1)])


def arch(g,x,z,width=12,height=8):
    structures(g).arch((x,0,z),width,height)


def cane(g,x,z,h=10):
    t=np.linspace(0,math.pi,25)
    points=np.vstack((np.c_[np.full(35,x),np.linspace(0,h,35),np.full(35,z)],
                      np.c_[x+h*.2-h*.2*np.cos(t),h+h*.2*np.sin(t),np.full(25,z)])[1:])
    return g.custom(f'CANE_{len(g.models):03}',points,'CANES','Candy cane',
                    [g.palette[1]]*len(points),{'ALL':list(range(1,len(points)+1))})


def tree(g,x,z,h=18,r=5):
    g.tree(f'TREE_{len(g.models):03}',x,z,h,r,0,12,24,'TREES')


def faces(g):
    from models.snowman_ensemble import face
    for side in (-1,1):
        m=face(g,'tree' if side<0 else 'bulb',0,g.palette[int(side>0)])
        _move(m,(0,0,0),(side*37,0,22),.35)
        m.name='GENERIC_FACE_'+str(side)
        m.details['generic_singer']= 'estimated_lead' if side<0 else 'estimated_backing'


def helix(g):
    # Reuse the native DNA generator, with one literal rung per MIDI note.
    g.dna('HX_CENTER_KEYBOARD_HELIX',0,-10,65,10,8.8,880,'DNA')
    m=g.models[-1]
    heights=sorted({round(m.points[n-1,1],6) for n in m.submodels['RUNGS']})
    if len(heights)!=88:
        raise ValueError('Expected88 literal helix rungs')
    for pitch,y in zip(range(21,109),heights):
        m.submodels[f'KEY_MIDI_{pitch:03d}']=[n for n in m.submodels['RUNGS'] if abs(m.points[n-1,1]-y)<1e-5]
    m.details['rung_animation']='Independent source guitar/bass strand envelopes; no geometric rotation claimed'


def ac_circuits(g, factor):
    # Each prop is one circuit in16; contiguous separately wired sections
    # become4 or16 circuits in64/256. Multiple bulbs share each real channel.
    for i,m in enumerate(g.models):
        _, indexes=np.unique(np.round(m.points,6),axis=0,return_index=True)
        indexes.sort()
        temp=Garden();q=temp.custom(m.name,m.points[indexes],m.zone,m.design,[m.colors[j] for j in indexes],{})
        entries=q.attrs['CustomModelCompressed'].split(';')
        assigned=np.minimum(factor-1,np.arange(len(entries))*factor//len(entries))+1
        q.attrs['CustomModelCompressed']=';'.join(','.join([str(c)]+e.split(',')[1:]) for e,c in zip(entries,assigned))
        q.kind='ac';q.details.update(circuit_count=factor,point_circuits=assigned.tolist(),physical_wiring_verified=False)
        q.attrs['StringType']=('Single Color Red','Single Color Green','Single Color White')[i%3]
        q.attrs['PixelSize']='12'
        q.submodels={f'CIRCUIT_{n:02}':[n] for n in range(1,factor+1)}
        g.models[i]=q


def ac_face(x, lane):
    """Separately wired outline, eyes and seven mouth circuits;16-channel bank.

    Many physical bulbs share each circuit. Unused controller addresses stay
    reserved; they are not invented pixel channels or extra performers.
    """
    from models.ultimate_showcase import _path
    g=Garden();points=[];circuits=[];subs={}
    def part(name,values,circuit):
        values=np.asarray(values)+(x,0,6)
        points.extend(values);circuits.extend([circuit]*len(values));subs[name]=[circuit]
    part('OUTLINE',_path([(0,22,0),(-5,14,0),(-3,14,0),(-7,5,0),(-4,5,0),(-9,0,0),(9,0,0),(4,5,0),(7,5,0),(3,14,0),(5,14,0)],180,closed=True),1)
    t=np.linspace(0,math.tau,40,endpoint=False)
    part('EYES',np.vstack([np.c_[s*2+.6*np.cos(t),10+.9*np.sin(t),np.full(40,.12)] for s in (-1,1)]),2)
    shapes={'REST':(2,.12),'MBP':(2,.18),'AH':(2.3,1.6),'EE':(2.5,.6),'OH':(1.3,1.5),'FV':(2,.45),'L':(1.8,1.2)}
    for circuit,(shape,(w,h)) in enumerate(shapes.items(),3):
        part('MOUTH_'+shape,np.c_[w*np.cos(t),6+h*np.sin(t),np.full(40,.2+circuit*.10)],circuit)
    model=g.custom('AC_SINGING_FACE_'+lane,points,'FACES','16-channel AC singing tree face',
                   ['#FFF6D8']*len(points),{})
    entries=model.attrs['CustomModelCompressed'].split(';')
    model.attrs.update(CustomModelCompressed=';'.join(','.join([str(c)]+e.split(',')[1:]) for e,c in zip(entries,circuits)),
                       StringType='Single Color White',PixelSize='14')
    model.kind='ac';model.submodels=subs
    model.details.update(circuit_count=16,point_circuits=circuits,generic_singer=lane,
                         physical_wiring_verified=False,reserved_unused_controller_circuits=7)
    return model


def build_layout(number):
    if not 1<=number<=12:raise ValueError('Layout number outside1..12')
    g=Garden(title=NAMES[number-1].replace('_',' '),slug=NAMES[number-1],
             palette=('#E73838','#35D56B','#FFF1CF') if number in (1,2,3,5) else ('#56D9FF','#BA83F4','#FFD18A'))
    if number<=6 or number==8:
        house(g,z=-12)
        for x in (-24,-8,8,24):arch(g,x,16)
        for x in (-28,-14,14,28):tree(g,x,8,h=10,r=3)
        for x in (-39,39):cane(g,x,8)
        if number<=3:
            assert len(g.models)==16
            ac_circuits(g,{1:1,2:4,3:16}[number])
            if number==3:
                # Preserve the exact256-circuit budget; restage existing
                # separate circuits into mega-tree/spinner/face silhouettes.
                tree(g,-46,-10,32,9)
                new=g.models.pop();
                replacement=Garden();replacement.models=[new];ac_circuits(replacement,16)
                g.models[10]=replacement.models[0]
                # A real radial spinner and two source-timed singing faces,
                # each assigned one16-channel bank within the same256 budget.
                spinner=Garden();a=np.repeat(np.arange(8)*math.tau/8,24);r=np.tile(np.linspace(.5,8,24),8)
                points=np.c_[46+r*np.cos(a),18+r*np.sin(a),np.full(len(a),-8)]
                spinner.custom('AC_RADIAL_SPINNER',points,'SPINNER','Eight-ray spinner',['#FFF1CF']*len(points),{})
                ac_circuits(spinner,16);g.models[11]=spinner.models[0]
                g.models[12]=ac_face(-15,'estimated_lead');g.models[13]=ac_face(15,'estimated_backing')
                for model in g.models:model.attrs['PixelSize']='14'
            return allocate(g)
        if number in (5,6,8):faces(g)
        if number in (6,8):
            for x in (-48,48):
                tree(g,x,-20,40,11)
                structures(g).starburst((x,44,-20),5)
            for x in (-20,20):structures(g).mesh('HOUSE_MATRIX',(x,9,-10),15,10,'MATRICES')
            for x in (-40,40):
                for radius in (5,7):structures(g).ring('SPINNER',(x,20,0),radius,radius,'SPINNERS',plane='xy')
    elif number==9:
        helix(g)
        for z in (-28,-8,12):structures(g).arch((0,0,z),85,75,pointed=True,zone='CATHEDRAL')
        for x in (-50,50):tree(g,x,-12,48,10)
    elif number==10:
        s=structures(g)
        for i in range(5):s.mesh('MOIRE_LAYER',(-4+i*2,2,-25+i*8),70,45,'OPTICAL',i%3,yaw=(-12+i*6),wave=1.5)
        for i in range(5):s.ring('SPIRAL_WAVE',(0,25,18+i),10+i*4,10+i*4,'SPIRALS',i%3,plane='xy',count=180)
    elif number==11:
        for i,z in enumerate((30,10,-10,-30,-50,-70)):
            s=structures(g);s.arch((0,0,z),100-i*12,60-i*6,i%3,pointed=True,zone='DEPTH')
            for side in (-1,1):s.tree(side*(52-i*6),z,30-i*2,5,color=i%3)
    elif number==12:
        base=build_ultimate_garden()
        g.models=[m for m in base.models if m.kind=='pixel' and m.display not in ('Image','Label')]
        for i,x in enumerate((-100,0,100)):house(g,x,z=10,scale=.7,prefix='HOUSE_'+str(i))
    if number>=9:
        from models.recovery_technical_layouts import enrich
        enrich(g,number)
    if number in (7,8,12):
        from models.canonical_native_band import add_band
        from tools.native_source_pose_band import stage_native_cast
        from models.showcase_flavors import _move
        added=add_band(g)
        stage_native_cast(added)
        if number==7:
            # Reuse the final native scene's actual proscenium/apron geometry.
            for side in (-1,1):
                g.poly(f'HX_SNOW_STAGE_PORTAL_{side}',[(side*48,0,50),(side*48,35,50),(0,43,50)],180,
                       'STAGE','Canonical stage portal',g.palette[2])
            g.poly('HX_SNOW_STAGE_APRON',[(-48,0,95),(48,0,95)],150,'STAGE','Canonical stage apron',g.palette[0])
        if number in (8,12):
            for m in added:_move(m,(0,0,75),(0,0,55 if number==8 else -105),.6 if number==8 else 1)
    for m in g.models:
        if not m.details.get('review_role'):
            # The large overview projects many nodes to less than one pixel.
            # Keep its real geometry/events, but make the preview bulbs legible.
            m.attrs['PixelSize']='8' if number!=12 else '10'
        if not m.submodels:m.submodels['ALL']=list(range(1,len(m.points)+1))
    return allocate(g)


def allocate(g):
    start=1
    for m in g.models:m.start=start;start+=m.channels
    return g
