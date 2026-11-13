"""Polar Prism Parade: a dense single-float native xLights/Helix showpiece.

All positions are relative *design units* (nominal feet), not road-certified
dimensions. The scene uses Helix's existing editable native model families.
No invented audio timing: source events are supplied by the production plan.
"""
from __future__ import annotations

import math
from collections import Counter

from models.approval_layouts import allocate, structures
from models.ultimate_showcase import Garden

TITLE = "POLAR PRISM — Infinite Night Parade"
AUDIO = "Polar Prism Parade.mp3"
AUDIO_DRIVE_ID = "1VdhX9WvUFgMNhO8HGpziiG-dcInItegJ"
PALETTE = ("#62F0FF", "#FF6DD6", "#FFE49C")
# Geometry is X left-right, Y up, Z front-to-back. Approximate design
# envelope: X +/- 56, Y 0..72, Z -88..88. Not a road/rigging specification.
GROUPS = {
    "FLOAT_PRIMARY": ("PRISM_CORE", "HELIX_CROWN", "ORBIT_SHELLS"),
    "FLOAT_DEPTH": ("TUNNEL_RINGS", "PERSPECTIVE_ARCHES", "DEPTH_GRIDS"),
    "FLOAT_RHYTHM": ("WHEEL_HALOS", "SPINNERS"),
    "FLOAT_HARMONY": ("MEGA_TREES", "SPIRAL_FOREST", "HARMONIC_MATRICES"),
    "FLOAT_FLOW": ("WAVE_RAILS", "FLOOR_RUNWAYS", "SIDE_RIBBONS"),
    "FLOAT_ACCENTS": ("SNOWFLAKES", "EDGE_HIGHLIGHTS"),
}
# These are choreography priorities, not hardcoded on/off sequences.
SECTION_MAP = {
    "intro": ("FLOAT_FLOW", "FLOAT_PRIMARY"),
    "verse": ("FLOAT_HARMONY", "FLOAT_DEPTH", "FLOAT_FLOW"),
    "build": ("FLOAT_DEPTH", "FLOAT_RHYTHM", "FLOAT_PRIMARY"),
    "chorus": ("FLOAT_PRIMARY", "FLOAT_HARMONY", "FLOAT_DEPTH", "FLOAT_RHYTHM"),
    "bridge": ("FLOAT_FLOW", "FLOAT_DEPTH"),
    "solo": ("FLOAT_PRIMARY", "FLOAT_HARMONY", "FLOAT_DEPTH"),
    "outro": ("FLOAT_FLOW", "FLOAT_PRIMARY"),
}
PERCUSSION = ("kick", "snare", "hihat", "cymbal")


def _route(g, start, zone, role, *, phase=0.0, direction=1, delay=0,
           axis=None, component=None, floor=.18):
    for index, model in enumerate(g.models[start:]):
        model.zone = zone
        model.attrs.update(BlackTransparency="100", PixelSize="8", Antialias="1")
        model.details.update(
            musical_role=role,
            spatial_phase=(phase + index * .071) % 1.0,
            spatial_direction=direction,
            propagation_delay_ms=delay + index * 11,
            source_display_floor=floor,
            parade_layer=zone,
        )
        if axis:
            model.details["spatial_axis"] = axis
        if component:
            model.details["percussion_component"] = component


def build(plan=None, *, duration=None):
    """Return (editable xLights Garden, no vocalist).

    plan and duration are accepted for compatibility with the existing
    Helix layout_builder callback. Instrumental music must not animate faces.
    """
    g = Garden(title=TITLE, slug="polar_prism_night_parade", palette=PALETTE,
               description="A multi-depth illuminated rolling prism cathedral.")
    s = structures(g)

    # Central double helix / prismatic lighthouse, with separately routed
    # rungs, strands and depth rings. No fake rotating physical geometry.
    for lane, (x, z, turns) in enumerate(((-15, -7, 5), (15, 7, -5))):
        start = len(g.models)
        g.dna(f"PRISM_DNA_{lane}", x, z, 69, 8.5, turns, 370, "HELIX_CROWN")
        _route(g, start, "HELIX_CROWN", "guitarist" if lane == 0 else "bassist",
               phase=lane*.5, direction=1 if lane == 0 else -1, axis="y")
    for height, radius in ((13, 16), (27, 21), (42, 24), (57, 19), (69, 12)):
        start = len(g.models)
        s.ring("PRISM_CORE_ORBIT", (0, height, 0), radius, radius*.75,
               "PRISM_CORE", int(height//14), plane="xz", count=130)
        _route(g, start, "PRISM_CORE", "keyboardist",
               phase=(height % 14)/14, direction=-1 if int(height) % 2 else 1,
               delay=height*2, axis="x")

    # Forced-perspective portals along the vehicle's length, growing then
    # shrinking. Independent depth ordering gives a perceivable vortex.
    depths = (-68, -47, -26, -5, 16, 37, 58)
    for index, z in enumerate(depths):
        size = 34 + 17*math.sin(math.pi*index/(len(depths)-1))
        start = len(g.models)
        s.ring("DEPTH_TUNNEL", (0, 33, z), size, size*.78,
               "TUNNEL_RINGS", index, plane="xy", count=170)
        _route(g, start, "TUNNEL_RINGS", "bassist" if index % 2 else "guitarist",
               phase=index/len(depths), direction=(-1)**index,
               delay=index*48, axis="x")
        start = len(g.models)
        s.arch((0, 1, z), width=size*2.2, height=size*1.5,
               color=index, zone="PERSPECTIVE_ARCHES")
        _route(g, start, "PERSPECTIVE_ARCHES", "drummer",
               phase=index/len(depths), component=PERCUSSION[index%4],
               delay=index*32, axis="x")

    # Four wheels are real visual groups, distinct from the independent
    # rhythm spinners hovering above them.
    for side in (-1, 1):
        for axle, z in enumerate((-49, 49)):
            x=side*47
            for layer, radius in enumerate((7.5, 10, 12)):
                start=len(g.models)
                s.ring("WHEEL_HALO", (x, 13, z+layer*.9), radius, radius,
                       "WHEEL_HALOS", axle+layer, plane="xy", count=120)
                _route(g, start, "WHEEL_HALOS", "drummer",
                       component=PERCUSSION[(axle+layer+(side>0))%4],
                       phase=layer/3, direction=side, axis="x")
            start=len(g.models)
            s.starburst((x, 13, z+4), 8, color=axle,
                        zone="SPINNERS")
            _route(g, start, "SPINNERS", "drummer", component="hihat" if side<0 else "snare",
                   phase=axle*.5, direction=side)

    # Readable long-range note cascades: non-coplanar spiral towers and four
    # separate harmonic matrix planes (not flat duplicate panels).
    for side in (-1, 1):
        for index, z in enumerate((-53, -22, 11, 44)):
            x=side*(37+(index%2)*4)
            start=len(g.models)
            s.tree(x, z, 25 + (index%3)*7, 7, color=index)
            _route(g, start, "SPIRAL_FOREST",
                   ("guitarist", "keyboardist", "bassist")[index%3],
                   phase=(index+(side>0)*.5)/4, direction=side, axis="y",
                   delay=index*60)
    for side in (-1,1):
        start=len(g.models)
        g.tree(f"PARADE_MEGA_{side}", side*43, -72, 52, 11, 2.5, 20, 50,
               "MEGA_TREES")
        _route(g,start,"MEGA_TREES","keyboardist",
               phase=0 if side<0 else .5, direction=side,axis="y")
    for layer,z in enumerate((-66,-23,23,66)):
        start=len(g.models)
        s.mesh("HARMONIC_PRISM_MATRIX",(0,8,z),48,38,"HARMONIC_MATRICES",
               layer,wave=2+layer,yaw=(-1)**layer*13)
        _route(g,start,"HARMONIC_MATRICES",
               ("keyboardist","guitarist","bassist")[layer%3],
               phase=layer/4, direction=(-1)**layer,delay=layer*95,axis="y")
    for layer,z in enumerate((-57,-20,17,54)):
        start=len(g.models)
        s.mesh("TRANSPARENT_DEPTH_GRID",(0,3,z),73,28,"DEPTH_GRIDS",
               layer,wave=3,yaw=(layer-1.5)*8)
        _route(g,start,"DEPTH_GRIDS","keyboardist",
               phase=layer/4,delay=layer*80,axis="x",floor=.13)

    # Propagating envelope paths: long waves, roof/edge contours, plus
    # staggered 3D rails following the full float.
    for side in (-1,1):
        for tier, y in enumerate((4, 14, 26)):
            vertices=[]
            for step in range(16):
                z=-79+step*(158/15)
                x=side*(49 - tier*4 + 2*math.sin(step*.8+tier))
                vertices.append((x,y+2*math.sin(step*.65+tier),z))
            start=len(g.models)
            s.path("SIDE_RIBBON",vertices,"SIDE_RIBBONS",tier,count=190)
            _route(g,start,"SIDE_RIBBONS",
                   "bassist" if tier==0 else "guitarist",
                   phase=tier/3, direction=side,axis="z",
                   delay=tier*45)
    for side in (-1,1):
        for y in (2,7):
            start=len(g.models)
            s.path("RUNWAY",[(side*19,y,-79),(side*19,y,79)],
                   "FLOOR_RUNWAYS",0,count=170)
            _route(g,start,"FLOOR_RUNWAYS","bassist",
                   phase=.5 if side>0 else 0,direction=side,axis="z")
    for tier,y in enumerate((22,36,50,64)):
        start=len(g.models)
        s.dna("OVERHEAD_WAVE",(-37,y,-74),(37,y,74),3+tier*.4,
              turns=2.5+tier*.5,zone="WAVE_RAILS",color=tier)
        _route(g,start,"WAVE_RAILS","guitarist",
               phase=tier/4,direction=(-1)**tier,axis="z")

    # Orbits/rays are precise, standalone native models and can receive
    # coordinated note/strike windows instead of global white pulses.
    for tier,(y,rx,rz) in enumerate(((30,34,57),(47,28,48),(62,19,37))):
        start=len(g.models)
        s.ring("ORBIT_SHELL",(0,y,0),rx,rz,"ORBIT_SHELLS",
               tier,plane="xz",count=190)
        _route(g,start,"ORBIT_SHELLS","keyboardist",
               phase=tier/3,direction=(-1)**tier,axis="x")
    for side in (-1,1):
        for index,z in enumerate((-65,-38,-11,16,43,70)):
            start=len(g.models)
            s.starburst((side*51,39+(index%3)*8,z),5+(index%3)*2,
                        color=index,zone="SNOWFLAKES")
            _route(g,start,"SNOWFLAKES","drummer",
                   component=PERCUSSION[index%4],phase=index/6,
                   direction=side,delay=index*29)
    for side in (-1,1):
        for index,z in enumerate((-74,0,74)):
            start=len(g.models)
            s.path("EDGE_GLYPH",[(side*53,1,z-9),(side*55,10,z),
                                 (side*53,1,z+9)],"EDGE_HIGHLIGHTS",
                   index,count=85)
            _route(g,start,"EDGE_HIGHLIGHTS","drummer",
                   component=PERCUSSION[(index+2)%4],direction=side)
    # Existing source-specific spatial route compiler owns actual note timing.
    from tools.source_role_routing import configure_source_routes
    configure_source_routes(g.models)
    return allocate(g), None


def inventory():
    g, _ = build()
    count=Counter(model.zone for model in g.models)
    return dict(title=TITLE, source=AUDIO, groups=GROUPS,
                section_priority=SECTION_MAP, model_count=len(g.models),
                pixels=sum(len(m.points) for m in g.models),
                zones=dict(sorted(count.items())), native_groups=len(GROUPS))
