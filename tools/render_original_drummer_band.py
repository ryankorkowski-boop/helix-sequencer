"""Verified original V3 source-art drummer + current six Helix snowman performers.

The original drummer is the exact authored planar xModel/source-art rig mounted
in the 3D show, NOT the newer Review3DScene geometric reconstruction.
Source-bound sound and time remain unchanged. The existing musical keyboard
wrist guard and retained screened source notes still apply.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from animation.articulated_source_drummer import ArticulatedDrummer
from models.review_snowman_scene import ReviewSnowmanScene
from tools.render_approval_revision import band, setup
from tools.render_drummer_v3_preview import SOURCE, XMODEL, TARGETS, load_component_masks, validate_xmodel_targets
from tools.render_refined_helix_band import physical_hits
from tools.drummer_v3_visual_masks import load_spec, exact_geometry

EXPECTED_E14_WAV_SHA256 = "8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171"


def preflight(root: Path, eid: str) -> dict:
    row, audio, scene, performance = setup(root, eid, scene_factory=ReviewSnowmanScene)
    if eid == 'E14' and hashlib.sha256(audio.read_bytes()).hexdigest() != EXPECTED_E14_WAV_SHA256:
        raise ValueError("Expected original hardKor E14 audio is missing")
    if hasattr(scene, 'configure_drummer') or not hasattr(scene, 'dry_drummer_corners'):
        raise ValueError("This is not the original authored 2D source-art drummer mounted in the 3D show")

    validate_xmodel_targets()
    source, masks = load_component_masks()
    spec = load_spec()
    geometry = exact_geometry(source, spec)
    for name in TARGETS:
        if name not in masks:
            raise ValueError("Original V3 drum surface missing: " + name)
    if len(TARGETS) != 8:
        raise ValueError("Original source artwork missing drum component contracts")

    drummer_sequence = root / 'sources' / eid / 'drummer.xsq'
    hits = physical_hits(drummer_sequence)
    drummer = ArticulatedDrummer(hits, natural_arms=True, cache_lighting=True)
    if len(drummer.hits) == 0:
        raise ValueError("The original drummer received no authentic source hits")
    if not drummer.source.size == source.size:
        raise ValueError("Original source art was silently substituted")
    if not all(side in drummer.lanes and side in drummer.roots for side in ('left','right')):
        raise ValueError("Original drumstick animation incomplete")
    hi_hat=TARGETS[2]
    hi_hat_events=[h for h in hits if h['target']==hi_hat]
    if not hi_hat_events or len(drummer.foot_hits)!=len(hi_hat_events):
        raise ValueError("Hi-hat source cues not all assigned to foot pedal")
    if any(h['target']==hi_hat for h in drummer.hits):
        raise ValueError("Hi-hat cue is incorrectly animated as a stick strike")
    for cue in hi_hat_events[:min(8,len(hi_hat_events))]:
        drummer.frame(cue['time'],active=(hi_hat,))
        if not drummer.last_hi_hat_foot_down:
            raise ValueError("Hi-hat light and foot depression are not simultaneous")
    drummer.frame(-1,active=())
    if drummer.last_hi_hat_foot_down:
        raise ValueError("Hi-hat pedal depressed without a source hit")
    # Exact original-snare contact remains the source of truth. Inspect
    # anatomical-left/screen-right elbow at the hit rather than judging from
    # a general animation/video-success flag.
    right_snare=ArticulatedDrummer(
        [dict(time=0.,target=TARGETS[1],side='right',velocity=1.)],
        natural_arms=True,cache_lighting=True)
    if len(right_snare.hits)!=1:
        raise ValueError("Right-side original snare hit became unplayable")
    right_snare.frame(0,active=(TARGETS[1],))
    joints=right_snare.last_joints['right']
    if joints['elbow'][1]<=joints['shoulder'][1]+8.:
        raise ValueError("Screen-right snare elbow is still raised above chest")
    if joints['elbow'][0]<joints['shoulder'][0]:
        raise ValueError("Screen-right snare elbow still crosses inward")
    authored_tip,_=right_snare.targets[TARGETS[1],'right']
    if np.linalg.norm(joints['tip']-authored_tip)>1e-4:
        raise ValueError("Snare elbow change displaced authored stick contact")
    singer_scarf=next(o for o in scene.instances if o['name']=='harmony_scarf')
    singer_color=np.asarray(singer_scarf['color'],dtype=float)
    if not (singer_color[2] > singer_color[0] and singer_color[0] > singer_color[1]):
        raise ValueError("Second singer must be purple, not pink")
    if any(o['name'].startswith(('harmony_bow','harmony_eyelash')) for o in scene.instances):
        raise ValueError("Second singer should retain gender-neutral design")

    # Do not market an idle xylophonist as a solo. The only defensible
    # hits are source-screened events actually sent to a moving mallet.
    # A full-band review may legitimately contain sparse mallets. It is not
    # a mallet feature and must not claim instrument identity from hit count.
    for hit in performance.mallet_schedule:
        if not 0<=hit['time']<performance.n/20 or hit['pitch'] not in scene.bars:
            raise ValueError("Mallet schedule not playable by this model")
    # Validate the actual full source timeline, including anticipation/recovery.
    for frame in range(performance.n):
        for side in ('left','right'):
            drummer._pose(side,frame/20)
            joint=drummer.last_joints[side]
            upper,lower=drummer.lengths[side]
            if not (np.isclose(np.linalg.norm(joint['elbow']-joint['shoulder']),upper)
                    and np.isclose(np.linalg.norm(joint['wrist']-joint['elbow']),lower)):
                raise ValueError('Drummer links changed length during transit')
    moving={}
    key_events=len(performance.keyboard_events)
    if key_events < 10 or int(np.count_nonzero(performance.curves['piano_energy'] > .01)) < 10:
        raise ValueError("Keyboard source note lane not active")
    for side in ('left','right'):
        p=np.asarray(performance.key_hand_targets[side])
        steps=np.linalg.norm(np.diff(p, axis=0),axis=1)
        moving[side]=int(np.count_nonzero(steps > .01))
        if len(steps) and float(np.max(steps)) > .045001:
            raise ValueError("Keyboard wrist windmill-speed movement is back")
    if sum(moving.values()) < 20:
        raise ValueError("Keyboardist animation is frozen")

    files = {
        'source_art': SOURCE,
        'source_xmodel': XMODEL,
        'authored_pose_spec': SOURCE.parents[1] / 'drummer_v3_pose_spec.json',
    }
    return {
        'identity': 'original_HX_SNOWMAN_DRUMMER_V3_source_art',
        'original_2d_art_mounted_in_3d': True,
        'replacement_3d_drum_geometry': False,
        'original_assets_sha256': {key: hashlib.sha256(p.read_bytes()).hexdigest() for key,p in files.items()},
        'source_audio_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(),
        'source_drummer_xsq_sha256': hashlib.sha256(drummer_sequence.read_bytes()).hexdigest(),
        'original_components': list(TARGETS),
        'original_drum_hits_from_source': len(hits),
        'original_playable_arm_hits': len(drummer.hits),
        'original_rejected_unplayable_hits': len(drummer.motion_rejections),
        'drum_transit_reach_adjustments':len(drummer.motion_adjustments),
        'drum_motion_rejections':drummer.motion_rejections,
        'screen_right_snare_elbow_pose_verified': True,
        'screen_right_snare_original_tip_preserved': True,
        'kick_surface_events': len(drummer.kick_hits),
        'kick_physical_beater_verified': False,
        'hi_hat_source_hits': len(hi_hat_events),
        'hi_hat_stick_strikes': 0,
        'hi_hat_foot_only': True,
        'second_singer_accent': '#8653D9',
        'second_singer_gender_ambiguous': True,
        'keyboard_note_events': key_events,
        'keyboard_motion_report': performance.keyboard_motion_report,
        'mallet_contacts_scheduled': len(performance.mallet_schedule),
        'mallet_feature_qualified': False,
        'mallet_instrument_identity_verified': False,
        'mallet_source_times': [round(hit['time'],2) for hit in performance.mallet_schedule],
        'keyboard_moving_frames': moving,
        'keyboard_wrist_step_limit': .045,
        'camera_mode': 'fixed_audience_front_all_frames',
        'performers': list(scene.visible_roles),
        'review_approval': 'pending',
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--id',default='E14')
    p.add_argument('--frames',type=int,default=720)
    p.add_argument('--check-only',action='store_true')
    a=p.parse_args()
    root=a.root.resolve()
    result=preflight(root,a.id)
    out=root/'videos'
    out.mkdir(parents=True,exist_ok=True)
    (out/'original_drummer_provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    print('ORIGINAL_SOURCE_ART_DRUMMER_VERIFIED',json.dumps(result),flush=True)
    if a.check_only:return
    if not 1<=a.frames<=720:
        raise ValueError("Only authentic E14 36-second excerpt is supported")
    # No showcase camera theatrics. One stationary audience-front camera
    # for every rendered frame, with all seven performers in context.
    from tools import render_approval_revision as stage
    original_camera=stage.camera
    frozen=original_camera(a.id,drummer3d=False)
    stage.camera=lambda eid,drummer3d=False: (lambda w,h,t: frozen(w,h,0.0))
    try:
        result=stage.band(root,a.id,frames=a.frames,scene_factory=ReviewSnowmanScene)
    finally:
        stage.camera=original_camera
    print('ORIGINAL_DRUMMER_FULL_BAND_MP4',result,flush=True)


if __name__=='__main__':
    main()

