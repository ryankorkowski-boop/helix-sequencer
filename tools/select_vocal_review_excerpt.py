"""Select a source-bound review excerpt; model activity is not singer identity proof."""
import argparse
import json
import subprocess
from pathlib import Path
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from music.review_score import vocal_clock
from music.vocal_qualification import absolute_vocal_activity, screen_candidate_lanes
from tools.phoneme_source import digest
from tools.roformer_review_fixture import build


def choose(audio, manifest, output, fixture):
    report = json.loads(manifest.read_text())
    if report['source_sha256'] != digest(audio):
        raise ValueError('Vocal manifest belongs to another source')
    clocks = []
    for role in ('lead', 'backing'):
        entry = report[role]
        path = manifest.parent / entry['path']
        if digest(path) != entry['sha256']:
            raise ValueError('Vocal stem checksum mismatch')
        y, sr = sf.read(path, dtype='float32', always_2d=True)
        d = gcd(sr, 16000)
        mono = y.mean(axis=1)
        clock = vocal_clock(resample_poly(mono, 16000 // d, sr // d))
        mask, _ = absolute_vocal_activity(mono, sr, len(clock['energy']))
        clocks.append((np.where(mask, clock['energy'], 0),
                       np.where(mask, clock['shapes'], 0),
                       np.where(mask, np.clip(clock['periodicity'], 0, 1), 0)))
    n = min(len(c[0]) for c in clocks)
    energy, shapes, _ = screen_candidate_lanes(*(np.column_stack([c[i][:n] for c in clocks]) for i in range(3)))
    lead, backing = ((energy > 0) & (shapes != 0)).T
    candidates = []
    for start in range(0, n - 3000 + 1, 100):
        a, b = lead[start:start+3000], backing[start:start+3000]
        overlap = int(np.count_nonzero(a & b))
        # A review candidate needs both active parts and independent entrances
        # or exits, not just two continuously copied envelopes.
        independent = int(np.count_nonzero(a ^ b))
        if overlap >= 100 and independent >= 100 and a.sum() >= 200 and b.sum() >= 200:
            candidates.append((overlap, independent, -start))
    if not candidates:
        raise ValueError('No 30-second passage passes the estimated vocal activity gate')
    overlap, independent, neg_start = max(candidates)
    start = -neg_start / 100
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(audio),
                    '-ss', str(start), '-t', '30', '-c:a', 'pcm_s16le', str(output)], check=True)
    build(audio, manifest, fixture, excerpt=output, start=start)
    receipt = {'source_sha256': digest(audio), 'excerpt_sha256': digest(output),
               'start_seconds': start, 'duration_seconds': sf.info(output).duration,
               'estimated_overlap_seconds': overlap / 100,
               'estimated_independent_activity_seconds': independent / 100,
               'independent_singer_identity_verified': False,
               'status': 'estimated_review_only'}
    (fixture / 'excerpt_selection.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('audio', 'manifest', 'output', 'fixture'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    choose(args.audio, args.manifest, args.output, args.fixture)
