"""Decode actual stage pixels; ignore titles and fixed-camera black margins."""
from __future__ import annotations
import subprocess
import numpy as np


def stage_motion(frames):
    frames=np.asarray(frames,dtype=np.int16)
    if frames.ndim!=4 or len(frames)<3 or frames.shape[-1]!=3:
        raise ValueError('Need at least three RGB frames')
    _,h,w,_=frames.shape
    # Normalized fixed-front stage region. Excludes both timestamp/title bands.
    stage=frames[:,int(h*.40):int(h*.82),int(w*.17):int(w*.83)]
    bright=(stage.max(axis=3)>30).mean(axis=(1,2))
    if np.any(bright<.01):
        bad=np.flatnonzero(bright<.01)
        raise ValueError(f'Blank stage frame: {len(bad)} sampled frames, first indices {bad[:12].tolist()}, minimum stage visibility {float(bright.min()):.5f}')
    delta=np.abs(np.diff(stage,axis=0)).max(axis=3)
    changed=(delta>12).mean(axis=(1,2))
    # Local articulated movement need not change the whole image's mean by 3.
    # Codec noise or a changing source-time label is not evidence of motion.
    moving=int(np.count_nonzero(changed>.002))
    if moving<max(2,int(len(changed)*.10)):
        raise ValueError(f'Frozen stage pixels: {moving}/{len(changed)} moving transitions, max changed fraction {float(changed.max()):.6f}, threshold {max(2,int(len(changed)*.10))}')
    return {'sampled_frames':len(frames),'moving_transitions':moving,
            'max_stage_changed_fraction':float(changed.max()),
            'min_visible_stage_fraction':float(bright.min()),
            'per_instrument_contacts_verified':False}


def verify_fixed_camera_video(path):
    raw=subprocess.check_output(['ffmpeg','-v','error','-xerror','-i',str(path),
        '-vf','fps=4,scale=640:360','-an','-f','rawvideo','-pix_fmt','rgb24','-'],timeout=300)
    frame_bytes=640*360*3
    if not raw or len(raw)%frame_bytes:raise ValueError('Incomplete decoded frames')
    return stage_motion(np.frombuffer(raw,dtype=np.uint8).reshape(-1,360,640,3))
