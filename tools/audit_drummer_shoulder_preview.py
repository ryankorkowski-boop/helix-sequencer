"""Check every delivered score pulse in encoded frames and the original audio."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw
import soundfile as sf

from tools.drummer_v3_visual_masks import TARGET_OUTLINE_RGB
from tools.render_drummer_v3_preview import parse_effects, _active_targets_for_frame


def audit(video: Path, audio: Path, xsq: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    scores = json.loads(video.with_suffix('.scores.json').read_text())
    assert hashlib.sha256(video.read_bytes()).hexdigest() == scores['video_sha256']
    assert hashlib.sha256(audio.read_bytes()).hexdigest() == scores['audio_sha256']
    assert hashlib.sha256(xsq.read_bytes()).hexdigest() == scores['source_xsq_sha256']
    effects = parse_effects(xsq)
    for event in scores['scores']:
        if event['target']:
            active = _active_targets_for_frame(
                effects, event['nearest_video_frame']*1000/scores['fps'], scores['fps'])
            assert event['target'] in active, event
    proof = defaultdict(list)
    for i,e in enumerate(scores['scores']):
        proof[e['nearest_video_frame']].append((i,e))
    representative = [0.12,.78,9.69,10.01,10.32,31.11,32.36,33.3,
                      33.93,34.09,34.72,35.03,35.19,36.29,37.08]
    selected={round(t*scores['fps']):t for t in representative}
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    process=subprocess.Popen([ffmpeg,'-v','error','-i',str(video),'-map','0:v',
                              '-vf','scale=960:540','-f','rawvideo','-pix_fmt','rgb24','-'],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    evidence=[];frames=0;images={}
    try:
        while True:
            data=process.stdout.read(960*540*3)
            if not data: break
            assert len(data)==960*540*3, 'Partial decoded frame'
            rgb=np.frombuffer(data,np.uint8).reshape(540,960,3)
            for i,e in proof.get(frames,[]):
                x,y=np.round(np.array(e['response_xy'])/2).astype(int)
                core=rgb[y-1:y+2,x-1:x+2].astype(float)
                expected=np.array(TARGET_OUTLINE_RGB.get(e['target'],(235,245,255)))
                error=np.linalg.norm(core-expected,axis=2)
                visible=bool(np.count_nonzero(error<100)>=3 and core.max()>150)
                evidence.append(dict(score_index=i,frame=frames,timestamp=e['timestamp'],
                                     target=e['target'],family=e['family'],
                                     visible_encoded_response=visible,
                                     minimum_color_error=float(error.min())))
            if frames in selected:
                image=Image.fromarray(rgb.copy())
                images[frames]=image
                image.save(output/f'frame_{frames:04d}_{selected[frames]:.2f}s.jpg',quality=94)
            frames+=1
    finally:
        process.stdout.close()
    stderr=process.stderr.read().decode();code=process.wait()
    assert code==0,stderr
    assert frames==scores['frames'],(frames,scores['frames'])
    failed=[e for e in evidence if not e['visible_encoded_response']]
    assert len(evidence)==scores['score_count']
    if failed: raise AssertionError(json.dumps(failed,indent=2))
    coverage=[]
    for attack in scores['independent_source_attacks']:
        nearest=min(scores['scores'],key=lambda e:abs(e['timestamp']-attack['timestamp']))
        delta=abs(nearest['timestamp']-attack['timestamp'])
        assert delta<=.055
        coverage.append(dict(source_attack=attack['timestamp'],novelty=attack['novelty'],
                             response_timestamp=nearest['timestamp'],distance_ms=delta*1000))
    wav=output/'encoded_audio.wav'
    subprocess.run([ffmpeg,'-v','error','-y','-i',str(video),'-vn','-ar','48000','-ac','2',str(wav)],check=True)
    encoded,sr=sf.read(wav,always_2d=True);original,source_sr=sf.read(audio,always_2d=True)
    assert sr==source_sr
    n=min(len(encoded),len(original));corr=float(np.corrcoef(encoded[:n].ravel(),original[:n].ravel())[0,1])
    assert corr>.98,corr
    sheet=Image.new('RGB',(1440,300*((len(images)+2)//3)),'#070b12');draw=ImageDraw.Draw(sheet)
    for i,(frame,image) in enumerate(sorted(images.items())):
        x=(i%3)*480;y=(i//3)*300
        sheet.paste(image.resize((480,270)),(x,y))
        draw.text((x+10,y+277),f'{frame/scores["fps"]:.3f}s — actual encoded frame {frame}',fill='white')
    sheet.save(output/'encoded_hit_review.jpg',quality=95)
    result=dict(full_decode_pass=True,decoded_frames=frames,
                scored_hits=len(evidence),visible_scored_hits=len(evidence)-len(failed),
                cached_family_hits=scores['cached_family_hits'],
                physical_hits_preserved=scores['preserved_physical_hits'],
                all_physical_poses_active_at_scored_frame=True,
                unassigned_responses=scores['unassigned_responses'],
                independent_source_attacks=len(coverage),covered_source_attacks=len(coverage),
                maximum_source_attack_response_distance_ms=max(e['distance_ms'] for e in coverage),
                original_audio_zero_lag_correlation=corr,
                video_sha256=scores['video_sha256'],audio_sha256=scores['audio_sha256'],
                hit_frame_evidence=evidence,source_attack_coverage=coverage,
                limitation='All scored cues and measured novelty candidates are checked. This does not prove every audible note is detected or every inferred family label is correct. Unresolved attacks pulse the torso rather than claiming a physical tom position.')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('hit_frame_evidence','source_attack_coverage')},indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('video','audio','xsq','output'): parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();audit(args.video,args.audio,args.xsq,args.output)
