"""Convert separated model estimates into native review clocks, never release evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd
from tools.phoneme_source import digest
from music.review_score import vocal_clock

def build(audio, manifest, output):
    audio, manifest, output = map(Path, (audio, manifest, output))
    report = json.loads(manifest.read_text())
    if report['source_sha256'] != digest(audio):
        raise ValueError('Source hash mismatch')
    count = round(sf.info(audio).duration * 100)
    arrays, tracks = {}, {}
    for role, lane in [('lead', 'estimated_lead'), ('backing', 'estimated_backing')]:
        entry = report[role]
        path = manifest.parent / entry['path']
        if digest(path) != entry['sha256']:
            raise ValueError('Track hash mismatch')
        wave, sr = sf.read(path, dtype='float32', always_2d=True)
        if abs(len(wave)/sr - count/100) > .1:
            raise ValueError('Track duration mismatch')
        d = gcd(sr, 16000)
        clock = vocal_clock(resample_poly(wave.mean(axis=1), 16000//d, sr//d))
        for key in ('energy', 'shapes'):
            values = clock[key][:count]
            arrays[lane+'_'+key] = np.pad(values, (0, count-len(values)))
        # Acoustic periodicity is a heuristic, not calibrated singer confidence.
        values = np.clip(clock['periodicity'][:count], 0, 1)
        arrays[lane+'_presence_probability'] = np.pad(values, (0, count-len(values)))
        tracks[lane] = {'sha256': entry['sha256']}
    output.mkdir(parents=True, exist_ok=False)
    archive = output/'acoustic_vocal_clocks.npz'
    np.savez_compressed(archive, **arrays)
    receipt = dict(audio_sha256=digest(audio), clock_sha256=digest(archive),
        clock_hop_seconds=.01, tracks=tracks, verification_state='ESTIMATED_REVIEW',
        independent_backing_verified=False, exact_phoneme_boundaries_verified=False,
        limitation='RoFormer model estimates; periodicity proxy, not calibrated presence or verified singer identity.')
    (output/'diagnostic.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return output

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('audio', 'manifest', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    build(a.audio, a.manifest, a.output)
