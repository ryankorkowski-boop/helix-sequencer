from __future__ import annotations
import math
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'xlights_rgbeffects.xml'
OUT=ROOT/'test_runs/ultimate_showcase/xlights_rgbeffects_ultimate.xml'

def model(name, display, x, y, z=0, x2=0, y2=0, z2=0, start=12000, parm1=1, parm2=50, parm3=1, **kw):
    a={'DisplayAs':display,'StartSide':'B','Dir':'L','Antialias':'1','PixelSize':'2','Transparency':'0','parm1':str(parm1),'parm2':str(parm2),'parm3':str(parm3),'LayoutGroup':'HELIX ULTIMATE','name':name,'CustomColor':'#000000','StringType':'RGB Nodes','WorldPosX':f'{x:.4f}','WorldPosY':f'{y:.4f}','WorldPosZ':f'{z:.4f}','X2':f'{x2:.4f}','Y2':f'{y2:.4f}','Z2':f'{z2:.4f}','versionNumber':'7','StartChannel':str(start)}
    a.update({k:str(v) for k,v in kw.items()})
    return ET.Element('model',a)

def spiral_points(cx,cy,height,radius,turns,n=180):
    pts=[]
    for i in range(n):
        t=i/(n-1); ang=2*math.pi*turns*t; r=radius*(1-t*0.88)
        pts.append((cx+r*math.cos(ang),cy+r*math.sin(ang),height*t))
    return pts

def add_poly(parent,name,pts,start,parm2=180):
    data=','.join(f'{x:.3f},{y:.3f},{z:.3f}' for x,y,z in pts)
    parent.append(model(name,'Poly Line',pts[0][0],pts[0][1],pts[0][2],start=start,parm2=parm2,NumPoints=len(pts),PointData=data,cPointData=''))

def add_arch(parent,name,cx,y,height,start):
    pts=[]
    for i in range(49):
        t=i/48; pts.append((cx-12+24*t,y,height*math.sin(math.pi*t)))
    add_poly(parent,name,pts,start,49)

def main():
    tree=ET.parse(SRC); root=tree.getroot(); models=root.find('models')
    if models is None: raise SystemExit('No <models> in xLights layout')
    for i,x in enumerate([-150,-105,-60,60,105,150],1):
        add_poly(models,f'HELIX_SPIRAL_TREE_{i:02d}',spiral_points(x,110,78,24,7.0),12000+i,180)
    add_poly(models,'HELIX_HERO_SPIRAL_MEGA_TREE',spiral_points(0,135,125,42,11.0,260),12100,260)
    for i,x in enumerate(range(-150,151,30),1):
        add_arch(models,f'HELIX_ARCH_{i:02d}',x,48,34+8*math.sin((i-1)/10*math.pi),12200+i)
    native=[('HELIX_STAR_01','Star',-150,15,12320),('HELIX_STAR_02','Star',150,15,12321),('HELIX_SNOWFLAKE_01','Snowflake',-120,15,12330),('HELIX_SNOWFLAKE_02','Snowflake',120,15,12331),('HELIX_SPINNER_01','Spinner',-90,15,12340),('HELIX_SPINNER_02','Spinner',90,15,12341),('HELIX_SPHERE_01','Sphere',-55,15,12350),('HELIX_SPHERE_02','Sphere',55,15,12351),('HELIX_CIRCLE_01','Circle',-25,15,12360),('HELIX_CIRCLE_02','Circle',25,15,12361),('HELIX_CANDY_LEFT','Candy Cane',-175,-5,12370),('HELIX_CANDY_RIGHT','Candy Cane',175,-5,12371),('HELIX_WINDOW_LEFT','Window Frame',-105,-8,12380),('HELIX_WINDOW_CENTER','Window Frame',0,-8,12381),('HELIX_WINDOW_RIGHT','Window Frame',105,-8,12382),('HELIX_ICICLES_LEFT','Icicles',-70,-5,12390),('HELIX_ICICLES_RIGHT','Icicles',70,-5,12391),('HELIX_MATRIX_LEFT','Matrix',-55,-12,12400),('HELIX_MATRIX_RIGHT','Matrix',55,-12,12401)]
    for n,d,x,y,s in native: models.append(model(n,d,x,y,4,start=s,parm1=1,parm2=50,parm3=1))
    for i,(x,y,z) in enumerate([(-75,-22,15),(0,-22,17),(75,-22,15)],1): models.append(model(f'HELIX_SINGING_FACE_{i:02d}','Matrix',x,y,z,start=12500+i,parm1=24,parm2=30,parm3=1,NumStrings=24))
    models.append(model('HELIX_BAND_STAGE','Single Line',0,-42,0,x2=170,y2=0,start=12600,parm1=1,parm2=170,parm3=1))
    drum=[('KICK',-15,5),('SNARE',-7,8),('HI_HAT',-15,13),('TOM_HIGH',3,11),('TOM_MID',12,9),('TOM_FLOOR',24,7),('CYMBAL_LEFT',-2,18),('CYMBAL_RIGHT',32,18),('RIDE',40,15),('STICKS',14,22)]
    for j,(name,x,z) in enumerate(drum): models.append(model('HX_SNOWMAN_DRUMMER_'+name,'Circle' if name!='STICKS' else 'Single Line',x,-35,z,start=12700+j,parm1=1,parm2=32,parm3=1))
    for j,x in enumerate([-135,-90,-45,45,90,135],1): add_poly(models,f'HELIX_FRONT_SPIRAL_{j:02d}',spiral_points(x,2,48,14,5.0,120),12800+j,120)
    OUT.parent.mkdir(parents=True,exist_ok=True); ET.indent(tree,space='  '); tree.write(OUT,encoding='utf-8',xml_declaration=True); print(OUT)

if __name__=='__main__': main()
