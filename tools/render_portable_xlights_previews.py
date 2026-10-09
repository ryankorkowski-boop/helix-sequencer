"""Make Android-compatible review movies from verified portable native renders."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import html
import json
import math
import multiprocessing
from pathlib import Path
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw

from models.showcase_flavors import FLAVORS, build_flavor
from models.ultimate_showcase import build_ultimate_garden
from tools.build_helpers.ultimate_showcase_preview import _base, _font, read_fseq
from tools.package_showcase_audio_batch import decode_audio
from tools.showcase_audio_preview import NativeSongView, render_native_song


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_inputs(root: Path, show: dict, sequence: dict) -> dict:
    folder = root / show['folder']
    native = sequence['native_verification']
    paths = {'xsq_sha256': folder / sequence['file'],
             'fseq_sha256': (folder / sequence['file']).with_suffix('.fseq'),
             'layout_sha256': folder / 'xlights_rgbeffects.xml'}
    for key, path in paths.items():
        if digest(path) != native[key]:
            raise ValueError(f'Verified native input changed: {path}')
    if not native['all_rgb_models_active'] or not native['control_channels_dark']:
        raise ValueError('Native lighting verification is incomplete')
    result = {key: native[key] for key in paths}
    if sequence['media']:
        result['audio_sha256'] = digest(folder / sequence['media'])
        if result['audio_sha256'] != sequence['audio_sha256']:
            raise ValueError('Soundtrack differs from preserved original')
    return result


def inspect_movie(path: Path, seconds: float, audio: bool) -> dict:
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate,nb_frames:format=duration',
        '-of', 'json', str(path)]))
    video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    sounds = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    if video['codec_name'] != 'h264' or video['pix_fmt'] != 'yuv420p':
        raise ValueError('Movie is not Android-compatible H.264')
    if video['r_frame_rate'] != '20/1' or int(video['nb_frames']) != math.ceil(seconds * 20):
        raise ValueError('Movie dropped frames or has incorrect duration')
    if abs(float(probe['format']['duration']) - seconds) > .15:
        raise ValueError('Movie duration differs from sequence')
    if bool(sounds) != audio or any(s['codec_name'] != 'aac' for s in sounds):
        raise ValueError('Movie soundtrack stream is missing or unexpected')
    # Parse top-level MP4 atoms; faststart must put the index before the media.
    atoms = []
    with path.open('rb') as stream:
        while stream.tell() < path.stat().st_size:
            header = stream.read(8)
            size, kind = int.from_bytes(header[:4], 'big'), header[4:8]
            if size == 1:
                size = int.from_bytes(stream.read(8), 'big')
                header = bytes(16)
            if size < len(header):
                raise ValueError('Invalid MP4 atom')
            atoms.append(kind)
            stream.seek(size - len(header), 1)
    if atoms.index(b'moov') > atoms.index(b'mdat'):
        raise ValueError('MP4 is not optimized for streaming')
    subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(path),
                    '-f', 'null', '-'], check=True)
    return {'probe': probe, 'complete_decode_passed': True, 'faststart': True}


def render_one(root: Path, output: Path, show: dict, sequence: dict) -> dict:
    inputs = assert_inputs(root, show, sequence)
    folder = root / show['folder']
    destination = output / show['folder']
    destination.mkdir(parents=True, exist_ok=True)
    movie = destination / Path(sequence['file']).with_suffix('.mp4')
    proof_path = movie.with_suffix('.verification.json')
    settings = {'width': 960, 'height': 540, 'fps': 20, 'preview_schema': 1}
    if proof_path.is_file() and movie.is_file():
        cached = json.loads(proof_path.read_text())
        if (cached['inputs'] == inputs and cached['settings'] == settings
                and cached['mp4_sha256'] == digest(movie)):
            return cached
    garden = (build_ultimate_garden() if show['folder'] == 'Helix_Aurora' else
              build_flavor(next(f.key for f in FLAVORS if f.slug == show['folder'])))
    fseq = (folder / sequence['file']).with_suffix('.fseq')
    duration = sequence['duration_seconds']
    if sequence['media']:
        render_native_song(garden, fseq, folder / sequence['media'], movie, duration,
                           width=960, height=540)
    else:
        frames, step = read_fseq(fseq)
        view = NativeSongView(garden, '24 SECOND LIGHTING STUDY', 960, 540, halo_scale=2)
        bottom = int(540 * .935)
        clean = _base(960, 540, garden.title)
        view.base.paste(clean.crop((0, bottom, 960, 540)), (0, bottom))
        ImageDraw.Draw(view.base).text((43, 513), 'NATIVE XLIGHTS / 24 SECOND LIGHTING STUDY / NO AUDIO',
                                      font=_font(9), fill=(134, 180, 198))
        encoder = subprocess.Popen([
            'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', '960x540', '-r', '20', '-i', '-', '-an', '-c:v', 'libx264',
            '-preset', 'veryfast', '-crf', '22', '-threads', '1', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', str(movie)], stdin=subprocess.PIPE)
        try:
            for i in range(math.ceil(duration * 20)):
                encoder.stdin.write(view.frame(frames[min(len(frames) - 1, round(i * 50 / step))]).tobytes())
        finally:
            encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError('Study encoder failed')
    proof = {'layout': garden.title, 'folder': show['folder'], 'sequence': sequence['file'],
             'kind': sequence['kind'], 'track': sequence.get('track', 'Lighting study'),
             'media': sequence['media'], 'duration_seconds': duration,
             'file': str(movie.relative_to(output)), 'inputs': inputs, 'settings': settings,
             'mp4_sha256': digest(movie), 'bytes': movie.stat().st_size,
             **inspect_movie(movie, duration, bool(sequence['media']))}
    frames, step = read_fseq(fseq)
    sample_times = (1, duration / 2, duration - 1)
    sample_dir = destination / (movie.stem + '_frames')
    sample_dir.mkdir(exist_ok=True)
    for i, second in enumerate(sample_times):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(movie),
                        '-frames:v', '1', str(sample_dir / f'{i}.png')], check=True)
    # Evidence from decoded video, rather than just the compositor inputs.
    images = [np.asarray(Image.open(sample_dir / f'{i}.png').convert('RGB')) for i in range(3)]
    proof['decoded_samples_animate'] = any(np.any(images[i] != images[0]) for i in (1, 2))
    if not proof['decoded_samples_animate']:
        raise ValueError('Decoded preview does not animate')
    proof['native_rgb_coverage_verified'] = sequence['native_verification']['all_rgb_models_active']
    proof_path.write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def finish(root: Path, output: Path, rows: list[dict]) -> dict:
    audio_cache = {}
    for row in rows:
        if not row['media']:
            continue
        movie = output / row['file']
        encoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(movie),
                                          '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])
        key = (row['inputs']['audio_sha256'], hashlib.sha256(encoded).hexdigest())
        if key not in audio_cache:
            original = decode_audio(root / row['folder'] / row['media'])
            actual = decode_audio(movie)
            size = min(len(original), len(actual))
            correlation = float(np.corrcoef(original[:size], actual[:size])[0, 1])
            if not np.isfinite(correlation) or correlation < .97 or abs(len(actual) - len(original)) / 2000 > .15:
                raise ValueError('Preview soundtrack differs from source song')
            audio_cache[key] = correlation
        row['soundtrack_correlation'] = audio_cache[key]
    reels = []
    for track in dict.fromkeys(row['track'] for row in rows if row['kind'] == 'full_song'):
        selected = sorted((r for r in rows if r['track'] == track), key=lambda r: r['folder'])
        duration = selected[0]['duration_seconds']
        # Seeking between native 50ms frames can leave the first stacked frame
        # at +50ms, losing a frame when ffmpeg trims the output to 24 seconds.
        start = math.floor(min(max(0, duration / 2 - 12), duration - 24) * 20) / 20
        movie = output / (Path(selected[0]['sequence']).stem.split('__')[0] + '_Six_Layouts_Review.mp4')
        args = ['ffmpeg', '-v', 'error', '-y', '-filter_complex_threads', '1']
        for row in selected:
            args += ['-threads', '1', '-ss', str(start), '-i', str(output / row['file'])]
        filters = [f'[{i}:v]setpts=PTS-STARTPTS,scale=640:360[v{i}]' for i in range(6)]
        filters += [''.join(f'[v{i}]' for i in range(6)) + 'xstack=inputs=6:layout=0_0|640_0|1280_0|0_360|640_360|1280_360[v]']
        args += ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '0:a:0', '-t', '24',
                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-threads', '1',
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(movie)]
        subprocess.run(args, check=True)
        inspect_movie(movie, 24, True)
        original = decode_audio(root / selected[0]['folder'] / selected[0]['media'], start=start, duration=24)
        actual = decode_audio(movie)
        size = min(len(original), len(actual))
        correlation = float(np.corrcoef(original[:size], actual[:size])[0, 1])
        if not np.isfinite(correlation) or correlation < .97:
            raise ValueError('Comparison soundtrack mismatch')
        reels.append({'track': track, 'file': movie.name, 'song_start_seconds': start,
                      'duration_seconds': 24, 'soundtrack_correlation': correlation, 'sha256': digest(movie)})
    report = {'schema': 'helix.android_native_previews.v1', 'source': str(root),
              'layout_packaging_acceptance': 'passed by user', 'laptop_launch': 'deferred by user; not verified locally',
              'drummer_acceptance': 'separate and unchanged', 'sequences': rows, 'comparison_reels': reels}
    (output / 'PREVIEWS.json').write_text(json.dumps(report, indent=2) + '\n')
    sections = []
    for track in dict.fromkeys(r['track'] for r in rows):
        selected = sorted((r for r in rows if r['track'] == track), key=lambda r: r['folder'])
        links = ''.join(f'<p><a href="{html.escape(r["file"])}">{html.escape(r["layout"])} — {r["duration_seconds"]:.2f}s</a></p>' for r in selected)
        reel = next((r for r in reels if r['track'] == track), None)
        if reel:
            links = f'<p><a href="{reel["file"]}">24-second six-layout comparison</a></p>' + links
        sections.append(f'<section><h2>{html.escape(track)}</h2>{links}</section>')
    (output / 'index.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Helix MP4 previews</title><style>body{background:#080e1a;color:#eef6ff;font:18px system-ui;max-width:800px;margin:auto;padding:24px}a{color:#85eee2}section{margin:32px 0}</style>'
        '<h1>Helix MP4 previews</h1><p>Full-song lighting from verified native xLights renders, with each original soundtrack. Silent 24-second studies are listed separately. Aurora has a study only.</p>' + ''.join(sections))
    (output / 'README.txt').write_text('HELIX ANDROID MP4 PREVIEWS\n\n30 full songs with original audio, seven silent 24-second studies, five same-song six-layout comparison reels.\n'
        'Full previews: 960x540, 20fps, H.264/yuv420p, AAC, streaming-friendly MP4.\n'
        'Lighting is decoded from verified native FSEQs and projected onto each matching layout. These are geometry previews, not xLights screen recordings.\n'
        'Custom nodes match exported geometry; stock review paths remain illustrative.\n'
        'Layout packaging accepted by user. Laptop playback deferred; no local audio-device proof. Drummer acceptance remains separate.\n'
        'Source media, XSQs, native FSEQs and production show folders are unchanged. See MASTER_TODO.md on feature/android-native-previews.\n')
    packages = []
    groups = [('Helix_All_MP4_Previews', rows, reels)]
    for track in dict.fromkeys(r['track'] for r in rows):
        chosen = [r for r in rows if r['track'] == track]
        slug = 'Helix_Lighting_Studies' if track == 'Lighting study' else Path(chosen[0]['sequence']).stem.split('__')[0]
        groups.append((slug + '_MP4s', chosen, [r for r in reels if r['track'] == track]))
    for slug, chosen, comparisons in groups:
        path = output.parent / (slug + '.zip')
        with zipfile.ZipFile(path, 'w') as archive:
            archive.write(output / 'README.txt', 'README.txt')
            archive.write(output / 'PREVIEWS.json', 'PREVIEWS.json', compress_type=zipfile.ZIP_DEFLATED)
            for row in chosen:
                archive.write(output / row['file'], row['file'])
            for reel in comparisons:
                archive.write(output / reel['file'], reel['file'])
            if len(chosen) == 37:
                archive.write(output / 'index.html', 'index.html')
        with zipfile.ZipFile(path) as archive:
            if archive.testzip():
                raise ValueError('Preview ZIP failed CRC check')
            if sum(n.endswith('.mp4') for n in archive.namelist()) != len(chosen) + len(comparisons):
                raise ValueError('Preview ZIP inventory mismatch')
        packages.append({'file': path.name, 'bytes': path.stat().st_size, 'sha256': digest(path),
                         'movies': len(chosen) + len(comparisons), 'crc_valid': True})
    report['packages'] = packages
    (output / 'PREVIEWS.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('outputs/Helix_Android_Previews'))
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root / 'SHOWS.json').read_text())
    jobs = [(show, sequence) for show in manifest['shows'] for sequence in show['sequences']]
    jobs.sort(key=lambda j: (not (j[0]['folder'] == 'Helix_Fire_and_Ice' and j[1]['file'].startswith('Wire_Tree__')), j[1]['duration_seconds']))
    results = []
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context('spawn')) as pool:
        futures = [pool.submit(render_one, root, output, show, sequence) for show, sequence in jobs]
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            (output / 'PROGRESS.json').write_text(json.dumps(results, indent=2) + '\n')
            print(json.dumps({'complete': len(results), 'total': len(jobs), 'preview': row['file']}), flush=True)
    results.sort(key=lambda r: (r['kind'], r['track'], r['folder']))
    report = finish(root, output, results)
    print(json.dumps({'verified_movies': len(results), 'comparison_reels': len(report['comparison_reels']),
                      'packages': report['packages']}), flush=True)


if __name__ == '__main__':
    main()
