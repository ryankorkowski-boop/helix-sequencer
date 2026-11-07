"""Six-up static concept-art movies with verified 30-second source excerpts."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'showcase/concepts/2026_10_09_mesmerizing'
SETS = {'A': list(range(63, 69)), 'B': list(range(77, 83))}


def run(args):
    subprocess.run(args, check=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                              '-show_format', '-of', 'json', str(path)]))


def source_songs():
    earlier = ROOT / 'evidence/showcase_audio/source'
    rows = [('Wire Tree', earlier / '1-Wire-Tree.mp3'),
            ('Tinsel Sawtooth', earlier / '2-Tinsel-Sawtooth-1-.mp3'),
            ('Frostbitten Fingerboard', earlier / '3-Frostbitten-Fingerboard-1-.mp3'),
            ('Holly Steel Run', earlier / '4-Holly-Steel-Run-1-.mp3'),
            ('Bell Circuit Carol', earlier / '5-Bell-Circuit-Carol-1-.mp3'),
            ('Helix Audiolights', ROOT / 'Helix Audiolights.mp3')]
    titles = ['Who Knew', '49', 'Candy Cane Chaos', 'Phoneme Test Hook', 'Festivus']
    rows += [(title, ROOT / f'outputs/Snowman_Ensemble/shows/{i:02}_band/media/song.mp3')
             for i, title in enumerate(titles, 1)]
    songs = []
    for i, (title, path) in enumerate(rows, 1):
        duration = float(probe(path)['format']['duration'])
        start = math.floor(min(max(0, duration * .35), duration - 30) * 20) / 20
        songs.append({'id': i, 'title': title, 'path': str(path), 'sha256': digest(path),
                      'source_duration_seconds': duration, 'start_seconds': start,
                      'duration_seconds': 30})
    # Account for every distinct MP3 already in this project, including copies in shows.
    all_hashes = {digest(p) for p in ROOT.rglob('*.mp3') if '.git' not in p.parts}
    assert all_hashes == {s['sha256'] for s in songs}
    return songs


def base_movie(key, output, concepts):
    ids = SETS[key]
    boards = [ART / concepts[n]['image'] for n in ids[::2]]
    args = ['ffmpeg', '-v', 'error', '-y', '-filter_complex_threads', '1']
    for p in boards:
        args += ['-loop', '1', '-framerate', '20', '-i', str(p)]
    filters = []
    for i in range(3):
        filters += [f'[{i}:v]split=2[l{i}][r{i}]',
                    f'[l{i}]crop=iw/2:ih:0:0,scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2:color=0x080e19[v{2*i}]',
                    f'[r{i}]crop=iw/2:ih:iw/2:0,scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2:color=0x080e19[v{2*i+1}]']
    title = output / f'set_{key}_title.txt'
    title.write_text(f'HELIX  |  SIX CONCEPTS  |  SET {key}  |  #{ids[0]}–{ids[-1]}')
    footer = output / 'artwork_disclosure.txt'
    footer.write_text('STATIC CONCEPT ART WITH MUSIC  •  Not native xLights playback or audio-reactive animation')
    filters += [''.join(f'[v{i}]' for i in range(6)) +
                'xstack=inputs=6:layout=0_0|640_0|1280_0|0_480|640_480|1280_480,'
                'pad=1920:1080:0:80:color=0x080e19,'
                f'drawtext=textfile={title}:fontcolor=white:fontsize=25:x=24:y=10,'
                f'drawtext=textfile={footer}:fontcolor=0x9eb8c8:fontsize=20:x=24:y=1048[v]']
    movie = output / f'_Set_{key}_Silent_Base.mp4'
    run(args + ['-filter_complex', ';'.join(filters), '-map', '[v]', '-t', '30', '-an',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-threads', '2',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(movie)])
    return movie


def audio_samples(path, start=0, seconds=30):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(start), '-i', str(path),
                                    '-t', str(seconds), '-vn', '-ac', '1', '-ar', '16000',
                                    '-f', 'f32le', '-'])
    return np.frombuffer(data, dtype='<f4')


def inspect(movie, seconds):
    p = probe(movie)
    v = next(s for s in p['streams'] if s['codec_type'] == 'video')
    a = next(s for s in p['streams'] if s['codec_type'] == 'audio')
    assert (v['codec_name'], v['pix_fmt'], v['width'], v['height'], v['r_frame_rate']) == (
        'h264', 'yuv420p', 1920, 1080, '20/1')
    assert int(v['nb_frames']) == seconds * 20
    assert abs(float(p['format']['duration']) - seconds) < .08
    assert a['codec_name'] == 'aac'
    run(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(movie), '-f', 'null', '-'])
    return {'seconds': seconds, 'frames': int(v['nb_frames']), 'full_decode_passed': True,
            'sha256': digest(movie), 'bytes': movie.stat().st_size}


def song_movie(key, base, song, output):
    title = output / f'song_{song["id"]:02}_title.txt'
    title.write_text(f'{song["title"]}  |  original audio {song["start_seconds"]:.2f}–{song["start_seconds"]+30:.2f}s')
    slug = song['title'].replace(' ', '_')
    movie = output / f'Set_{key}_{song["id"]:02}_{slug}_30s.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-threads', '1', '-i', str(base), '-ss', str(song['start_seconds']),
         '-i', song['path'], '-vf', f'drawtext=textfile={title}:fontcolor=0xffd495:fontsize=23:x=24:y=44',
         '-map', '0:v:0', '-map', '1:a:0', '-t', '30', '-c:v', 'libx264', '-preset', 'veryfast',
         '-crf', '20', '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000',
         '-b:a', '192k', '-movflags', '+faststart', str(movie)])
    proof = inspect(movie, 30)
    source = audio_samples(song['path'], song['start_seconds'])
    encoded = audio_samples(movie)
    n = min(len(source), len(encoded))
    correlation = float(np.corrcoef(source[:n], encoded[:n])[0, 1])
    assert np.isfinite(correlation) and correlation > .98, correlation
    return {'file': movie.name, 'set': key, 'concept_ids': SETS[key], 'song': song,
            'source_soundtrack_correlation': correlation, **proof}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/Concept_Art_Comparisons')
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    concepts = {c['id']: c for c in json.loads((ART / 'concepts.json').read_text())['concepts']}
    songs = source_songs()
    rows = []
    for key in SETS:
        base = base_movie(key, output, concepts)
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda song: song_movie(key, base, song, output), songs))
        rows += results
        print(f'Set {key}: {len(results)} clips verified', flush=True)
        # Only the delivered comparisons are retained as MP4s; bases are transient inputs.
        base.unlink()
    reels = []
    for key in SETS:
        chosen = [r for r in rows if r['set'] == key]
        listing = output / f'set_{key}_concat.txt'
        listing.write_text(''.join(f"file '{r['file']}'\n" for r in chosen))
        movie = output / f'Set_{key}_All_11_Songs_Comparison.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing),
             '-c', 'copy', '-movflags', '+faststart', str(movie)])
        proof = inspect(movie, 330)
        # Rebuild one uninterrupted AAC stream from exact 30-second source segments;
        # stream-copying independent AAC encodes retains their per-clip padding.
        fixed = output / f'_Set_{key}_Continuous_Audio.mp4'
        args = ['ffmpeg', '-v', 'error', '-y', '-i', str(movie)]
        for r in chosen:
            args += ['-ss', str(r['song']['start_seconds']), '-t', '30', '-i', r['song']['path']]
        filters = [f'[{i+1}:a]aresample=48000,atrim=duration=30,asetpts=PTS-STARTPTS[a{i}]'
                   for i in range(len(chosen))]
        filters += [''.join(f'[a{i}]' for i in range(len(chosen))) +
                    f'concat=n={len(chosen)}:v=0:a=1[a]']
        run(args + ['-filter_complex', ';'.join(filters), '-map', '0:v:0', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', '330',
                    '-movflags', '+faststart', str(fixed)])
        fixed.replace(movie)
        proof = inspect(movie, 330)
        actual = audio_samples(movie, seconds=330)
        expected = np.concatenate([audio_samples(r['song']['path'], r['song']['start_seconds'])[:480000]
                                   for r in chosen])
        n = min(len(actual), len(expected))
        correlation = float(np.corrcoef(actual[:n], expected[:n])[0, 1])
        assert np.isfinite(correlation) and correlation > .98
        proof['continuous_source_soundtrack_correlation'] = correlation
        proof['soundtrack_segments'] = [{'song': r['song']['title'], 'timeline_start_seconds': i*30,
                                        'source_start_seconds': r['song']['start_seconds'],
                                        'clip_soundtrack_correlation': r['source_soundtrack_correlation']}
                                       for i, r in enumerate(chosen)]
        reels.append({'file': movie.name, 'set': key, 'concept_ids': SETS[key], **proof})
    report = {'schema': 'helix.static_concept_art_comparisons.v1', 'songs': songs, 'sets': SETS,
              'clips': rows, 'reels': reels, 'static_artwork': True, 'native_animation': False}
    (output / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'clips': len(rows), 'reels': len(reels),
                      'minimum_audio_correlation': min(r['source_soundtrack_correlation'] for r in rows)}), flush=True)


if __name__ == '__main__':
    main()
