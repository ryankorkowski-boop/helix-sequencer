"""Export source-bound singer clocks and an explicitly unverified review timeline.

The VAD value, when present, measures speech presence, not singer identity.
Missing probabilities stay null. No confidence is invented from energy.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import soundfile as sf

from models.band_sampler_logic import SHAPE_NAMES
from tools.phoneme_source import digest

LANES = (('lead', 'estimated_lead'), ('backing', 'estimated_backing'))


def export(audio: Path, fixture: Path, output: Path) -> dict:
    audio, fixture, output = map(Path, (audio, fixture, output))
    receipt = json.loads((fixture/'diagnostic.json').read_text())
    clocks = fixture/'acoustic_vocal_clocks.npz'
    if receipt.get('audio_sha256') != digest(audio) or receipt.get('clock_sha256') != digest(clocks):
        raise ValueError('Vocal diagnostic source or clock checksum mismatch')
    duration = sf.info(audio).duration
    hop = float(receipt['clock_hop_seconds'])
    if hop != .01:
        raise ValueError('Unsupported vocal clock; expected measured 10ms frames')
    lanes = {}
    with np.load(clocks, allow_pickle=False) as data:
        for role, prefix in LANES:
            energy, shapes = data[prefix+'_energy'], data[prefix+'_shapes']
            probability = data.get(prefix+'_presence_probability')
            if (energy.ndim != 1 or energy.shape != shapes.shape or not len(energy)
                    or abs(len(energy)*hop-duration) > .02
                    or not np.isfinite(energy).all() or np.any((energy < 0) | (energy > 1))
                    or not np.isfinite(shapes).all() or np.any(shapes != np.floor(shapes))
                    or np.any((shapes < 0) | (shapes >= len(SHAPE_NAMES)))):
                raise ValueError('Invalid vocal diagnostic clock')
            if probability is not None and (probability.shape != energy.shape
                    or not np.isfinite(probability).all() or np.any((probability < 0) | (probability > 1))):
                raise ValueError('Invalid VAD probability clock')
            active = (energy > 0) & (shapes != SHAPE_NAMES.index('REST'))
            # Match the exact face export: an inactive mouth always renders REST.
            names = [SHAPE_NAMES[int(s)] if a else 'REST' for s, a in zip(shapes, active)]
            lanes[role] = dict(energy=energy.copy(), active=active, names=names,
                               probability=None if probability is None else probability.copy())
    if len(lanes['lead']['energy']) != len(lanes['backing']['energy']):
        raise ValueError('Singer clocks have different lengths')
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output/'Vocal_Timeline.csv'
    fields = ['time_seconds'] + [role+'_'+key for role, _ in LANES
                                for key in ('active', 'phoneme_estimate', 'energy', 'speech_vad_probability')]
    with csv_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for i in range(len(lanes['lead']['energy'])):
            row = dict(time_seconds=f'{i*hop:.3f}')
            for role, lane in lanes.items():
                row.update({role+'_active': int(lane['active'][i]), role+'_phoneme_estimate': lane['names'][i],
                            role+'_energy': float(lane['energy'][i]),
                            role+'_speech_vad_probability': '' if lane['probability'] is None else float(lane['probability'][i])})
            writer.writerow(row)
    summary = dict(schema='helix.vocal-review-timeline.v1', source_audio_sha256=digest(audio),
        source_clock_sha256=digest(clocks), source_duration_seconds=duration, hop_seconds=hop,
        independent_backing_verified=False, exact_phoneme_boundaries_verified=False,
        confidence_meaning='Speech VAD probability where retained; not calibrated singing or singer identity confidence. Blank CSV fields mean unavailable.',
        lanes={})
    for role, lane in lanes.items():
        cuts = np.r_[0, np.flatnonzero(np.diff(lane['active']))+1, len(lane['active'])]
        summary['lanes'][role] = dict(active_seconds=float(np.count_nonzero(lane['active'])*hop),
            source_track_sha256=receipt['tracks'][dict(LANES)[role]]['sha256'],
            speech_vad_available=lane['probability'] is not None,
            regions=[dict(start_seconds=float(a*hop), end_seconds=float(min(b*hop, duration)),
                          active=bool(lane['active'][a])) for a, b in zip(cuts[:-1], cuts[1:])])
    summary['timeline_csv_sha256'] = digest(csv_path)
    image_path = output/'Vocal_Timeline.png'
    picture = Image.new('RGB', (1280, 200), '#0c1725')
    draw = ImageDraw.Draw(picture)
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font = ImageFont.truetype(font_path, 16)
    small = ImageFont.truetype(font_path, 13)
    draw.text((18, 10), 'SOURCE-SEPARATED VOCAL ESTIMATES | identity and lexical phonemes unverified', font=font, fill='white')
    for j, (role, lane) in enumerate(lanes.items()):
        y = 60+j*50
        draw.text((18, y+6), role.title()+' estimate', font=font, fill='#eedfd0' if j == 0 else '#c9a1ff')
        draw.rectangle((180, y, 1260, y+30), fill='#1c2e42')
        for region in summary['lanes'][role]['regions']:
            if region['active']:
                x1=180+1080*region['start_seconds']/duration
                x2=180+1080*region['end_seconds']/duration
                draw.rectangle((int(x1), y, max(int(x1), int(x2)-1), y+30), fill='#e8ad6b' if j == 0 else '#a774df')
    for second in np.arange(0, duration, 5):
        x = 180+1080*second/duration
        draw.line((x, 47, x, 145), fill='#62758b')
        draw.text((x, 148), f'{second:.0f}s', font=small, fill='#c5d2df')
    draw.text((18, 178), 'Activity is measured per source. Blank confidence stays unavailable. This timeline does not certify two singers.', font=small, fill='#b6c5d5')
    picture.save(image_path)
    summary['timeline_png_sha256'] = digest(image_path)
    (output/'Vocal_Timeline.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


def attach(native_video: Path, diagnostic: Path, target: Path, *, source_audio: Path):
    """Append a diagnostic chart beneath native footage; retain its soundtrack."""
    diagnostic, target = Path(diagnostic), Path(target)
    report = json.loads((diagnostic/'Vocal_Timeline.json').read_text())
    picture = diagnostic/'Vocal_Timeline.png'
    if digest(picture) != report['timeline_png_sha256']:
        raise ValueError('Vocal timeline picture checksum mismatch')
    from tools.verify_recovery_media import verify
    native_proof = verify(native_video, source_audio, report['source_audio_sha256'])
    duration = report['source_duration_seconds']
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name('.timeline-'+uuid.uuid4().hex+'.mp4')
    try:
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-filter_complex_threads', '2',
            '-threads', '2', '-i', str(native_video), '-loop', '1', '-framerate', '20', '-i', str(picture),
            '-f', 'lavfi', '-i', 'color=c=white:s=2x100:r=20',
            '-filter_complex', '[0:v]scale=1280:720[v];[v][1:v]vstack=inputs=2[stack];'
                f'[stack][2:v]overlay=x=180+1080*t/{duration}:y=767:shortest=1[out]',
            '-map', '[out]', '-map', '0:a:0', '-t', str(duration), '-c:v', 'libx264',
            '-preset', 'fast', '-crf', '19', '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
            '-movflags', '+faststart', str(temporary)], check=True)
        output_proof = verify(temporary, source_audio, report['source_audio_sha256'])
        temporary.replace(target)
        output_proof.update(file=target.name, native_stage_footage_sha256=native_proof['sha256'],
                            diagnostic_csv_sha256=report['timeline_csv_sha256'],
                            presentation='Native xLights stage footage with appended diagnostic chart',
                            independent_backing_verified=False)
        target.with_suffix('.json').write_text(json.dumps(output_proof, indent=2)+'\n')
        return output_proof
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--native-video', type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.audio, args.fixture, args.output), indent=2))
    if args.native_video:
        attach(args.native_video, args.output, args.output/'Native_Vocal_Timeline.mp4', source_audio=args.audio)
