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

    moving={}
    key_events=len(performance.keyboard_events)
    if key_events < 10 or int(np.count_nonzero(performance.curves['piano_energy'] > .01)) < 10:
        raise ValueError("Keyboard source note lane not active")
    for side in ('left','right'):
        p=np.asarray(performance.key_hand_targets[side])
        steps=np.linalg.norm(np.diff(p, axis=0),axis=1)
        moving[side]=int(np.count_nonzero(steps > .01))
        if len(steps) and float(np.max(steps)) > .130001:
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
        'keyboard_note_events': key_events,
        'keyboard_moving_frames': moving,
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
    # Restore a dedicated view of the original drummer at seconds 29-33.
    # This only changes the review camera, never event timing or model geometry.
    from tools import render_approval_revision as stage
    original_camera=stage.camera
    stage.camera=lambda eid,drummer3d=False: original_camera(eid,drummer3d=True)
    try:
        result=stage.band(root,a.id,frames=a.frames,scene_factory=ReviewSnowmanScene)
    finally:
        stage.camera=original_camera
    print('ORIGINAL_DRUMMER_FULL_BAND_MP4',result,flush=True)


if __name__=='__main__':
    main()
