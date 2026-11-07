"""Sample-accurate, lossless showcase excerpts with source provenance."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile


def timestamp(value: str) -> float:
    parts = value.split(':')
    if len(parts) > 3:
        raise ValueError('Use seconds, MM:SS or HH:MM:SS')
    numbers = [float(v) for v in parts]
    if any(not math.isfinite(v) or v < 0 for v in numbers):
        raise ValueError('Timestamp must be finite and nonnegative')
    if len(numbers) > 1 and any(v >= 60 for v in numbers[1:]):
        raise ValueError('Timestamp minute/second field must be below 60')
    result = 0.0
    for number in numbers:
        result = result * 60 + number
    return result


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
         '-show_streams', '-of', 'json', str(path)],
        capture_output=True, text=True, check=True, timeout=30)
    streams = json.loads(result.stdout).get('streams', [])
    if not streams:
        raise ValueError('No audio stream')
    stream = streams[0]
    if not math.isfinite(float(stream['duration'])):
        raise ValueError('Invalid audio duration')
    return stream


def active_window(source: Path) -> dict:
    """Reuse the existing 36s multidimensional activity ranker, not volume alone."""
    from tools.showcase_excerpt_rank import rank_one
    with tempfile.TemporaryDirectory(prefix='helix-rank-') as directory:
        (Path(directory) / 'source.mp3').symlink_to(source.resolve())
        result = rank_one((dict(id='source', title=source.name,
                               mime_type='audio/mpeg', folder='supplied'), directory))
    if not result['candidates']:
        raise ValueError('No complete 36-second active window')
    return result['candidates'][0]


def extract(source: Path, target: Path, *, start: float = 0,
            end: float = 30) -> dict:
    """Reject short/invalid input; publish only a complete verified PCM WAV."""
    source, target = source.resolve(), target.resolve()
    if source == target:
        raise ValueError('Excerpt must not replace the source')
    if not source.is_file():
        raise FileNotFoundError(source)
    if not all(math.isfinite(v) for v in (start, end)) or start < 0:
        raise ValueError('Excerpt timestamps must be finite and nonnegative')
    duration = end - start
    if not 30 <= duration <= 42:
        raise ValueError('Showcase excerpts must be 30–42 seconds')
    if target.suffix.lower() != '.wav':
        raise ValueError('Use .wav to preserve decoded audio without lossy re-encoding')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise RuntimeError('ffmpeg and ffprobe are required')
    info = probe(source)
    if end > float(info['duration']) + 1e-6:
        raise ValueError('Requested ending exceeds source duration')
    rate, channels = int(info['sample_rate']), int(info['channels'])
    source_sha = digest(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.excerpt-', dir=target.parent) as directory:
        temporary = Path(directory) / 'audio.wav'
        subprocess.run(
            ['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(source),
             '-ss', format(start, '.9f'), '-t', format(duration, '.9f'),
             '-map', '0:a:0', '-vn', '-c:a', 'pcm_s24le', str(temporary)],
            capture_output=True, check=True, timeout=180)
        clipped = probe(temporary)
        actual = int(clipped['duration_ts']) * float(clipped['time_base'].split('/')[0]) / float(clipped['time_base'].split('/')[1])
        if (abs(actual - duration) > 1.01 / rate or
                int(clipped['sample_rate']) != rate or
                int(clipped['channels']) != channels):
            raise ValueError('Incomplete excerpt or changed audio format')
        if digest(source) != source_sha:
            raise ValueError('Source changed during extraction')
        report = dict(schema='helix.audio_excerpt.v1', source_name=source.name,
                      source_sha256=source_sha, source_start_seconds=start,
                      source_end_seconds=end, duration_seconds=actual,
                      sample_rate=rate, channels=channels, codec='pcm_s24le',
                      excerpt_sha256=digest(temporary), artist='hardKor',
                      processing='decode and trim only; no normalization or fading')
        temporary.replace(target)
    manifest = target.with_suffix('.excerpt.json')
    manifest.write_text(json.dumps(report, indent=2) + '\n')
    return report
