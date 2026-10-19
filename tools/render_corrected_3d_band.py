"""Render corrected seven-snowman 3D performance from verified Helix E14 analysis.

This uses ReviewBandPerformance.pose() with source WAV and original analyzed
events. There is no audio-reactive animation invented at export time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from models.review_3d_scene import Review3DScene
from tools.render_approval_revision import band, setup

ORDER = ('CYMBAL_LEFT', 'TOM_FLOOR', 'TOM_MID', 'KICK',
         'SNARE', 'TOM_HIGH', 'HI_HAT', 'CYMBAL_RIGHT')
E14_SHA256 = '8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171'


def preflight(root: Path, eid: str) -> dict:
    row, audio, scene, performance = setup(root, eid, scene_factory=Review3DScene)
    if eid == 'E14' and hashlib.sha256(audio.read_bytes()).hexdigest() != E14_SHA256:
        raise ValueError('Source audio identity mismatch')
    if tuple(sorted(scene.drum_centers, key=lambda key: scene.drum_centers[key][0])) != ORDER:
        raise ValueError('Kit is backwards as seen from the audience')
    if len(scene.drum_centers) != 8:
        raise ValueError('A physical drum component is missing')
    if tuple(scene.drummer_rigs) != ('left', 'right'):
        raise ValueError('Both physical drumstick rigs are required')
    if not np.allclose(scene.drum_centers['HI_HAT'][0], 1.76):
        raise ValueError('Hi-hat must be to audience right')
    if len(scene.drummer_parts) != len(ORDER):
        raise ValueError('Incomplete visible drum component mesh')
    max_keyboard_steps = {}
    moving_keyboard_frames = {}
    contact_omissions = {}
    source_note_frames=int(np.count_nonzero(performance.curves['piano_energy']>.01))
    if source_note_frames<10 or len(performance.keyboard_events)<10:
        raise ValueError('Retained source keyboard notes did not drive performance')
    for side in ('left', 'right'):
        poses=np.asarray(performance.key_hand_targets[side])
        distances=np.linalg.norm(np.diff(poses,axis=0),axis=1)
        max_keyboard_steps[side]=float(np.max(distances)) if len(distances) else 0.0
        moving_keyboard_frames[side]=int(np.count_nonzero(distances>.01))
        if max_keyboard_steps[side]>0.130001:
            raise ValueError('Keyboard windmill-speed hand gesture')
        contacts=performance.key_assignments[side]
        contact_omissions[side]=sum(
            pitch is None for i,pitch in enumerate(contacts)
            if performance.curves['piano_energy'][i]>.01)
        for i in (0, min(len(poses)-1, 100), len(poses)-1):
            rig=next(r for r in scene.rigs if r['role']=='piano' and r['side']==side)
            if np.linalg.norm(poses[i]-rig['shoulder'])>=sum(rig.get('link_lengths',(.80,.78)))-.04:
                raise ValueError('Keyboard wrist exceeds mechanical reach')
    if sum(moving_keyboard_frames.values())<20:
        raise ValueError('Keyboardist remains frozen despite real keyboard events')
    # Exercise all eight drum targets without inventing any playback events.
    for target in ORDER:
        source_side='left' if scene.drum_centers[target][0]<0 else 'right'
        scene.configure_drummer([dict(target=target,time=0.0,side=source_side,velocity=1.0)])
        scene.update_drummer(0)
        if target not in ('KICK', 'HI_HAT') and not scene.drum_contact_proof:
            raise ValueError('Drum kit component cannot be struck: '+target)
    return {'source_audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),
            'song':row['filename'],'drum_order_audience_left_to_right':ORDER,
            'kit_components':len(ORDER),'keyboard_max_step_per_50ms':max_keyboard_steps,
            'keyboard_moving_frames':moving_keyboard_frames,
            'source_keyboard_note_frames':source_note_frames,
            'keyboard_contact_omissions_reported':contact_omissions,
            'source_timed':True,'all_snowmen':True,
            'artistic_approval':'pending'}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--id',default='E14')
    parser.add_argument('--frames',type=int,default=720)
    parser.add_argument('--check-only',action='store_true')
    a=parser.parse_args()
    root=a.root.resolve()
    result=preflight(root,a.id)
    (root/'videos').mkdir(parents=True,exist_ok=True)
    (root/'videos'/'corrected_band_preflight.json').write_text(json.dumps(result,indent=2)+'\n')
    if a.check_only:
        print('CORRECTED_3D_PREFLIGHT_PASS',json.dumps(result))
    else:
        if not 1<=a.frames<=720:raise ValueError('frames outside 36s E14')
        path=band(root,a.id,frames=a.frames,scene_factory=Review3DScene)
        print('CORRECTED_3D_BAND_RENDERED',path)


if __name__=='__main__':
    main()
