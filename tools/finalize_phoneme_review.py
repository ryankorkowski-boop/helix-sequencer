"""Collect only verified native output; keep musical acceptance separate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from tools.phoneme_source import digest, EXPECTED_SHA256


def finalize(show: Path) -> dict:
    show = show.resolve()
    manifest = json.loads((show / 'run_manifest.json').read_text())
    native = manifest.get('native_preview', {})
    report = dict(schema='helix.phoneme-review.v1', native_video_verified=False,
                  owner_approved=False, release_ready=False, blockers=[])
    try:
        if native.get('status') != 'success' or not native.get('audio_stream_verified'):
            raise ValueError('Native preview unsuccessful; inspect run_manifest.json and native-preview-* logs')
        source = show / 'media/Phoneme_Test_Hook.mp3'
        video = Path(native['mp4'])
        if digest(source) != EXPECTED_SHA256 or native.get('audio_sha256') != EXPECTED_SHA256:
            raise ValueError('Original soundtrack provenance mismatch')
        if digest(video) != native.get('mp4_sha256'):
            raise ValueError('Native MP4 checksum differs from render receipt')
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video),
                        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
        from tools.verify_showcase_luma import verify_mp4
        readability = verify_mp4(video)
        (show / 'SHOWCASE_READABILITY.json').write_text(json.dumps(readability, indent=2) + '\n')
        report['readability'] = readability
        if not readability['passed']:
            raise ValueError('Native movie is unreadable or frozen; retain diagnostic media without promoting it for owner approval')
        import numpy as np
        def pcm(path):
            return np.frombuffer(subprocess.check_output([
                'ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                '-ac', '1', '-ar', '16000', '-f', 'f32le', '-']), dtype='<f4')
        original, decoded = pcm(source), pcm(video)
        length = min(len(original), len(decoded))
        correlation = float(np.corrcoef(original[:length], decoded[:length])[0, 1])
        report['soundtrack'] = dict(zero_lag_correlation=correlation,
                                     decoded_seconds=len(decoded)/16000,
                                     original_seconds=len(original)/16000)
        if not np.isfinite(correlation) or correlation < .97 or len(decoded) < len(original) - 1600:
            raise ValueError('Native soundtrack does not match the full original at timeline zero')
        target = show / 'Phoneme_Test_Hook_Helix_Native.mp4'
        shutil.copyfile(video, target)
        report.update(native_video_verified=True, video=target.name,
                      audio_sha256=EXPECTED_SHA256, native_report=native)
        vocal = json.loads((show / 'vocal_lane_diagnostic.json').read_text())
        if not vocal.get('independent_backing_verified'):
            report['blockers'].append('Independent backing vocals not established from mixed stereo source')
        report['blockers'].extend(['Canonical appearance and whole-band musical review pending',
                                   'Owner MP4 approval required before merge/public beta'])
        return report
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        report['blockers'].append(str(exc))
        raise
    finally:
        (show / 'native_render_verification.json').write_text(json.dumps(report, indent=2) + '\n')
        with (show / 'SHA256SUMS').open('w') as receipt:
            for path in sorted(show.rglob('*')):
                if path.is_file() and path.name != 'SHA256SUMS':
                    receipt.write(digest(path) + '  ' + str(path.relative_to(show)) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('show', type=Path)
    args = parser.parse_args()
    print(json.dumps(finalize(args.show), indent=2))
