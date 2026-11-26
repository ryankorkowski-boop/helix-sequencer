"""Compare the recovered Beta 1.3 pilot with a current native Helix show."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from tools.phoneme_source import EXPECTED_SHA256, digest
from tools.verify_recovery_media import verify


BASELINE_COMMIT = '6b87b31d9c6fbb7e78729be1b490c3e765ff8aad'
REVIEW_SECONDS = 30


def verify_inputs(baseline: Path, candidate: Path, candidate_commit: str) -> dict:
    reports = []
    for show, commit in ((baseline, BASELINE_COMMIT), (candidate, candidate_commit)):
        report = json.loads((show / 'run_manifest.json').read_text())
        if (report['source_commit'] != commit or report['status'] != 'sequence_generated'
                or report['sequencer_exit_code'] != 0):
            raise ValueError(f'Unverified sequence production at {show}')
        audio = show / 'media/Phoneme_Test_Hook.mp3'
        if digest(audio) != EXPECTED_SHA256 or report['audio_sha256'] != EXPECTED_SHA256:
            raise ValueError(f'Unexpected original soundtrack at {show}')
        reports.append(report)
    base, current = reports
    common = ('source_duration_seconds', 'vocal_cache_sha256', 'vocal_receipt_sha256')
    if base['source_duration_seconds'] < REVIEW_SECONDS or any(base[k] != current[k] for k in common):
        raise ValueError('The lanes must use the same source timeline and vocal estimates')
    layout = digest(baseline / 'xlights_rgbeffects.xml')
    if layout != digest(candidate / 'xlights_rgbeffects.xml'):
        raise ValueError('Native A/B requires the identical xLights layout')
    return {'baseline_commit': BASELINE_COMMIT, 'candidate_commit': candidate_commit,
            'original_audio_sha256': EXPECTED_SHA256, 'layout_sha256': layout,
            **{key: base[key] for key in common}}


def native_movie(show: Path) -> Path:
    receipt = json.loads((show / 'run_manifest.json').read_text())['native_preview']
    movie = Path(receipt['mp4'])
    if (receipt['status'] != 'success' or receipt['mp4_sha256'] != digest(movie)
            or receipt['native_export_resolution'] != [1920, 1080]):
        raise ValueError(f'Missing verified HD xLights export at {show}')
    return movie


def compare(baseline: Path, candidate: Path, candidate_commit: str, output: Path) -> dict:
    inputs = verify_inputs(baseline, candidate, candidate_commit)
    output.mkdir(parents=True, exist_ok=True)
    audio = output / 'Review_30s.wav'
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i',
                    str(candidate / 'media/Phoneme_Test_Hook.mp3'), '-t', str(REVIEW_SECONDS),
                    '-c:a', 'pcm_s16le', str(audio)], check=True)
    video = output / 'Beta13_vs_Beta14_30s.mp4'
    filters = (
        "[0:v]scale=960:540,pad=960:1080:0:270,"
        "drawtext=text='Beta 1.3':fontsize=26:fontcolor=white:x=20:y=220[a];"
        "[1:v]scale=960:540,pad=960:1080:0:270,"
        "drawtext=text='Beta 1.4 recovery':fontsize=26:fontcolor=white:x=20:y=220[b];"
        '[a][b]hstack=inputs=2[v]'
    )
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error',
                    '-i', str(native_movie(baseline)), '-i', str(native_movie(candidate)),
                    '-i', str(audio), '-filter_complex', filters, '-map', '[v]', '-map', '2:a:0',
                    '-t', str(REVIEW_SECONDS), '-r', '30', '-c:v', 'libx264', '-pix_fmt',
                    'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', str(video)], check=True)
    media = verify(video, audio, digest(audio))
    if media['dimensions'] != [1920, 1080] or media['actual_frame_rate'] != '30/1':
        raise ValueError('A/B delivery must decode at 1920×1080 and 30 fps')
    proof = {**inputs, 'scope': 'six-snowman band with common source-separated vocal estimates',
             'independent_singers_verified': False, 'owner_approved': False, 'media': media}
    (output / 'AB_PROOF.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--candidate-commit', required=True)
    parser.add_argument('--output', type=Path, help='Without an output directory, verify inputs only')
    args = parser.parse_args()
    if args.output is None:
        result = verify_inputs(args.baseline, args.candidate, args.candidate_commit)
    else:
        result = compare(args.baseline, args.candidate, args.candidate_commit, args.output)
    print(json.dumps(result, indent=2))
