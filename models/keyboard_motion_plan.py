"""Source-note keyboard motion; lights and physical contacts are separate facts."""
from __future__ import annotations
import numpy as np


def plan_keyboard_hands(held, levels, centers, rigs, *, max_step=.030,
                        max_acceleration=.010, contact_tolerance=.025):
    """Two mittens, at most two contacts, no debounce or invented notes.

    Each hand owns its half of the keybed. During gaps it hovers over the
    last key instead of repeatedly retreating to the torso. Note changes
    are selected by distance/continuity and approached with bounded inertia.
    Unreachable and excess chord notes remain illuminated but unplayed.
    Coordinates use the model's design units, one sample per 50 ms.
    """
    held=np.asarray(held);levels=np.asarray(levels,float)
    if held.ndim!=2 or held.shape!=levels.shape or not np.isfinite(levels).all():
        raise ValueError('Invalid note grid')
    if min(max_step,max_acceleration,contact_tolerance)<=0:
        raise ValueError('Motion bounds must be positive')
    centers={int(k):np.asarray(v,float) for k,v in centers.items()}
    center_x=(rigs['left']['shoulder'][0]+rigs['right']['shoulder'][0])/2
    lanes={};contacts={};diagnostics={}
    for side in ('left','right'):
        rig=rigs[side];shoulder=np.asarray(rig['shoulder'],float)
        previous=np.asarray(rig['hand'],float).copy();velocity=np.zeros(3)
        upper,lower=rig.get('link_lengths',(.80,.78))
        own=lambda x: x<=center_x if side=='left' else x>=center_x
        candidates={p:c+np.array((0,.110,.065)) for p,c in centers.items()
                    if own(c[0]) and abs(upper-lower)+.1<np.linalg.norm(c+np.array((0,.110,.065))-shoulder)<upper+lower-.1}
        lane=[];assigned=[];last_pitch=None;unplayed=0;active_frames=0
        target=previous.copy()
        for i,notes in enumerate(held):
            active={int(p) for p,v in zip(notes,levels[i]) if p>=0 and v>0}
            available=active & candidates.keys()
            pitch=None
            if available:
                # Continuity wins while a key is held. No minimum inter-onset
                # interval: fast adjacent scales are allowed at source speed.
                pitch=min(available,key=lambda p:(0 if p==last_pitch else 1,
                          np.linalg.norm(candidates[p]-previous),p))
                target=candidates[pitch].copy();last_pitch=pitch
            elif last_pitch is not None:
                target=candidates[last_pitch]+(0,.025,0)
            delta=target-previous;distance=float(np.linalg.norm(delta))
            desired=delta*min(.65,max_step/max(distance,1e-12))
            change=desired-velocity;norm=float(np.linalg.norm(change))
            velocity+=change*min(1.,max_acceleration/max(norm,1e-12))
            previous=previous+velocity
            lane.append(previous.copy())
            contact=pitch if pitch is not None and np.linalg.norm(previous-candidates[pitch])<=contact_tolerance else None
            assigned.append(contact)
            if available:
                active_frames+=1;unplayed+=int(contact is None)
        lanes[side]=np.asarray(lane);contacts[side]=assigned
        diagnostics[side]={'source_active_frames':active_frames,
                           'frames_without_contact':unplayed,
                           'contact_frames':sum(p is not None for p in assigned)}
    diagnostics['max_contacts_per_frame']=2
    diagnostics['contact_tolerance']=contact_tolerance
    diagnostics['musical_ground_truth_verified']=False
    return lanes,contacts,diagnostics
