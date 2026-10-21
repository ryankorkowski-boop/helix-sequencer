"""Build a deterministic high-activity sampler from a resolved Drive inventory.

Every inventory entry contributes its own decoded audio. Same-name recordings
remain distinct. The manifest binds source bytes, exact sample ranges and PCM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def select_window(pcm: np.ndarray, rate: int, seconds: float) -> tuple[int, int]:
    """Rank complete windows by energy and positive energy changes, without RNG."""
    if pcm.ndim != 2 or not len(pcm) or not np.isfinite(pcm).all():
        raise ValueError('Expected finite nonempty multichannel PCM')
    if rate <= 0 or not np.isfinite(seconds) or seconds <= 0:
        raise ValueError('Expected positive sample rate and clip duration')
    length = min(len(pcm), round(seconds * rate))
    if length < 1:
        raise ValueError('Clip shorter than one sample')
    hop = max(1, rate // 10)
    mono = pcm.mean(axis=1).astype('f8')
    starts = np.arange(0, len(pcm), hop)
    energy = np.add.reduceat(mono * mono, starts) / np.minimum(hop, len(pcm) - starts)
    novelty = np.maximum(0, np.diff(energy, prepend=energy[0]))
    # Avoid intros/outros where a complete interior candidate exists.
    lo = min(3 * rate, max(0, (len(pcm) - length) // 4))
    hi = max(lo, len(pcm) - length - lo)
    candidates = list(range(lo, hi + 1, max(1, rate // 2))) or [0]
    def score(start):
        a, b = start // hop, max(start // hop + 1, (start + length) // hop)
        return float(np.mean(energy[a:b]) + 2 * np.mean(novelty[a:b]))
    start = max(candidates, key=score)
    return start, start + length


def build(inventory: Path, output: Path, seconds: float = 16.0) -> dict:
    rows = json.loads(inventory.read_text())
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Expected nonempty inventory with unique Drive IDs')
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    rate = 44100
    clips, timeline, clock = [], [], 0
    for i, row in enumerate(rows):
        source = inventory.parent / row['name']
        if digest(source) != row['sha256']:
            raise ValueError('Source hash mismatch: ' + row['name'])
        decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(source),
            '-f', 'f32le', '-ar', str(rate), '-ac', '2', '-'])
        pcm = np.frombuffer(decoded, '<f4').reshape(-1, 2)
        start, end = select_window(pcm, rate, seconds)
        clip = pcm[start:end].copy()
        # Short boundary fades only. No overlap hides the start of the next song.
        fade = min(round(.02 * rate), len(clip) // 2)
        clip[:fade] *= np.linspace(0, 1, fade)[:, None]
        clip[-fade:] *= np.linspace(1, 0, fade)[:, None]
        clips.append(clip)
        timeline.append(dict(index=i + 1, title=row['title'], drive_file_id=row['id'],
            source_sha256=row['sha256'], source_samples=len(pcm),
            source_start_sample=start, source_end_sample=end,
            source_start_seconds=start / rate, source_end_seconds=end / rate,
            sampler_start_sample=clock, sampler_end_sample=clock + len(clip),
            sampler_start_seconds=clock / rate, duration_seconds=len(clip) / rate))
        clock += len(clip)
    audio = output / 'Helix_Starred_All_Songs.wav'
    sf.write(audio, np.concatenate(clips), rate, subtype='PCM_24')
    report = dict(schema='helix.starred_sampler.v1', sample_rate=rate, channels=2,
        audio=audio.name, audio_sha256=digest(audio), duration_seconds=clock / rate,
        songs=len(rows), clips=timeline, method='window RMS plus positive energy change',
        boundary_fade_seconds=.02, independently_verified_instrument_analysis=False)
    (output / 'sampler_manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-c:a', 'libmp3lame',
        '-b:a', '256k', '-metadata', 'artist=hardKor', '-metadata', 'album=Helix Music Mix',
        '-metadata', 'title=Helix Starred Showcase Sampler', str(audio.with_suffix('.mp3'))], check=True)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inventory', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--seconds', type=float, default=16)
    args = p.parse_args()
    print(json.dumps(build(args.inventory, args.output, args.seconds), indent=2))


if __name__ == '__main__':
    main()
