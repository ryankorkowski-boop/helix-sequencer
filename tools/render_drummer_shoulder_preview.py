"""Dry-source shoulder review with explicit coverage of unresolved attacks.

The accepted XSQ controls the original physical poses. Source-bound detections
without a physical position get a white torso pulse, not an invented tom stroke.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

import imageio.v2 as imageio
import imageio_ffmpeg
import librosa
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from scipy.signal import find_peaks
import soundfile as sf

from animation.cymbal_lighting import cymbal_level
from tools.drummer_v3_visual_masks import load_spec, TARGET_OUTLINE_RGB, idle_art_key
from tools.render_drummer_v3_preview import (
    TARGETS, LABELS, load_component_masks, compose_lighting, _content_crop,
    parse_effects, parse_snare_hands, parse_cymbal_hits,
    _active_targets_for_frame, snare_hand_for_frame,
)

WIDTH, HEIGHT, FPS = 1920, 1080, 60
PREFIX = "HX_SNOWMAN_DRUMMER_V3_"


def source_attacks(audio: Path) -> list[dict]:
    """Independent positive spectral novelty; avoid counting ringing RMS peaks."""
    y, sr = sf.read(audio, always_2d=True)
    y = librosa.resample(y.mean(axis=1), orig_sr=sr, target_sr=22050)
    novelty = librosa.onset.onset_strength(
        y=y, sr=22050, hop_length=110, n_fft=1024, max_size=3)
    peaks, _ = find_peaks(novelty, distance=18, prominence=1.5)
    return [dict(timestamp=float(p * 110 / 22050),
                 novelty=float(novelty[p])) for p in peaks]


def score_schedule(report: dict, raw: dict, attacks: list[dict]) -> list[dict]:
    assert report['analysis']['audio_sha256'] == raw['audio_sha256']
    scheduled = [e for e in report['event_audit'] if e['scheduled']]
    used = set()
    scores = []
    for event in raw['events']:
        matching = [(i, e) for i, e in enumerate(scheduled)
                    if i not in used and e['type'] == event['drum_family']
                    and abs(e['timestamp']-event['timestamp']) < .021]
        target = None
        if matching:
            i, match = min(matching, key=lambda pair:
                           abs(pair[1]['timestamp']-event['timestamp']))
            used.add(i)
            target = match['physical_component']
        scores.append(dict(timestamp=event['timestamp'], target=target,
                           family=event['drum_family'],
                           confidence=event['confidence'],
                           provenance='cached_family_detection',
                           source_onset_index=event['source_onset_index'],
                           uncertainty=None if target else 'physical_position_unresolved'))
    assert len(used) == len(scheduled), 'Accepted physical event lost in score schedule'
    # Source-only novelty candidates remain untyped, even if a nearby family
    # detector could be guessed. They are visibly distinguished in this review.
    for attack in attacks:
        if min(abs(e['timestamp']-attack['timestamp']) for e in scores) > .055:
            scores.append(dict(timestamp=attack['timestamp'], target=None,
                               family='source', confidence=None,
                               provenance='independent_source_novelty',
                               novelty=attack['novelty'],
                               uncertainty='family_and_position_unresolved'))
    return sorted(scores, key=lambda e: e['timestamp'])


def pulse_scores(scores: list[dict], time: float, fps: int = FPS) -> list[dict]:
    return [e for e in scores if -0.5/fps <= time-e['timestamp'] < .075]


def render(audio: Path, xsq: Path, report_path: Path, raw_path: Path,
           output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    report, raw = [json.loads(p.read_text()) for p in (report_path, raw_path)]
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    assert digest == raw['audio_sha256'] == report['analysis']['audio_sha256']
    attacks = source_attacks(audio)
    scores = score_schedule(report, raw, attacks)
    source, masks = load_component_masks()
    effects = parse_effects(xsq)
    hands = parse_snare_hands(xsq)
    cymbals, frame_ms = parse_cymbal_hits(xsq)
    crop = _content_crop(source)
    scale = min(1400/(crop[2]-crop[0]), 840/(crop[3]-crop[1]))
    size = (round((crop[2]-crop[0])*scale), round((crop[3]-crop[1])*scale))
    origin = ((WIDTH-size[0])//2-95, 138+(840-size[1])//2)

    def project(point):
        return [round(origin[0]+(point[0]*(source.width-1)-crop[0])*scale),
                round(origin[1]+(point[1]*(source.height-1)-crop[1])*scale)]

    spec = load_spec()
    zones = {z['id']: z for z in spec['zones']}
    positions = {}
    for target in spec['lighting_targets']:
        strikes = [zones[a]['strike'] for a in target['actuators']
                   if zones[a].get('strike')]
        if strikes:
            p = strikes[0]['contact']
        else:
            pts = np.array(zones[target['surface']]['commands'][0]['points'])
            p = pts.mean(axis=0)
        positions[PREFIX+target['id']] = project(p)
    positions[None] = project([.515, .465])
    for event in scores:
        event['response_xy'] = positions[event['target']]
        event['nearest_video_frame'] = round(event['timestamp']*FPS)
    base_torso = ImageEnhance.Brightness(masks[idle_art_key()].convert('RGB')).enhance(1.8)
    duration = sf.info(audio).duration
    frames = round(duration*FPS)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 25)
    title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 38)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    silent = output.with_suffix('.silent.mp4')
    writer = imageio.get_writer(silent, fps=FPS, codec='libx264',
                               ffmpeg_params=['-crf','19','-pix_fmt','yuv420p'],
                               macro_block_size=None)
    cache = {}
    counts = Counter()
    cursor = 0
    try:
        for index in range(frames):
            time = index/FPS
            active = _active_targets_for_frame(effects,time*1000,FPS)
            hand = snare_hand_for_frame(hands,time*1000,FPS)
            levels = {k:round(cymbal_level(v,time*1000,frame_ms=frame_ms,
                                          nearest_ms=500/FPS)*20)/20 for k,v in cymbals.items()}
            key = (tuple(sorted(active)), hand, tuple(sorted(levels.items())))
            if key not in cache:
                if len(cache)>300: cache.clear()
                cache[key] = compose_lighting(source,masks,active,
                                             snare_hand=hand,cymbal_levels=levels)
            lit = cache[key]
            pulses = pulse_scores(scores,time)
            if any(e['target'] is None for e in pulses):
                lit = Image.composite(base_torso,lit.convert('RGB'),masks['__preview_body__'])
            canvas = Image.new('RGB',(WIDTH,HEIGHT),'#060a12')
            canvas.paste(lit.crop(crop).resize(size,Image.Resampling.LANCZOS),origin)
            draw = ImageDraw.Draw(canvas)
            draw.text((44,26),'SNOWMAN DRUMMER  /  NATURAL SHOULDERS',font=title_font,fill='#edf4ff')
            draw.text((46,79),'Dry Drum Test · original strike timing · outward, lower arm anchors',font=font,fill='#aebdce')
            while cursor<len(scores) and scores[cursor]['timestamp']<=time+.5/FPS:
                event=scores[cursor]
                counts[event['target'] or 'unassigned']+=1
                cursor+=1
            draw.text((1540,162),f'HITS: {cursor}',font=title_font,fill='white')
            draw.text((1540,216),f'{time:05.2f} / {duration:.2f}s',font=font,fill='#aebdce')
            for row,target in enumerate([*TARGETS,'unassigned']):
                y=305+row*65
                label=LABELS.get(target,'UNASSIGNED')
                color=TARGET_OUTLINE_RGB.get(target,(230,236,255))
                draw.text((1540,y),label,font=font,fill=color)
                draw.text((1810,y),str(counts[target]),font=font,fill='white')
                on=any((e['target'] or 'unassigned')==target for e in pulses)
                draw.rounded_rectangle((1505,y+4,1524,y+24),radius=3,
                                       fill=color if on else '#202938')
            for event in pulses:
                px,py=event['response_xy'];age=max(0,time-event['timestamp'])
                radius=round(11+age*160)
                color=TARGET_OUTLINE_RGB.get(event['target'],(235,245,255))
                draw.ellipse((px-radius,py-radius,px+radius,py+radius),outline=color,width=4)
                draw.ellipse((px-4,py-4,px+4,py+4),fill=color)
            draw.text((44,1012),'Each scored hit pulses. Unassigned attacks flash the torso; no physical tom position is guessed.',
                      font=small,fill='#b4c0d0')
            writer.append_data(np.asarray(canvas))
            if index % 600 == 0: print(f'rendered {index}/{frames}',flush=True)
    finally:
        writer.close()
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(silent),
                    '-i',str(audio),'-map','0:v','-map','1:a','-c:v','copy',
                    '-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(output)],check=True)
    silent.unlink()
    result=dict(audio_sha256=digest,source_duration=duration,frames=frames,fps=FPS,
                width=WIDTH,height=HEIGHT,cached_family_hits=len(raw['events']),
                preserved_physical_hits=report['event_count'],
                score_count=len(scores),unassigned_responses=sum(e['target'] is None for e in scores),
                independent_source_attacks=attacks,scores=scores,
                scope='Physical poses from original accepted XSQ; unresolved positions and source-only candidates are labelled torso pulses.',
                video_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                video_bytes=output.stat().st_size,
                source_xsq_sha256=hashlib.sha256(xsq.read_bytes()).hexdigest())
    output.with_suffix('.scores.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('scores','independent_source_attacks')},indent=2))
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('audio','xsq','report','raw','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    render(args.audio,args.xsq,args.report,args.raw,args.output)
