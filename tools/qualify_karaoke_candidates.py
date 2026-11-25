"""Measure retained offline karaoke output without certifying singer identity."""
from __future__ import annotations
import argparse
import json
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from music.review_score import vocal_clock
from music.vocal_qualification import absolute_vocal_activity, screen_candidate_lanes
from tools.phoneme_source import digest
from tools.qualified_keyboard import verified_piano


def qualify(audio, stem_manifest, receipt_path):
    audio, stem_manifest, receipt_path = map(Path, (audio, stem_manifest, receipt_path))
    verified_piano(audio, stem_manifest)
    manifest = json.loads(stem_manifest.read_text())
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get('schema') != 'helix.offline_karaoke_candidates.v1'
            or receipt.get('source_sha256') != digest(audio)
            or receipt.get('stem_manifest_sha256') != digest(stem_manifest)
            or receipt.get('combined_vocals_sha256') != manifest['tracks']['vocals']['sha256']):
        raise ValueError('Foreign karaoke candidate receipt')
    root = receipt_path.resolve().parent
    entries = receipt['outputs']
    if len(entries) != 2 or len({e['sha256'] for e in entries}) != 2:
        raise ValueError('Two distinct karaoke outputs required')
    duration = sf.info(audio).duration
    clock_count = round(duration*100)
    clocks, observations, pcm = [], [], []
    for entry in entries:
        path = (root/entry['path']).resolve()
        if not path.is_relative_to(root) or digest(path) != entry['sha256']:
            raise ValueError('Changed karaoke output')
        wave, sr = sf.read(path, dtype='float32', always_2d=True)
        if abs(len(wave)/sr-duration) > .05 or not np.isfinite(wave).all():
            raise ValueError('Invalid karaoke output clock')
        mono = wave.mean(axis=1)
        mask, windows = absolute_vocal_activity(mono, sr, clock_count)
        d = gcd(sr,16000)
        resampled = resample_poly(mono,16000//d,sr//d)
        pcm.append(resampled)
        clock = vocal_clock(resampled)
        # Independent absolute-level activity check prevents an inaudible
        # residual from becoming a full-volume singer via relative scaling.
        values = {k: np.pad(clock[k][:clock_count],(0,max(0,clock_count-len(clock[k])))) for k in ('energy','shapes','periodicity')}
        values['energy'] = np.where(mask, values['energy'], 0)
        values['shapes'] = np.where(mask, values['shapes'], 0)
        clocks.append(values)
        observations.append(dict(path=entry['path'], sha256=entry['sha256'], sample_rate=sr,
            duration_seconds=len(wave)/sr, rms_dbfs=round(20*np.log10(max(float(np.sqrt(np.mean(mono**2))),1e-12)),3),
            absolute_activity_seconds=round(sum(w.end_ms-w.start_ms for w in windows)/1000,3)))
    energy, shapes, screen = screen_candidate_lanes(
        np.column_stack([c['energy'] for c in clocks]),
        np.column_stack([c['shapes'] for c in clocks]),
        np.column_stack([np.clip(c['periodicity'],0,1) for c in clocks]))
    active=(energy>0)&(shapes!=0)
    count=min(map(len,pcm)); x,y=(p[:count].astype('float64') for p in pcm)
    denom=np.linalg.norm(x)*np.linalg.norm(y)
    correlation=float(abs(x@y)/denom) if denom else 0.
    seconds=active.sum(axis=0)/100
    overlap=float(active.all(axis=1).sum()/100)
    exclusive=float(np.logical_xor(*active.T).sum()/100)
    # Existing estimated-review criteria: >=2s per candidate and >=1s
    # both simultaneous and exclusive activity. Not release qualification.
    passes=bool(np.all(seconds>=2) and overlap>=1 and exclusive>=1 and correlation<.995)
    return dict(schema='helix.karaoke_candidate_qualification.v1', source_sha256=digest(audio),
        candidate_receipt_sha256=digest(receipt_path), source_duration_seconds=duration,
        candidates=observations, screened_activity_seconds=seconds.tolist(),
        screened_overlap_seconds=overlap, screened_exclusive_seconds=exclusive,
        absolute_pcm_correlation=correlation, confidence_screening=screen,
        estimated_review_activity_pass=passes, singer_identity_verified=False,
        independent_backing_verified=False, exact_phonemes_verified=False,
        status='estimated_activity_only' if passes else 'insufficient_distinct_activity')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('audio','stem_manifest','receipt','output'):
        p.add_argument(name,type=Path)
    a=p.parse_args(); report=qualify(a.audio,a.stem_manifest,a.receipt)
    a.output.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
