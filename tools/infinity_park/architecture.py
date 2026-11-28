"""Distinct estate, festival, vehicle and stage meshes for the park."""

from math import cos, pi, sin

import numpy as np

from .geometry import bezier, ring


def framed_window(s, d, label, x, y, z, w, h, frame, pane, *, pointed=False):
    if pointed:
        outline = [(x-w/2,y,z-h*.5), (x+w/2,y,z-h*.5), (x+w/2,y,z+h*.08),
                   (x+w*.36,y,z+h*.27), (x,y,z+h*.55), (x-w*.36,y,z+h*.27),
                   (x-w/2,y,z+h*.08)]
        # Stained panels form separate coloured petals within the stone jamb.
        center = (x,y+.02,z)
        for i, a in enumerate(outline):
            s.mesh(d, (pane, "ruby", "violet", "mint")[i%4], [center, a, outline[(i+1)%len(outline)]], [(0,1,2)])
        s.tube(d, frame, outline + [outline[0]], .16)
        s.light(d, "Window", label, np.concatenate([
            np.linspace(a, b, 5, endpoint=False) for a,b in zip(outline,outline[1:]+outline[:1])]), .13)
    else:
        s.box(d, frame, (x,y+.035,z), (w+.39,.28,h+.34))
        s.box(d, pane, (x,y-.13,z), (w,.17,h))
        for horizontal in (False, True):
            size = (w,.1,.07) if horizontal else (.07,.1,h)
            s.box(d, frame, (x,y-.23,z), size)
        outline = [(x-w/2,y-.27,z-h/2), (x+w/2,y-.27,z-h/2),
                   (x+w/2,y-.27,z+h/2), (x-w/2,y-.27,z+h/2)]
        s.light(d, "Window", label, np.concatenate([
            np.linspace(a,b,5,endpoint=False) for a,b in zip(outline,outline[1:]+outline[:1])]), .10)


def staircase(s, d, xy, w, step_count, depth=.55, rise=.25):
    x,y = xy
    for i in range(step_count):
        s.box(d, "marble", (x,y-i*depth,(step_count-i)*rise/2), (w+i*.35,depth+.1,(step_count-i)*rise))


def terrace_rail(s, d, label, x, y, z, width, metal):
    s.strip(d, "Roofline", label, (x-width/2,y-.05,z+1.05), (x+width/2,y-.05,z+1.05), max(12,int(width*3)))
    s.tube(d, metal, [(x-width/2,y,z+1), (x+width/2,y,z+1)], .11)
    s.tube(d, metal, [(x-width/2,y,z+.18), (x+width/2,y,z+.18)], .095)
    for a in np.linspace(x-width/2,x+width/2,int(width)+1):
        s.tube(d, metal, [(a,y,z+.12),(a,y,z+1)], .065)


def grand_estate(s, x, y):
    d = "Grand"
    s.box(d, "paving", (x,y-8,.05), (57,34,.28))
    for i, (dx,w,depth,h) in enumerate(((0,26,18,14),(-20,15,15,10),(20,15,15,10))):
        cx = x+dx
        front = y-depth/2
        s.box(d, "marble", (cx,y,h/2), (w,depth,h))
        for z in (1,h*.54,h-.3,h+.15):
            s.box(d, "trim", (cx,y,z), (w+.55,depth+.55,.32))
        s.roof(d,"slate",(cx,y,h+.24),(w+.7,depth+.85,3.2),w*.67)
        s.strip(d,"Roofline",str(i),(cx-w/2,front-.32,h+.18),(cx+w/2,front-.32,h+.18),68)
        for j, dx2 in enumerate(np.linspace(-w*.36,w*.36,5)):
            for k,z in enumerate((h*.31,h*.74)):
                framed_window(s,d,f"{i}_{j}_{k}",cx+dx2,front-.16,z,1.75,2.6,"trim","warm_glass")
        for side in (-1,1):
            for j in range(4):
                s.box(d,"trim",(cx+side*(w/2+.07),y-5+3.3*j,h*.62),(.3,1.8,4.2))
    front = y-13
    staircase(s,d,(x,front-1),20,6)
    s.box(d,"marble",(x,y-11,1.3),(22,6,.55))
    s.box(d,"slate",(x,y-11,12.6),(23,6,.65))
    s.roof(d,"trim",(x,y-11,12.95),(23,6.8,3.1),.3)
    s.light(d,"Roofline","Portico_Gable",[(x+u,front-.83,13+v) for u,v in
            zip(np.linspace(-11.5,11.5,79),3.1*(1-np.abs(np.linspace(-1,1,79))))],.17)
    for j, dx in enumerate(np.linspace(-10,10,8)):
        s.profile(d,"trim",(x+dx,front),[(1.5,.66),(1.65,.74),(2.02,.53),(11.8,.42),(12,.64),(12.45,.68)],sides=18)
        for k in range(10):
            a=k*pi/5
            s.tube(d,"marble",[(x+dx+.5*cos(a),front+.5*sin(a),2),
                               (x+dx+.4*cos(a),front+.4*sin(a),11.8)],.041)
        s.strip(d,"Pillar",str(j),(x+dx,front-.57,2),(x+dx,front-.45,11.8),34,.12)
    terrace_rail(s,d,"Balcony",x,y-9.65,7.7,11,"gold")
    s.box(d,"gold",(x,y-9.23,3.45),(4,.48,4.9))
    s.box(d,"dark_stone",(x,y-9.52,3.38),(3.5,.2,4.44))
    for side in (-1,1):
        for j in range(3):
            s.box(d,"hedge",(x+side*(12+5*j),y-20,.57),(3.6,8.3,1.15))
            s.profile(d,"paving",(x+side*(12+5*j),y-26),[(0,.8),(1.1,.63),(1.26,.87)],sides=12)
            s.profile(d,"fern",(x+side*(12+5*j),y-26),[(.9,.5),(1.6,1.22),(2.25,.23)],sides=16)
    pond_y = y-29
    for mat, z, rx, ry in (("marble",.15,10,4.7),("water",.22,9.4,4.15)):
        s.shell(d,mat,[ring(x,pond_y,z-.13,rx,ry,n=64),ring(x,pond_y,z,rx,ry,n=64)])
    s.light(d,"Pathway","Reflection_Pond",ring(x,pond_y,.27,9.65,4.37,n=110),.13)
    for i in (-5,0,5):
        s.profile(d,"marble",(x+i,pond_y),[(.2,.55),(.7,.49),(1.15,.22),(1.25,.69)],sides=18)
        for j in range(6):
            a=j*pi/3
            t=np.linspace(0,1,13)
            jet=np.c_[x+i+t*1.6*cos(a),pond_y+t*1.6*sin(a),1.25+9*t*(1-t)-.97*t]
            s.tube(d,"glass",jet,.034)
            s.light(d,"Fountain",f"{i+5}_{j}",jet,.07)


def modern_estate(s, x, y):
    d = "Modern"
    s.box(d,"paving",(x,y-5,.17),(53,33,.5))
    volumes = [(-5,0,25,16,2.1,5.5),(7,2,34,14,7.6,5.3),
               (-10,5,22,13,12.9,5),(15,6,10,10,1.9,6)]
    for i,(dx,dy,w,depth,base,h) in enumerate(volumes):
        cx,cy = x+dx,y+dy
        s.box(d,"graphite",(cx,cy,base+h/2),(w,depth,h))
        for z in (base,base+h):
            s.box(d,"ceramic",(cx,cy,z),(w+.72,depth+1.02,.52))
        front=cy-depth/2-.32
        n=int(w/2.6)
        for j in range(n):
            xx=cx-w/2+1.2+j*(w-2.4)/(n-1)
            s.box(d,"glass" if j%4 else "warm_glass",(xx,front,base+h/2),(2.1,.22,h-.86))
            s.box(d,"chrome",(xx+1.13,front-.15,base+h/2),(.09,.19,h-.45))
        for side in (-1,1):
            s.box(d,"glass",(cx+side*(w/2+.07),cy+.4,base+h/2),(.2,depth-2,h-.85))
        for z, suffix in ((base,"Lower"),(base+h,"Upper")):
            s.strip(d,"Roofline",f"{i}_{suffix}",(cx-w/2,front-.34,z),(cx+w/2,front-.34,z),int(w*3))
        terrace_rail(s,d,f"Terrace_{i}",cx,front-.54,base+.12,w-1,"chrome")
    staircase(s,d,(x+10,y-10),13,7)
    s.box(d,"water",(x+16,y-21,.31),(19,7,.17))
    s.box(d,"ceramic",(x+16,y-25,.32),(21,.65,.4))
    for i in range(9):
        s.box(d,"ceramic",(x-18+i*.83,y-8.4,5.2),(.36,.88,7.3))
    for j, p in enumerate(((-23,-10,3.2),(25,-5,4),(6,-7,10),(-18,0,15))):
        dx,dy,z=p
        s.box(d,"screen",(x+dx,y+dy+.25,z),(6.5,.5,3.75))
        s.surface(d,"Matrix",f"Media_{j}",(x+dx,y+dy-.08,z),6,3.2,23,13)


def gothic_estate(s, x, y):
    d = "Gothic"
    s.box(d,"dark_stone",(x,y,8.8),(36,17,17.6))
    s.roof(d,"slate",(x,y,17.55),(37,18.4,10),24)
    s.roof(d,"copper",(x,y-5,16.5),(17,12,10),.4)
    for i, (dx,dy,h,r) in enumerate(((-18,-4,23,4.5),(18,-4,24,4.6),(-12,7,20,3),
                                      (12,7,20,3),(0,4,29,3.1))):
        cx, cy = x+dx, y+dy
        s.profile(d,"stone",(cx,cy),[(0,r+.51),(2,r+.45),(2.3,r),(h-1.2,r),(h,r+.54),(h+.8,r+.4)],sides=8)
        s.profile(d,"slate",(cx,cy),[(h+.75,r+.43),(h+2,r+.12),(h+7,r*.47),(h+11,.11)],sides=8)
        for j in range(8):
            a=j*pi/4
            s.strip(d,"Spires",f"{i}_{j}",(cx+(r+.13)*cos(a),cy+(r+.13)*sin(a),h+1.8),
                    (cx+.19*cos(a),cy+.19*sin(a),h+10.8),28)
            s.box(d,"dark_stone",(cx+(r+.13)*cos(a),cy+(r+.13)*sin(a),h+.12),(.5,.5,1.45))
        for j,z in enumerate((6,12,18)):
            framed_window(s,d,f"Tower_{i}_{j}",cx,cy-r-.07,min(z,h-2),1.25,2.75,"dark_stone","ruby",pointed=True)
    for i,dx in enumerate((-12,-7,0,7,12)):
        framed_window(s,d,f"Facade_{i}",x+dx,y-8.7,9.5,3 if dx else 4,6.8,"stone","violet",pointed=True)
        if dx:
            s.box(d,"stone",(x+dx-2,y-9.1,7.5),(.6,1.1,15))
    framed_window(s,d,"Grand_Portal",x,y-8.86,2.8,4.4,5.1,"stone","dark_stone",pointed=True)
    staircase(s,d,(x,y-9.1),9,4)
    for k in range(4):
        s.strip(d,"Roofline",f"Main_{k}",(x-18.4,y-8.8+k*.14,17.8+k*.23),
                (x+18.4,y-8.8+k*.14,17.8+k*.23),82,.135)
    for side in (-1,1):
        terrace_rail(s,d,f"Balcony_{side}",x+side*9,y-9.27,6.15,7,"copper")
        for i in range(7):
            xx=x+side*(7+i*2.7)
            s.box(d,"stone",(xx,y-17,.9),(1.1,1.1,1.8))
            s.profile(d,"copper",(xx,y-17),[(1.8,.68),(2.6,.03)],sides=4)
    rose = ring(x,y-10.96,17.5,3.2,n=68,vertical=True)
    s.tube(d,"stone",np.r_[rose,rose[:1]],.27)
    s.light(d,"Star","Rose_Window",rose,.17)
    for i in range(12):
        a=i*pi/6
        end=(x+2.95*cos(a),y-11.07,17.5+2.95*sin(a))
        s.strip(d,"Tracery",str(i),(x,y-11.09,17.5),end,13,.13)


def jungle(s, x, y):
    d="Jungle"
    sites = [(-21,0,12,6),(-7,5,18,8),(10,7,14,6.2),(23,1,19,8),
             (-15,-13,9,4.5),(2,-11,11,5.8),(19,-12,9,4.1),(-26,11,9,4.1)]
    for i,(dx,dy,h,r) in enumerate(sites):
        px,py=x+dx,y+dy
        drift = (-1)**i*2.2
        stem=bezier([(px,py,0),(px-2,py+2,h*.4),(px+drift,py,h*.65),
                     (px+drift,py+.8,h)],21)
        for j in range(6):
            a=j*pi/3
            vine=np.array([(a0+.66*cos(a+t*7),b+.66*sin(a+t*7),z)
                           for (a0,b,z),t in zip(stem,np.linspace(0,1,len(stem)))])
            s.light(d,"Vine",f"{i}_{j}",vine,.13)
        s.tube(d,"cream",stem,.64+r*.105,sides=16)
        cx,cy=stem[-1,:2]
        cap=(("ruby","violet","peach","mint")[i%4])
        s.profile(d,cap,(cx,cy),[(h-.82,r*.34),(h-.51,r*.76),(h-.13,r),(h+.6,r*.93),
                                 (h+r*.34,r*.7),(h+r*.46,r*.33),(h+r*.50,.2)],sides=40)
        s.profile(d,"cream",(cx,cy),[(h-.79,r*.36),(h-.58,r*.74),(h-.24,r*.97)],sides=38)
        s.light(d,"Mushroom",f"{i}_Brim",ring(cx,cy,h-.29,r*.98,n=85),.18)
        for j in range(20):
            a=j*pi/10
            gill=np.array([(cx+rr*cos(a),cy+rr*sin(a),h-.88+.6*t)
                           for t,rr in zip(np.linspace(0,1,15),np.linspace(r*.3,r*.96,15))])
            s.tube(d,"peach",gill,.065,sides=4)
            s.light(d,"Gill",f"{i}_{j}",gill,.094)
        for j in range(11):
            a=j*2.39996
            rr=r*(.35+.48*((j%4)/3))
            z=h+r*.52*(1-(rr/r)**1.55)
            s.shell(d,"cream",[ring(cx+rr*cos(a),cy+rr*sin(a),z,.56,n=12),
                               ring(cx+rr*cos(a),cy+rr*sin(a),z+.12,.27,n=12)])
    for i in range(18):
        px=x-27+(i%9)*6.6
        py=y-23+(i//9)*36+.8*sin(i)
        z=2.6+.6*(i%3)
        stem=[(px,py,0),(px+.2,py,z*.6),(px-.3,py,z)]
        s.tube(d,"fern",stem,.17)
        for j in range(6):
            a=j*pi/3
            petal=bezier([stem[-1],(px+cos(a)*.6,py+sin(a)*.6,z+.4),
                          (px+cos(a)*1.7,py+sin(a)*1.7,z+1),
                          (px+cos(a)*1.35,py+sin(a)*1.35,z+1.3)],9)
            s.tube(d,("coral","mint","gold")[i%3],petal,.23,sides=8)
            s.light(d,"Flower",f"{i}_{j}",petal,.092)
    for i in range(8):
        px=x-29+8.1*i
        py=y+16
        branch=bezier([(px,py,0),(px+4,py,5),(px-4,py,8),(px+2.8,py-2,12)],25)
        s.tube(d,"bark",branch,.48,sides=10)
        s.light(d,"Vine",f"Canopy_{i}",branch+np.array([0,-.43,0]),.15)
        for j in range(4):
            start=branch[11+3*j]
            end=start+np.array([(-1)**j*(2+j*.45),-2.9,2.85])
            s.tube(d,"bark",[start,start*.5+end*.5+np.array([0,0,-.45]),end],.225)
            s.profile(d,"fern",end[:2],[(end[2]-1,.9),(end[2],2.3),(end[2]+.9,1.42)],sides=14)


def vehicle(s,d,label,center,style,angle):
    x,y,z=center
    long,wide = (11,4.15) if style in ("float","stage","sleigh") else (8.6,3.35)
    if style == "lowrider":
        long,wide=7.6,2.78
    def place(a,b,c):
        return x+a*cos(angle)-b*sin(angle), y+a*sin(angle)+b*cos(angle), z+c
    def box(mat,pos,size):
        s.box(d,mat,place(*pos),size,angle)
    paint={"float":"violet","sleigh":"ruby","stage":"mint","van":"peach","lowrider":"coral","truck":"copper"}[style]
    box("graphite",(0,0,1.0),(long,wide,1.23))
    box(paint,(0,0,1.65),(long-.18,wide+.08,.66))
    for side in (-1,1):
        for i,dx in enumerate((-long*.34,long*.34)):
            center=place(dx,side*(wide/2-.23),.82)
            angles=np.arange(22)*2*pi/22
            rings=[np.array([place(dx+.83*cos(a),side*(wide/2-.30)+b,.82+.83*sin(a)) for a in angles])
                   for b in (-.27,.27)]
            s.shell(d,"rubber",rings)
            wheel=[place(dx+.55*cos(a),side*(wide/2+.01),.82+.55*sin(a)) for a in angles]
            s.shell(d,"chrome",[wheel,[place(dx+.42*cos(a),side*(wide/2+.14),.82+.42*sin(a)) for a in angles]])
            s.light(d,"Wheel",f"{label}_{side}_{i}",wheel,.095)
        for height in (.55,1.71):
            s.strip(d,"Vehicle",f"{label}_{side}_{height}",place(-long*.46,side*(wide/2+.05),height),
                    place(long*.46,side*(wide/2+.05),height),37,.12)
    for dx in (-long/2,long/2):
        box("chrome",(dx,0,1.29),(.4,wide+.13,.45))
        for side in (-1,1):
            box("warm_glass" if dx>0 else "ruby",(dx*1.01,side*wide*.36,1.82),(.2,.57,.33))
            s.strip(d,"Headlight",f"{label}_{dx}_{side}",
                    place(dx*1.02,side*wide*.36-.18,1.84),place(dx*1.02,side*wide*.36+.18,1.84),6,.11)
    for i in range(7):
        box("chrome",(long/2+.08,0,1.45+i*.076),(.14,wide*.47,.029))
    cab_x = long*.27 if style != "lowrider" else .1
    cab_h = 1.6 if style != "lowrider" else 1.03
    if style in ("van","truck","stage","lowrider"):
        box(paint,(cab_x,0,2+cab_h/2),(long*.29,wide*.87,cab_h))
        box("glass",(cab_x+long*.15,0,2+cab_h*.63),(.16,wide*.76,cab_h*.66))
        for side in (-1,1):
            box("glass",(cab_x,side*wide*.438,2+cab_h*.66),(long*.21,.12,cab_h*.48))
        if style != "lowrider":
            box("ceramic",(-long*.19,0,3.15),(long*.61,wide,2.75))
            for side in (-1,1):
                s.surface(d,"Matrix",f"{label}_{side}",place(-long*.19,side*(wide/2+.035),3.19),
                          long*.54,2.03,23,9,angle=angle)
                box("graphite",(-long*.19,side*wide*.499,3.19),(long*.58,.16,2.3))
    if style in ("float","sleigh"):
        box("gold",(0,0,2.05),(long,wide+.45,.44))
        for i in range(4):
            ax=(i-1.5)*2.15
            px,py,pz=place(ax,0,0)
            h=2.8+(3-abs(i-1.5))*.75
            if style == "sleigh":
                s.profile(d,"pine",(px,py),[(2.24,1.18),(3.2,1.38),(3.55,.84),(4.45,.96),(h+.83,.07)],sides=14)
            else:
                s.profile(d,("violet","mint","peach","ruby")[i],(px,py),[(2.24,.2),(h-.37,.31),(h+.3,1.25),(h+.9,.2)],sides=20)
            s.light(d,"Float",f"{label}_{i}",ring(px,py,h+.27,1.19,n=23),.13)
    return place


def motor_district(s,x,y):
    d="Motor"
    s.box(d,"road",(x,y,.09),(65,49,.25))
    for j in (-12,2,16):
        s.box(d,"paving",(x,y+j,.16),(64,.75,.3))
        for i in np.linspace(-30,30,13):
            s.box(d,"gold",(x+i,y+j-1.6,.21),(2,.24,.11))
    specs=[(-21,-11,"float"),(-8,-11,"lowrider"),(6,-11,"sleigh"),(22,-11,"van"),
           (-19,4,"van"),(-4,4,"stage"),(11,4,"lowrider"),(24,4,"truck"),
           (-21,16,"truck"),(-6,16,"sleigh"),(9,16,"float"),(24,16,"stage")]
    for i,(dx,dy,style) in enumerate(specs):
        vehicle(s,d,f"{style}_{i:02d}",(x+dx,y+dy,.18),style,(-1)**i*.13)


def concert(s,x,y):
    d="Arena"
    s.box(d,"graphite",(x,y,1.08),(49,25,2.13))
    staircase(s,d,(x,y-12.95),17,6,.52,.32)
    s.box(d,"black",(x,y+2,2.24),(45,20,.27))
    s.box(d,"graphite",(x-12,y+3,2.65),(9,6,1.14))
    s.box(d,"ceramic",(x,y+2,16.3),(52,24,.55))
    s.roof(d,"graphite",(x,y+2,16.6),(52,24,3.1),41)
    for sx in (-1,1):
        for yy in (-10,11):
            xx=x+sx*23.4
            for i in (-.9,.9):
                s.tube(d,"chrome",[(xx+i,y+yy,0),(xx+i,y+yy,16.3)],.16)
            for i in range(9):
                lo=1+1.65*i
                s.tube(d,"chrome",[(xx-.9,y+yy,lo),(xx+.9,y+yy,lo+1.65)],.088)
                s.tube(d,"chrome",[(xx+.9,y+yy,lo),(xx-.9,y+yy,lo+1.65)],.088)
            s.strip(d,"Truss",f"{sx}_{yy}",(xx,y+yy-.1,1),(xx,y+yy-.1,16),56,.16)
        for j in range(4):
            s.box(d,"black",(x+sx*26.3,y-8.8,j*1.08+2.8),(2.6,2,1.04),sx*.16)
        s.box(d,"screen",(x+sx*18.2,y+3,9),(5.7,.62,11.4))
        s.surface(d,"Matrix",f"Portrait_{sx}",(x+sx*18.2,y+2.62,9),5.2,10.8,17,28)
    for i,dy in enumerate((-10,-3,4,11)):
        for dz in (15,16.1):
            s.tube(d,"chrome",[(x-23,y+dy,dz),(x+23,y+dy,dz)],.14)
        for dx in range(-22,22,2):
            s.tube(d,"chrome",[(x+dx,y+dy,15),(x+dx+2,y+dy,16.1)],.075)
        s.strip(d,"Truss",f"Overhead_{i}",(x-22,y+dy-.08,15),(x+22,y+dy-.08,15),91)
    for i in range(13):
        dx=(i-6)*2.37
        bend=.015*dx*dx
        s.box(d,"screen",(x+dx,y+8+bend,9.2),(2.5,.58,10.7),.030*dx)
    s.surface(d,"Matrix","Curved_Backwall",(x,y+7.55,9.2),30,10,81,26,curve=3.4)
    for i in range(8):
        s.strip(d,"Stagefloor",str(i),(x-21,y-10+i*1.9,2.39),(x+21,y-10+i*1.9,2.39),72,.096)
    for i in range(6):
        xx=x-14.5+i*5.8
        s.strip(d,"Performance_Riser",str(i),(xx-2.5,y-5.4,2.59),(xx+2.5,y-5.4,2.59),19,.1)


def nexus(s,x,y):
    d="Nexus"
    s.profile(d,"dark_stone",(x,y),[(0,16.2),(.5,16.2),(.68,14.5),(1.6,14.5),(1.8,11.2)],sides=48)
    for i,(dx,r,h,turns) in enumerate(((-9,5.3,42,2.4),(9,5.1,38,2.15))):
        cx=x+dx
        s.profile(d,"graphite",(cx,y),[(0,4.6),(1.5,4.5),(2.2,1.5),(h,1.12),(h+.7,.29)],sides=16)
        t = np.linspace(0,1,362)
        strands=[]
        for j in range(2):
            phase=2*pi*turns*t+j*pi+i*.6
            path=np.c_[cx+r*np.cos(phase),y+r*np.sin(phase),2+h*t]
            strands.append(path)
            s.tube(d,"chrome",path,.22,sides=8)
            for side in (-1,1):
                result=path+np.c_[side*.33*np.cos(phase),side*.33*np.sin(phase),np.full(len(t),.2)]
                s.light(d,"Double_Helix",f"{i}_{j}_{side}",result,.19)
        for j,k in enumerate(range(0,len(t),13)):
            s.tube(d,"copper",[strands[0][k],strands[1][k]],.12)
            s.strip(d,"Helix_Rung",f"{i}_{j}",strands[0][k]+(0,0,.22),strands[1][k]+(0,0,.22),19,.13)
    for level,z in enumerate((5,14,23)):
        path=ring(x,y,z,22-level*2.5,15-level*.8,n=120,closed=True)
        s.tube(d,"graphite",path,.26)
        s.light(d,"Elevated_Track",str(level),path[:-1]+(0,0,.25),.17)
        for j in range(0,120,15):
            a,b,_=path[j]
            s.tube(d,"graphite",[(a,b,0),(a,b,z)],.19)
