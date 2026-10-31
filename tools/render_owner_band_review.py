"""Render the six-member owner review from retained recording-bound cues.

This is the solid OpenGL/source-art band view, not a native xLights recording.
Vocal candidates remain estimates; this tool never writes a release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

import numpy as np

ROLES = ('drummer', 'bass', 'guitar', 'piano', 'lead', 'harmony')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def active_cues(cues, milliseconds):
    return [c for c in cues if c['start_ms'] <= milliseconds < c['end_ms']]


def drum_hits(cues):
    """Snare hands advance on snares only; ambiguous toms stay unresolved."""
    from tools.render_drummer_v3_preview import TARGETS
    hits, unresolved, snare = [], [], 0
    for cue in sorted(cues, key=lambda c: c['start_ms']):
        target = {'kick': TARGETS[0], 'snare': TARGETS[1],
                  'hihat': TARGETS[2], 'cymbal': TARGETS[7]}.get(cue['kind'])
        if cue['kind'] == 'tom':
            from audio.drum_classification import DrumEvent
            from mapping.drum_mapper import tom_class_for_event
            event = DrumEvent(timestamp=cue['start_ms']/1000,
                velocity=cue.get('velocity', .8), confidence=cue.get('confidence', 0),
                frequency_band_info=cue.get('frequency_band_info', {}),
                cluster_id=cue.get('cluster_id'), drum_type='tom')
            try:
                target = {'high': TARGETS[3], 'mid': TARGETS[4], 'floor': TARGETS[5]}[tom_class_for_event(event)]
            except ValueError:
                pass
        if target is None:
            unresolved.append(dict(start_ms=cue['start_ms'], kind=cue['kind']))
            continue
        side = 'right' if target in (TARGETS[3], TARGETS[7]) else 'left'
        if cue['kind'] == 'snare':
            side = 'right' if snare % 2 else 'left'
            snare += 1
        hits.append(dict(time=cue['start_ms']/1000, target=target,
                         side=side, velocity=float(cue.get('velocity', .8))))
    return hits, unresolved


def fixed_camera(width, height, elapsed):
    eye = np.array((0., 5.9, 18.0), dtype='f4')
    target = np.array((.25, 2.8, -.8))
    forward = target-eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, (0, 1, 0)); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    view = np.eye(4, dtype='f4')
    view[:3, :3] = np.vstack((right, up, -forward)); view[:3, 3] = -view[:3, :3] @ eye
    f = 1/math.tan(math.radians(44)/2); near, far = .1, 100
    projection = np.zeros((4, 4), dtype='f4')
    projection[0, 0] = f/(width/height); projection[1, 1] = f
    projection[2, 2] = (far+near)/(near-far)
    projection[2, 3] = 2*far*near/(near-far); projection[3, 2] = -1
    return projection @ view, eye


def render(source, vocals, reference, output, expected_sha256, *, seconds=None, width=1920, height=1080):
    from PIL import ImageDraw, ImageFont
    import soundfile as sf
    from models.final_band_scene import FinalBandScene
    from models.band_performance_scene import TUNINGS, matrix, line_matrix
    from models.band_motion_refinement import elbow_3d
    from models.band_instrument_logic import event_curves
    from models.keyboard_motion_plan import plan_keyboard_hands
    from models.band_sampler_logic import SHAPE_NAMES
    from models.expressive_band_face import lip_ring_mesh
    from music.note_events import NoteEvent
    from animation.articulated_source_drummer import ArticulatedDrummer
    from tools.render_drummer_v3_preview import TARGETS
    from tools.render_intricate_band_samplers import SamplerView, SAMPLER_VERTEX
    from tools.render_refined_helix_band import REFINED_FRAGMENT, DynamicDry, encoder

    source, vocals, reference, output = map(Path, (source, vocals, reference, output))
    audio = source/'media/Helix_Starred_New_Review.wav'
    if digest(audio) != expected_sha256:
        raise ValueError('Original recording identity mismatch')
    if digest(reference) != 'ec0c30bb95fc51d18488bda90980188d99b3d6e4e952500eddf41db4409e00ef':
        raise ValueError('Wrong owner-passed original V3 reference')
    duration = sf.info(audio).duration
    if seconds is not None: duration = min(duration, float(seconds))
    if duration <= 0: raise ValueError('Positive duration required')
    n = math.ceil(duration*20)
    plan_path, = (source/'sequence').glob('*.snowman_band.json')
    plan = json.loads(plan_path.read_text())['cues']
    receipt = json.loads((vocals/'diagnostic.json').read_text())
    if receipt['audio_sha256'] != expected_sha256 or digest(vocals/'acoustic_vocal_clocks.npz') != receipt['clock_sha256']:
        raise ValueError('Vocal clock identity mismatch')
    with np.load(vocals/'acoustic_vocal_clocks.npz', allow_pickle=False) as z:
        clocks = {k:z[k].copy() for k in z.files}
    scene = FinalBandScene('glacier_pier', full_keyboard=True)
    if scene.visible_roles != ROLES: raise ValueError('Six-member cast required')
    keys = {int(o['name'].rsplit('_', 1)[1]):o['matrix'][:3, 3].copy()
            for o in scene.instances if o['name'].startswith('piano_key_') and o['kind'] != 'hidden'}
    keyboard = [NoteEvent(c['start_ms']/1000, c['end_ms']/1000,
        round(c['pitch_midi']), float(c['velocity']), source='retained_production_plan')
        for c in plan['keyboardist'] if round(c['pitch_midi']) in keys]
    held, velocities, _, _ = event_curves(keyboard, n, 6, release=0)
    rigs = {r['side']:r for r in scene.rigs if r['role'] == 'piano'}
    wrists, assignments, keyboard_report = plan_keyboard_hands(held, velocities, keys, rigs,
        max_step=.030, max_acceleration=.010, anticipation_frames=12)
    hits, unresolved = drum_hits(plan['drummer'])
    player = ArticulatedDrummer(hits, natural_arms=True, cache_lighting=True)
    view = SamplerView(scene, width, height, SAMPLER_VERTEX.replace('activity[128]', 'activity[280]'), REFINED_FRAGMENT)
    view.groups.append(view.make_vao(lip_ring_mesh(), [o for o in scene.instances if o['kind'] == 'lip_ring']))
    view.camera_callback = fixed_camera; view.dry = DynamicDry(player)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.stem+'.encoding.mp4')
    writer = encoder(temporary, width, height, 20, audio, 0, duration)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', round(width/60))
    began = time.monotonic(); poses = []; snapshots = output.parent/'frames'; snapshots.mkdir(exist_ok=True)
    try:
        for i in range(n):
            t = i/20; levels = np.zeros(280, 'f4'); levels[177] = .7
            voice = []
            for k, role in enumerate(('lead', 'harmony')):
                lane = ('estimated_lead', 'estimated_backing')[k]; j = i*5
                energy = float(clocks[lane+'_energy'][j]); index = int(clocks[lane+'_shapes'][j]) if energy > 0 else 0
                shape = SHAPE_NAMES[index]; scene.update_singer_mouth(role, shape, energy)
                for part in ('cavity', 'lips', 'tongue', 'teeth'):
                    scene.instances[scene.expressive_mouths[role][part]]['matrix'][:3, :2] *= .42
                levels[3+k] = energy*.6; voice.append(dict(shape=shape, energy=energy))
            for role, first in (('bass', 13), ('guitar', 17)):
                cues = active_cues(plan[{'bass':'bassist', 'guitar':'guitarist'}[role]], t*1000)
                cues = [c for c in cues if c['kind'] != 'chord_change']
                routes = []
                for c in cues:
                    pitch = round(c.get('pitch_midi', 40))
                    choices = [(s, pitch-p, pitch) for s, p in enumerate(TUNINGS[role]) if 0 <= pitch-p <= 24]
                    if choices: routes.append((c, min(choices, key=lambda a:abs(a[1]-4))))
                gain = max((float(c.get('velocity', .6)) for c in cues), default=0)
                for c, route in routes: levels[first+route[0]] = max(levels[first+route[0]], float(c.get('velocity', .6)))
                levels[int(role == 'guitar')] = gain*.5
                for string in range(len(scene.strings[role])): scene.vibrate(role, string, float(levels[first+string]), t)
                for rig in [r for r in scene.rigs if r['role'] == role]:
                    hand = rig['hand'].copy()
                    if cues and rig['side'] in ('pluck', 'strum'):
                        age = (t*1000-max(c['start_ms'] for c in cues))/1000
                        hand[1] -= .18*gain*max(0, 1-age/.2)
                    if routes and rig['side'] == 'finger':
                        route = routes[-1][1]
                        hand = scene.guitar_contact(*route[:2]) if role == 'guitar' else scene.bass_contact(*route[:2])
                    shoulder = rig['shoulder']; elbow = elbow_3d(shoulder, hand, *rig['link_lengths'], (-.8, -.2, .8))
                    a, b, c = rig['ids']; scene.instances[a]['matrix'] = line_matrix(shoulder, elbow, .046)
                    scene.instances[b]['matrix'] = line_matrix(elbow, hand, .046); scene.instances[c]['matrix'] = matrix(hand, (.10, .075, .08))
            for pitch, value in zip(held[i], velocities[i]):
                if pitch >= 0: levels[192+int(pitch)-21] = value
            for side, rig in rigs.items():
                hand = wrists[side][i]; shoulder = rig['shoulder']
                elbow = elbow_3d(shoulder, hand, *rig['link_lengths'], (-.8 if side == 'left' else .8, -.2, .8))
                a, b, c = rig['ids']; scene.instances[a]['matrix'] = line_matrix(shoulder, elbow, .046)
                scene.instances[b]['matrix'] = line_matrix(elbow, hand, .046); scene.instances[c]['matrix'] = matrix(hand, (.10, .075, .08))
            lighting = np.zeros(8, 'f4'); strikes = np.zeros(8, 'f4')
            for hit in hits:
                age = t-hit['time']
                if 0 <= age < .30:
                    slot = TARGETS.index(hit['target']); lighting[slot] = max(lighting[slot], hit['velocity']*math.exp(-age/.10))
                    strikes[slot] = max(strikes[slot], float(age < .05))
            levels[5:13] = lighting
            # Source roles own separate stage regions; no beat-only global pulse.
            for slot in range(64, 112): levels[slot] = float(levels[[0, 1, 2, 3, 4, 5, 6, 7][slot % 8]])*.7
            levels[2] = float(velocities[i].max())*.5
            view.dry.time = t
            image = view.frame(levels, lighting, strikes, 0, t, t)
            draw = ImageDraw.Draw(image); draw.rectangle((0, 0, width, round(height*.055)), fill='#07111E')
            draw.text((24, 12), 'HELIX / SIX-MEMBER SNOWMAN BAND / REAL STARRED AUDIO', font=font, fill='#DCEBF4')
            writer.stdin.write(image.tobytes())
            poses.append(dict(frame=i, seconds=t, voices=voice,
                              keys={side:assignments[side][i] for side in rigs}))
            if i in {0, 10, 20, n//4, n//2, 3*n//4, n-1}: image.save(snapshots/f'band_{i:05}.jpg', quality=94)
            if i % 100 == 0: print('BAND_FRAME', i, n, round(time.monotonic()-began, 1), flush=True)
    except BaseException:
        writer.stdin.close(); writer.terminate(); writer.wait(); temporary.unlink(missing_ok=True); raise
    finally:
        if not writer.stdin.closed: writer.stdin.close()
        view.close()
    if writer.wait(): raise RuntimeError('Band encoder failed')
    temporary.replace(output)
    result = dict(schema='helix.owner-six-band-review.v1', file=output.name, sha256=digest(output),
        frames=n, fps=20, source_audio_sha256=expected_sha256, source_plan_sha256=digest(plan_path),
        passed_reference_sha256=digest(reference), visible_roles=list(scene.visible_roles),
        renderer='OpenGL solid meshes plus preserved original planar V3 artwork', native_xlights=False,
        camera='fixed front', keyboard=keyboard_report, unresolved_drums=unresolved,
        drum_motion_rejections=player.motion_rejections, hand_reassignments=player.hand_reassignments,
        voices=receipt, frame_evidence=poses, exact_lexical_phonemes_verified=False,
        independent_acoustic_singer_identity_verified=False, release_acceptance=False)
    output.with_suffix('.json').write_text(json.dumps(result, indent=2, default=lambda x:int(x))+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'vocals', 'reference', 'output'): p.add_argument(name, type=Path)
    p.add_argument('--expected-sha256', required=True); p.add_argument('--seconds', type=float)
    p.add_argument('--width', type=int, default=1920); p.add_argument('--height', type=int, default=1080)
    a = p.parse_args()
    render(a.source, a.vocals, a.reference, a.output, a.expected_sha256, seconds=a.seconds, width=a.width, height=a.height)
