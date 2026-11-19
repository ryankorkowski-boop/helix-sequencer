"""Render a hash-verified original through sixteen native xLights layouts."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from models.full_song_layouts import NAMES, build as build_layout
from tools.build_current_comparison import build as build_layouts
from tools.native_preview import preview_run, probe_media
from tools.phoneme_source import digest
from tools.render_approval_collection import comparison
from tools.verify_recovery_media import verify as verify_media


ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def prepare(audio, work, sha, *, instrumental, vocals):
    if digest(audio) != sha:
        raise ValueError('Original Drive bytes do not match the expected SHA-256')
    if instrumental == (vocals is not None):
        raise ValueError('Choose either explicit instrumental input or a source-bound vocal fixture')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    production = work / 'production'
    media = production / 'media' / audio.name
    manifest = production / 'run_manifest.json'
    identity = dict(audio_name=audio.name, audio_sha256=sha, source_commit=commit)
    if manifest.exists():
        previous = json.loads(manifest.read_text())
        if (any(previous.get(k) != v for k, v in identity.items()) or digest(media) != sha):
            raise ValueError('Production checkpoint belongs to a different source or commit')
        plan, = (production / 'sequence').rglob('*.snowman_band.json')
        if digest(plan) != previous['plan_sha256']:
            raise ValueError('Production plan changed after verification')
    else:
        media.parent.mkdir(parents=True, exist_ok=True)
        if not media.exists():
            shutil.copyfile(audio, media)
        if digest(media) != sha:
            raise ValueError('Staged audio differs from original')
        if list((production / 'sequence').rglob('*.snowman_band.json')):
            raise ValueError('Existing production plan has no source receipt; use fresh work directory')
        command = [
            sys.executable, str(ROOT / 'main.py'), '--profile', 'master', '--',
            '--template', str(ROOT / 'template.xsq'), '--audio', str(media),
            '--layout-file', str(ROOT / 'xlights_rgbeffects.xml'),
            '--output-dir', str(production / 'sequence'), '--single', '--variants', '1',
            '--no-prompt', '--no-save-settings', '--no-workspace-history',
            '--no-learning-memory', '--palette-mode', 'warm', '--sync-lyrics-heads',
        ]
        with (production / 'sequencer.log').open('w') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        plan, = (production / 'sequence').rglob('*.snowman_band.json')
        write_json(manifest, dict(identity, plan_sha256=digest(plan)))
    layouts = work / 'layouts'
    layouts.mkdir(exist_ok=True)
    settings = dict(identity, plan_sha256=digest(plan), instrumental=instrumental,
                    vocal_clock_sha256=digest(vocals / 'acoustic_vocal_clocks.npz') if vocals else None)
    checkpoint = layouts / 'batch_identity.json'
    if checkpoint.exists():
        if json.loads(checkpoint.read_text()) != settings:
            raise ValueError('Layout checkpoint belongs to different inputs')
    else:
        write_json(checkpoint, settings)
    for number in range(1, len(NAMES) + 1):
        folder = layouts / f'{number:02}'
        panel = folder / 'run_manifest.json'
        if panel.exists():
            row = json.loads(panel.read_text())
            if (row['source_audio_sha256'] != sha or row['source_analysis_sha256'] != digest(plan)
                    or row['layout_sha256'] != digest(folder / 'xlights_rgbeffects.xml')
                    or row['xsq_sha256'] != digest(folder / row['xsq'])):
                raise ValueError(f'Layout checkpoint {number} has changed')
            continue
        if folder.exists():
            raise ValueError(f'Incomplete layout checkpoint at {folder}; move it aside before retrying')
        build_layouts(production, vocals, layouts, numbers=(number,), names=NAMES,
                      layout_builder=build_layout, preserve_addresses=(3,),
                      instrumental=instrumental, expected_sha256=sha)
    return settings


def render_panel(folder, audio, xlights, *, port=49914):
    manifest = folder / 'run_manifest.json'
    row = json.loads(manifest.read_text())
    xsq = folder / row['xsq']
    if (digest(audio) != row['source_audio_sha256'] or digest(xsq) != row['xsq_sha256']
            or digest(folder / 'xlights_rgbeffects.xml') != row['layout_sha256']):
        raise ValueError(f'Native panel {row["number"]} inputs changed after layout preparation')
    report = row.get('native_preview', {})
    renderer_sha = digest(Path(xlights))
    if report.get('status') == 'success' and row.get('batch_renderer_sha256') == renderer_sha:
        movie = Path(report['mp4'])
        fseq = Path(report['evidence_dir']) / xsq.with_suffix('.fseq').name
        if (movie.is_file() and fseq.is_file()
                and digest(movie) == report['mp4_sha256'] and digest(fseq) == report['native_fseq_sha256']
                and digest(xsq) == report['xsq_sha256'] and row['layout_sha256'] == report['layout_sha256']
                and row['source_audio_sha256'] == report['audio_sha256']):
            return row, report, fseq
    report = preview_run(folder, xsq=xsq, audio=audio, xlights=xlights, port=port)
    if report['status'] != 'success':
        raise RuntimeError(f'Native panel {row["number"]} failed: {report["warnings"]}')
    row = json.loads(manifest.read_text())
    row['batch_renderer_sha256'] = renderer_sha
    write_json(manifest, row)
    return row, report, Path(report['evidence_dir']) / xsq.with_suffix('.fseq').name


def inspect_grid(movie):
    """Sample decoded layout pixels over the full video, excluding the labels."""
    width, height = 960, 540
    frame_bytes = width * height
    hashes = [hashlib.sha256() for _ in NAMES]
    previous = [None] * len(NAMES)
    visible = np.zeros(len(NAMES), dtype=int)
    moving = np.zeros(len(NAMES), dtype=int)
    total = 0
    command = ['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-threads', '2', '-i', str(movie),
               '-an', '-vf', f'fps=4,scale={width}:{height}', '-pix_fmt', 'gray',
               '-threads', '1', '-f', 'rawvideo', '-']
    with subprocess.Popen(command, stdout=subprocess.PIPE) as decoder:
        while block := decoder.stdout.read(frame_bytes):
            if len(block) != frame_bytes:
                raise ValueError('Incomplete decoded comparison frame')
            frame = np.frombuffer(block, dtype=np.uint8).reshape(height, width)
            for index, fingerprint in enumerate(hashes):
                y, x = (index // 4) * 135, (index % 4) * 240
                crop = frame[y + 21:y + 132, x + 3:x + 237]
                fingerprint.update(crop.tobytes())
                visible[index] += np.count_nonzero(crop > 32) >= 16
                if previous[index] is not None:
                    moving[index] += np.count_nonzero(np.abs(crop.astype(np.int16) - previous[index]) > 8) >= 12
                previous[index] = crop
            total += 1
        if decoder.wait():
            raise ValueError('Comparison panel decode failed')
    fingerprints = [item.hexdigest() for item in hashes]
    rows = [dict(number=i + 1, decoded_panel_sha256=value, sampled_frames=total,
                 visible_frames=int(visible[i]), moving_frames=int(moving[i]))
            for i, value in enumerate(fingerprints)]
    passed = total >= 4 and len(set(fingerprints)) == 16 and all(
        r['visible_frames'] >= max(4, total // 20) and r['moving_frames'] >= max(3, total // 100)
        for r in rows)
    return rows, passed


def render(audio, work, xlights, identity, *, port=49914):
    receipts = []
    for number, name in enumerate(NAMES, 1):
        folder = work / 'layouts' / f'{number:02}'
        row, native, fseq = render_panel(folder, audio, xlights, port=port)
        channels = json.loads((fseq.parent / 'native_channels.json').read_text())
        if number <= 3 and (channels['channels'], row['channels']) != ((16, 64, 256)[number - 1],) * 2:
            raise ValueError(f'Native AC channel budget mismatch for panel {number}')
        receipts.append(dict(number=number, name=name, layout_sha256=native['layout_sha256'],
                             xsq_sha256=native['xsq_sha256'], fseq_sha256=digest(fseq),
                             native_movie_sha256=native['mp4_sha256'], native_movie=native['mp4'],
                             native_channels=channels, xlights_version=native['xlights_version'],
                             vocal_mode=row['vocal_mode']))
        print(f'NATIVE PANEL {number:02} verified', flush=True)
    if any(len({r[key] for r in receipts}) != 16 for key in ('layout_sha256', 'xsq_sha256', 'fseq_sha256')):
        raise ValueError('Duplicate native layout, XSQ or FSEQ')
    movie = work / 'Full_Length_16_Panel_Comparison.mp4'
    candidate = work / 'Full_Length_16_Panel_Candidate.mp4'
    manifest = work / 'comparison_manifest.json'
    previous = json.loads(manifest.read_text()) if manifest.is_file() else {}
    if (movie.is_file() and previous.get('panels') == receipts
            and previous.get('media', {}).get('sha256') == digest(movie)):
        candidate = movie
    else:
        comparison([Path(r['native_movie']) for r in receipts],
                   [f'{i:02}  {name}' for i, name in enumerate(NAMES, 1)], candidate, audio, 4, 4,
                   duration=float(probe_media(audio, 'ffprobe')['format']['duration']))
    media = verify_media(candidate, audio, identity['audio_sha256'])
    streams = probe_media(candidate, 'ffprobe')['streams']
    if (media['dimensions'] != [1920, 1080] or media['actual_frame_rate'] != '30/1'
            or sorted(s['codec_type'] for s in streams) != ['audio', 'video']):
        raise ValueError('Expected exact 1920×1080 H.264/AAC at 30 fps with one original soundtrack')
    activity, passed = inspect_grid(candidate)
    write_json(work / 'panel_activity.json', {'passed': passed, 'panels': activity})
    if not passed:
        raise ValueError('Decoded comparison contains duplicate, blank, or static panels')
    if candidate != movie:
        candidate.replace(movie)
    media['file'] = movie.name
    write_json(manifest,
               dict(identity, media=media, panels=receipts, decoded_panel_activity=activity,
                    renderer_sha256=digest(Path(xlights)), status='technically_verified',
                    owner_approved=False))
    print(f'Verified comparison: {movie}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('work', type=Path)
    parser.add_argument('--expected-sha256', required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--instrumental', action='store_true')
    source.add_argument('--vocal-fixture', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--xlights')
    parser.add_argument('--port', type=int, choices=(49913, 49914), default=49914)
    parser.add_argument('--render-panels', nargs='+', type=int, choices=range(1, 17),
                        help='Render only these prepared panels without composing the comparison')
    args = parser.parse_args()
    if not args.prepare_only and not args.xlights:
        parser.error('--xlights is required for native rendering')
    if args.prepare_only and args.render_panels:
        parser.error('--render-panels cannot be combined with --prepare-only')
    audio, work = args.audio.resolve(), args.work.resolve()
    identity = prepare(audio, work, args.expected_sha256,
                       instrumental=args.instrumental, vocals=args.vocal_fixture)
    if args.prepare_only:
        return
    xlights = str(Path(shutil.which(args.xlights) or args.xlights).resolve(strict=True))
    if not os.access(xlights, os.X_OK):
        raise ValueError('Pinned xLights binary is not executable')
    if args.render_panels:
        for number in dict.fromkeys(args.render_panels):
            render_panel(work / 'layouts' / f'{number:02}', audio, xlights, port=args.port)
        return
    render(audio, work, xlights, identity, port=args.port)


if __name__ == '__main__':
    main()
