"""Verify the source-bound native band artifact, never the diagnostic fixture.

Artifact selection/commit identity belongs to the workflow. This independently
checks transported bytes and decoded media; artistic approval remains separate.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
from scipy import signal
from tools.native_preview import _sha256, probe_media, _stream, _duration
from tools.quality.native import inspect_fseq
from tools.verify_showcase_luma import verify_mp4

AUDIO_SHA256 = '8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171'
ROLES = {'drummer', 'bass', 'guitar', 'piano', 'lead', 'harmony'}


def unique(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1 or not matches[0].is_file():
        raise ValueError(f'Expected exactly one {name}; found {len(matches)}')
    return matches[0]


def verify_inputs(root: Path, *, expected_commit: str | None = None) -> dict:
    run_manifest = json.loads(unique(root, 'run_manifest.json').read_text())
    manifest = run_manifest['native_preview']
    if expected_commit is not None:
        if not re.fullmatch(r'[0-9a-f]{40}', expected_commit):
            raise ValueError('Expected source commit must be a full lowercase SHA')
        provenance = json.loads(unique(root, 'PROVENANCE.json').read_text())
        if (run_manifest.get('source_commit') != expected_commit
                or provenance.get('source_commit') != expected_commit):
            raise ValueError('Artifact source commit does not match the selected producer commit')
    if (manifest.get('status') != 'success'
            or manifest.get('backend') != 'xlights_house_preview'
            or manifest.get('audio_stream_verified') is not True):
        raise ValueError('No successful native House Preview with original audio')
    if manifest.get('audio_sha256') != AUDIO_SHA256:
        raise ValueError('Wrong original source identity')
    paths = {key: unique(root, name) for key, name in {
        'mp4': 'preview.mp4', 'audio': 'audio.wav', 'xsq': 'Performance.xsq',
        'layout': 'xlights_rgbeffects.xml', 'native_fseq': 'Performance.fseq'}.items()}
    for key, path in paths.items():
        if _sha256(path) != manifest.get(key + '_sha256'):
            raise ValueError(f'{key} digest differs from accepted native manifest')
    proof = json.loads(unique(root, 'pose_provenance.json').read_text())
    if (proof.get('audio_sha256') != AUDIO_SHA256
            or set(proof.get('visible_performer_roles', [])) != ROLES
            or proof.get('legacy_xylophone_enabled') is not False
            or proof.get('source_score') != 'ReviewBandPerformance.pose'):
        raise ValueError('Six-musician source performance provenance invalid')
    layout = ET.parse(paths['layout']).getroot()
    models = {m.get('name'): m for m in layout.findall('./models/model')}
    expected = {'HX_SNOW_' + r.upper() for r in ROLES}
    if set(models) != expected or len(layout.findall('./models/model')) != 6:
        raise ValueError('Missing or duplicated snowman model')
    seq = ET.parse(paths['xsq']).getroot()
    rows = seq.findall('./ElementEffects/Element')
    model_rows = [e for e in rows if e.get('type') == 'model']
    if {e.get('name') for e in model_rows} != expected or len(model_rows) != 6:
        raise ValueError('Six independent editable XSQ model rows required')
    counts = {}
    musical_counts = {}
    for row in model_rows:
        parts = {s.get('name') for s in models[row.get('name')].findall('subModel')}
        layers = row.findall('SubModelEffectLayer')
        if not layers or any(layer.get('name') not in parts for layer in layers):
            raise ValueError('XSQ submodel row does not resolve to native layout')
        counts[row.get('name')] = sum(len(layer.findall('Effect')) for layer in layers)
        if not counts[row.get('name')]:
            raise ValueError('Performer has no editable effects')
        # Lit bodies, idle pose banks and closed mouths cannot establish that
        # a performer played. Inspect the transported editable musical lanes.
        role = row.get('name').removeprefix('HX_SNOW_').lower()
        def musical_part(name):
            if role == 'drummer':
                return name in {'SNARE_LEFT', 'SNARE_RIGHT', 'KICK', 'TOM_HIGH',
                                'TOM_MID', 'TOM_FLOOR', 'HI_HAT',
                                'CYMBAL_LEFT', 'CYMBAL_RIGHT'}
            if role == 'piano':
                return name.startswith('NOTE_MIDI_')
            if role in ('guitar', 'bass'):
                return name.startswith('STRING_')
            return name.startswith('MOUTH_') and name.upper() != 'MOUTH_REST'
        musical_counts[row.get('name')] = sum(
            1 for layer in layers if musical_part(layer.get('name', ''))
            for effect in layer.findall('Effect')
            if 0 <= int(effect.get('startTime', '-1'))
            < int(effect.get('endTime', '-1')) <= 36000)
        if not musical_counts[row.get('name')]:
            raise ValueError(
                f"No non-rest musical effects for {row.get('name')}; "
                "body illumination and idle/rest poses do not establish playing or singing")
    duration = float(seq.findtext('head/sequenceDuration', '0'))
    if duration != 36 or manifest.get('duration_seconds') != duration:
        raise ValueError('Expected exact original 36-second excerpt')
    return {'paths': paths, 'duration': duration, 'effects_per_model': counts,
            'musical_effects_per_model': musical_counts}


def verify(root: Path, *, expected_commit: str | None = None) -> dict:
    checked = verify_inputs(root, expected_commit=expected_commit)
    paths = checked['paths']
    channels = inspect_fseq(paths['native_fseq'])
    if (channels['nonzero_frames'] != channels['frames']
            or channels['nonzero_samples'] <= 0
            or abs(channels['duration_ms'] - checked['duration'] * 1000) > 100):
        raise ValueError('Inactive or duration-mismatched native FSEQ')
    media = probe_media(paths['mp4'], 'ffprobe')
    video, audio = (_stream(media, kind) for kind in ('video', 'audio'))
    if (int(video['width']), int(video['height'])) != (1920, 1080):
        raise ValueError('Native HD dimensions required')
    for stream in (video, audio):
        if abs(_duration(stream) - checked['duration']) > .1 or abs(float(stream.get('start_time', 0))) > .03:
            raise ValueError('Audio/video duration or start offset invalid')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(paths['mp4']),
                    '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
                   check=True, timeout=180, capture_output=True)
    decoded = []
    for path in (paths['audio'], paths['mp4']):
        pcm = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
            '-map', '0:a:0', '-ar', '8000', '-ac', '2', '-f', 'f32le', '-'], timeout=60)
        decoded.append(np.frombuffer(pcm, '<f4').reshape(-1, 2))
    reference, actual = decoded
    windows = []
    for second in (0, 9, 18, 27, 33):
        lo, hi = second * 8000, (second + 3) * 8000
        x, y = reference[lo:hi], actual[lo:hi]
        if x.shape != (24000, 2) or y.shape != x.shape:
            raise ValueError('Truncated source soundtrack')
        coefficients = [float(np.corrcoef(x[:, c], y[:, c])[0, 1]) for c in range(2)]
        cross = signal.correlate(y.mean(axis=1), x.mean(axis=1), method='fft')
        center = len(x) - 1
        lag = int(np.argmax(cross[center-160:center+161]) - 160)
        if not all(np.isfinite(c) and c > .99 for c in coefficients) or abs(lag) > 1:
            raise ValueError(f'Original soundtrack mismatch at {second}s: {coefficients}, lag={lag}')
        windows.append({'second': second, 'correlations': coefficients, 'offset_ms': lag / 8})
    readability = verify_mp4(paths['mp4'])
    if not readability['passed']:
        raise ValueError('Native video is black, unreadable or frozen: ' + json.dumps(readability))
    return {'schema': 'helix.native_band_acceptance.v1', 'passed': True,
            'source_commit': expected_commit,
            'mp4_sha256': _sha256(paths['mp4']), 'source_audio_sha256': AUDIO_SHA256,
            'duration_seconds': checked['duration'], 'effects_per_model': checked['effects_per_model'],
            'musical_effects_per_model': checked['musical_effects_per_model'],
            'independent_vocal_sources_verified': False,
            'fseq': channels, 'soundtrack_windows': windows, 'readability': readability,
            'owner_visual_approval': False, 'hardware_tested': False,
            'full_song_showcase_complete': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--expected-commit', required=True,
                        help='Exact source SHA selected by the workflow, never an earlier artifact')
    args = parser.parse_args()
    try:
        result = verify(args.artifact, expected_commit=args.expected_commit)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, subprocess.SubprocessError) as exc:
        result = {'passed': False, 'error': str(exc)}
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
