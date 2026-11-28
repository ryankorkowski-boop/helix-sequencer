"""Generate deterministic Infinity 3D pixel geometry (engineering interchange, not native xLights XML)."""
import csv, math
from pathlib import Path
rows=[]
def add(name,role,points):
    for i,(x,y,z) in enumerate(points):
        rows.append((name,role,i+1,round(x,4),round(y,4),round(z,4),3*len(rows)+1))
def helix(x,z,r,h,n,turns,phase=0):
    return [(x+r*math.cos(phase+2*math.pi*turns*i/(n-1)),h*i/(n-1),z+r*math.sin(phase+2*math.pi*turns*i/(n-1))) for i in range(n)]
def line(a,b,n):
    return [tuple(a[j]+(b[j]-a[j])*i/(n-1) for j in range(3)) for i in range(n)]
for k,x in enumerate((-12,12)):
    for s in range(2): add(f'DoubleHelix{k+1}_Strand{s+1}','counterpoint',helix(x,18,2.5,14,1024,5,s*math.pi))
for k in range(8): add(f'Spiral{k+1}','melody',helix(-21+6*k,27,1.4,7,512,4))
add('PixelVolume','spatial',[(x*.3-2.25,y*.3+1,z*.3+31) for y in range(16) for z in range(16) for x in range(16)])
# Four residential silhouettes with distinct roof profiles and separate facade segments.
for k,(w,h,peak) in enumerate(((8,3,5),(7,5,3),(9,4,1),(8,4,2))):
    x=-19+k*13; z=0
    vertices=[(x,0,z),(x+w,0,z),(x+w,h,z),(x+w/2,h+peak,z),(x,h,z),(x,0,z)]
    for j in range(5): add(f'House{k+1}_Outline{j+1}','architecture',line(vertices[j],vertices[j+1],100))
    for j in range(4): add(f'House{k+1}_WindowMatrix{j+1}','harmony',[(x+1+j*(w-2)/4+a*.06,1+b*.08,z+.03) for b in range(10) for a in range(25)])
for k,(w,h,n) in enumerate(((10,7,2400),(12,9,2400),(9,16,3200))):
    x=-18+15*k
    add(f'Downtown{k+1}_Facade','structure',[(x+w*(i%40)/39,h*(i//40)/(n//40-1),45) for i in range(n)])
for k in range(6):
    add(f'Megatree{k+1}','harmony',[( -22+9*k+2*(1-j/49)*math.cos(2*math.pi*s/16),8*j/49,10+2*(1-j/49)*math.sin(2*math.pi*s/16)) for s in range(16) for j in range(50)])
for k in range(12):
    add(f'Tunnel{k+1}','transition',[(3*math.cos(math.pi*i/199),3*math.sin(math.pi*i/199),4+k*.6) for i in range(200)])
for k in range(12):
    add(f'PathArch{k+1}','rhythm',[( -25+4*k+1.5*math.cos(math.pi*i/199),1.5*math.sin(math.pi*i/199),-4) for i in range(200)])
# Canonical band geometry must be imported from approved repository assets, not fabricated.
# Continuous figure-eight double helix: Y is vertical, Z is depth.
# Two opposed strands follow a grade-separated closed centerline.
def infinity_track(t, phase):
    a,b=24.0,12.0
    x=a*math.sin(t)
    z=23+b*math.sin(2*t)
    y=6+4*math.cos(t)
    dx=a*math.cos(t)
    dz=2*b*math.cos(2*t)
    norm=math.hypot(dx,dz)
    angle=20*t+phase
    return (x-1.6*dz/norm*math.cos(angle),
            y+1.6*math.sin(angle),
            z+1.6*dx/norm*math.cos(angle))
for strand in range(2):
    add(f'DoubleHelixTrack_Strand{strand+1}','counterpoint',
        [infinity_track(2*math.pi*i/1200,strand*math.pi) for i in range(1200)])
for rung in range(80):
    t=2*math.pi*rung/80
    add(f'DoubleHelixTrack_Rung{rung+1:03d}','transition',
        line(infinity_track(t,0),infinity_track(t,math.pi),8))
assert len(rows)==38928, len(rows)
assert len({r[-1] for r in rows})==len(rows)
if __name__=='__main__':
    out=Path('infinity_pixel_geometry.csv')
    with out.open('w',newline='') as f:
        writer=csv.writer(f); writer.writerow(['model','role','node','x_m','y_m','z_m','start_channel']); writer.writerows(rows)
    print(f'{len(rows)} RGB nodes; {len(rows)*3} channels; band excluded pending canonical asset import')
