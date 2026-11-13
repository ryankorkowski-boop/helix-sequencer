"""Ford Transit Connect rear/side three-quarter native RGB pixel-matrix concept.

Design-unit coordinates only; not a vehicle measurement or wiring plan.
Front faces positive Z; rear faces negative Z. Both side panels carry the owner's traced D/M mark.
"""
from __future__ import annotations
import numpy as np
from models.ultimate_showcase import Garden
from models.approval_layouts import allocate, structures
from models.brewery_branding import owner_logo_mask

def _panel(g, name, points, zone, color, role="guitarist", **details):
    if not points:
        raise ValueError("Empty van panel: " + name)
    return g.custom(name, points, zone, "Native editable van RGB pixel nodes",
                    [color] * len(points), {"ALL": list(range(1, len(points)+1))},
                    details={"musical_role": role, "parade_layer": zone, **details})

def build(plan=None, *, duration=None):
    g = Garden(title="Drastic Measures — Ford Transit Connect RGB Matrix",
               slug="drastic_measures_transit_connect_rgb",
               palette=("#45DFFF", "#FFB84F", "#FF5BB9"),
               description="Recognizable compact van with dense RGB body matrix, clear windows and side logos")
    s = structures(g)
    # The silhouette has a tall rear cabin and short, sloping hood.
    for side in (-1, 1):
        x = side * 34
        # Body-side pixel matrix, excluding glass, wheel openings and the central logo field.
        body, logo_field = [], []
        for z in range(-66, 70, 3):
            top = 49 if z <= 35 else (49-(z-35)*.86 if z <= 53 else 27)
            for y in range(9, int(top)+1, 3):
                # Two wheel openings remain dark and legible.
                if y < 20 and (abs(z+43) < 14 or abs(z-46) < 14):
                    continue
                # Side glass and windshield are unlit.
                if y >= 29 and (18 <= z <= 53):
                    continue
                if -45 <= z <= 4 and 19 <= y <= 42:
                    logo_field.append((x, float(y), float(z)))
                else:
                    body.append((x, float(y), float(z)))
        _panel(g, "TRANSIT_BODY_MATRIX_"+str(side), body, "BODY_MATRIX",
               "#45DFFF", role="bassist", source_display_floor=.12)
        # A subdued independent panel behind the logo allows branding to stay visible.
        _panel(g, "TRANSIT_LOGO_BACKDROP_"+str(side), logo_field, "LOGO_BACKDROP",
               "#244E69", role="keyboardist", source_display_floor=.06)
        lines = {
            "ROOFLINE": [(x,49,-69),(x,49,35),(x,46,42)],
            "WINDSHIELD": [(x,46,42),(x,29,54)],
            "HOOD": [(x,29,54),(x,27,69)],
            "SILL": [(x,9,-69),(x,9,69)],
            "REAR": [(x,9,-69),(x,49,-69)],
            "BELT": [(x,26,-69),(x,26,54)],
            "DOOR": [(x,10,-13),(x,29,-13)],
        }
        for label, coords in lines.items():
            s.path("TRANSIT_"+label, coords, "BODY_OUTLINE", 0, count=70)
        # Original brewery D/M artwork, mapped onto the side door area.
        mask = owner_logo_mask()
        up=np.zeros_like(mask);up[1:]=mask[:-1]
        down=np.zeros_like(mask);down[:-1]=mask[1:]
        left=np.zeros_like(mask);left[:,1:]=mask[:,:-1]
        right=np.zeros_like(mask);right[:,:-1]=mask[:,1:]
        edge=mask & ~(up & down & left & right)
        rr,cc=np.where(edge & (np.indices(mask.shape)[0]%2==0))
        points=[(side*36, 17+(145-float(r))*.17, -25+(float(c)-55.5)*.33)
                for r,c in zip(rr,cc)]
        _panel(g, "DRASTIC_MEASURES_LOGO_"+str(side), points,
               "BREWERY_EMBLEM", "#FFB84F", brand_emblem=True,
               source_display_floor=.58, always_readable=True)
        # Dark wheel outlines establish the vehicle profile, not floating decoration.
        for z in (-43,46):
            s.ring("TRANSIT_WHEEL", (x,11,z), 12,12,"WHEELS",0,plane="yz",count=80)
    # Rear split cargo doors and tail lamps establish the owner's rear/side view.
    rear=[(float(x),float(y),-70.) for x in range(-31,32,3)
          for y in range(10,49,3) if not (abs(x)<3)]
    _panel(g,"TRANSIT_REAR_DOOR_MATRIX",rear,"REAR_MATRIX","#45DFFF",
           source_display_floor=.14)
    for side in (-1,1):
        s.path("TRANSIT_TAIL_LAMP",[(side*31,17,-71),(side*31,42,-71)],
               "TAIL_LAMPS",0,count=50)
    # Front grille, headlights, and hood matrix retain the opposite angle.
    front=[(float(x),float(y),70.) for x in range(-31,32,3)
           for y in range(12,28,3) if not (-19 < x < 19 and 14 < y < 20)]
    _panel(g,"TRANSIT_FRONT_MATRIX",front,"FRONT_MATRIX","#45DFFF",
           source_display_floor=.14)
    for side in (-1,1):
        s.path("TRANSIT_HEADLIGHT",[(side*17,23,71),(side*29,23,71)],
               "HEADLIGHTS",0,count=35)
    for m in g.models:
        m.attrs.update(BlackTransparency="100",PixelSize="8",Antialias="1")
        m.details.setdefault("musical_role","guitarist")
        m.details.setdefault("parade_layer",m.zone)
        m.details.setdefault("source_display_floor",.12)
    from tools.source_role_routing import configure_source_routes
    configure_source_routes(g.models)
    return allocate(g),None
