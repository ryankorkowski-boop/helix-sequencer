"""Refine source-stem performance curves; conservative vocal-style routing."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import librosa
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'outputs/Snowman_Ensemble'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mono(path):
    a, sr = sf.read(path, dtype='float32')
    if a.ndim == 2:
        a = a.mean(axis=1)
    return librosa.resample(a, orig_sr=sr, target_sr=16000)


def curve(a, n):
    rms = librosa.feature.rms(y=a, frame_length=2048, hop_length=800)[0]
    rms = np.pad(rms, (0, max(0, n-len(rms))))[:n]
    floor = max(.0015, float(np.quantile(rms, .15)) * .7)
    top = max(floor * 3, float(np.quantile(rms, .97)))
    energy = np.clip((rms-floor)/(top-floor), 0, 1)
    # Only measured attacks move the picking hand; sustained energy stays visible.
    attacks = librosa.onset.onset_detect(y=a, sr=16000, hop_length=800,
                                        backtrack=False, units='frames',
                                        delta=.045, wait=2)
    attack = np.zeros(n, dtype=np.float32)
    for i in attacks:
        if i < n and energy[i] > .09:
            for j, value in enumerate((1., .8, .45, .15)):
                if i+j < n:
                    attack[i+j] = max(attack[i+j], value * energy[i])
    return energy, attack, rms


def pitch_notes(a, n, kind):
    if kind == 'bass':
        f0, voiced, probability = librosa.pyin(a, fmin=32.7, fmax=392., sr=16000,
                                              frame_length=2048, hop_length=800)
        notes = np.full((n, 6), -1, dtype=np.int16)
        size = min(n, len(f0))
        valid = np.isfinite(f0[:size]) & voiced[:size] & (probability[:size] >= .55)
        midi = np.zeros(size, dtype=np.int16)
        midi[valid] = np.rint(librosa.hz_to_midi(f0[:size][valid])).astype(np.int16)
        midi = median_filter(midi, size=3)
        valid &= midi >= 28
        notes[np.flatnonzero(valid), 0] = midi[valid]
        return notes
    spectrum = np.abs(librosa.cqt(a, sr=16000, hop_length=800,
                                  fmin=librosa.midi_to_hz(36), n_bins=60))
    notes = np.full((n, 6), -1, dtype=np.int16)
    for i in range(min(n, spectrum.shape[1])):
        column = spectrum[:, i]
        peaks, _ = find_peaks(column, distance=2, height=float(column.max())*.32)
        selected = sorted(peaks, key=lambda k: column[k], reverse=True)[:6]
        # CQT candidates can be overtones. Reject near-exact overtones of an
        # already stronger lower note rather than claiming six independent notes.
        kept = []
        for k in sorted(selected):
            hz = librosa.midi_to_hz(36+k)
            if any(abs(hz/librosa.midi_to_hz(36+j)-round(hz/librosa.midi_to_hz(36+j))) < .025
                   for j in kept):
                continue
            kept.append(k)
        for j, k in enumerate(kept[:6]):
            notes[i, j] = 36+k
    return notes


def route_vocals(a, vocals, n, encoder):
    candidates, embeddings = [], []
    for line in vocals['lines']:
        start, end = line['start_ms']/1000, line['end_ms']/1000
        if end-start < .65:
            continue
        clip = a[round(start*16000):round(min(end, start+5)*16000)]
        if len(clip) < 10400 or np.sqrt(np.mean(clip*clip)) < .006:
            continue
        with torch.inference_mode():
            e = encoder.encode_batch(torch.from_numpy(clip).unsqueeze(0)).cpu().numpy().ravel()
        e /= max(np.linalg.norm(e), 1e-9)
        embeddings.append(e); candidates.append(dict(line))
    routes = np.zeros(n, dtype=np.int8)
    proof = {'model': 'speechbrain/spkrec-ecapa-voxceleb',
             'model_revision': '0f99f2d0ebe89ac095bcc5903c4dd8f72b367286',
             'method': 'phrase-level normalized speaker embeddings / conservative two-style clustering',
             'gender_or_identity_inferred': False, 'overlapping_voices_separated': False,
             'two_voice_candidates': False, 'phrase_count': len(candidates), 'phrases': []}
    if len(embeddings) < 8:
        proof['fallback'] = 'insufficient independent voiced phrases; lead character only'
        return routes, proof
    e = np.array(embeddings)
    fit = KMeans(n_clusters=2, random_state=7, n_init=10).fit(e)
    labels = fit.labels_
    counts = np.bincount(labels, minlength=2)
    centers = np.array([e[labels == k].mean(axis=0) for k in range(2)])
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)
    separation = float(1-np.dot(*centers))
    silhouette = float(silhouette_score(e, labels, metric='cosine'))
    accepted = bool(counts.min() >= 3 and separation > .40 and silhouette > .28)
    proof.update(cluster_phrase_counts=counts.tolist(), cosine_separation=separation,
                 silhouette=silhouette, two_voice_candidates=accepted)
    lead = int(np.argmax(counts))
    for line, vector, label in zip(candidates, e, labels):
        margins = vector @ centers.T
        confident = bool(abs(margins[0]-margins[1]) > .12)
        slot = 1 if accepted and confident and label != lead else 0
        lo, hi = max(0, line['start_ms']//50), min(n, (line['end_ms']+49)//50)
        routes[lo:hi] = slot
        proof['phrases'].append(dict(line, character_slot=slot,
                                     embedding_cluster=int(label), confident=confident))
    proof['fallback'] = ('uncertain phrases use lead character' if accepted else
                         'no sufficiently stable second voice profile; lead character only')
    proof['casting'] = 'most frequent profile -> male character; alternate -> female character; authored casting, not gender classification'
    return routes, proof


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', nargs='+', default=['00','01','02','03','04','05'])
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/Snowman_Band_Upgrade/analysis')
    args = parser.parse_args()
    from speechbrain.inference.speaker import EncoderClassifier
    encoder = EncoderClassifier.from_hparams(source='/workspace/runtime/speaker_ecapa',
                                              savedir='/workspace/runtime/speaker_ecapa',
                                              run_opts={'device':'cpu'})
    sources = json.loads((OLD/'sources.json').read_text())
    for row in sources:
        if row['id'] not in args.ids:
            continue
        output = args.output/row['id']; output.mkdir(parents=True, exist_ok=True)
        if (output/'verification.json').exists():
            continue
        stem_name = Path(row['path']).stem
        stems = OLD/'stems/htdemucs_6s'/stem_name
        original = OLD/'shows'/f'{row["id"]}_band/media/song.mp3'
        assert sha(original) == row['sha256']
        n = math_ceil_frames(row['duration'])
        arrays = {}; proof = {'source_sha256': row['sha256'], 'frame_ms': 50,
                              'note_method': 'bass probabilistic YIN; guitar/piano CQT pitch candidates with overtone rejection',
                              'verified_musical_score': False, 'stems': {}}
        for kind in ('bass','guitar','piano'):
            source = stems/(kind+'.wav'); a = mono(source)
            energy, attack, rms = curve(a, n)
            notes = pitch_notes(a, n, kind)
            notes[energy < .09] = -1
            arrays[kind+'_energy'] = energy; arrays[kind+'_attack'] = attack
            arrays[kind+'_notes'] = notes
            proof['stems'][kind] = {'sha256': sha(source), 'active_frames': int((energy>.09).sum()),
                                     'pitch_candidate_frames': int(np.any(notes>=0, axis=1).sum())}
        vocal_source = stems/'vocals.wav'; vocals = json.loads((OLD/'analysis'/row['id']/'vocals.json').read_text())
        a = mono(vocal_source)
        arrays['vocal_energy'], _, _ = curve(a, n)
        arrays['vocal_route'], routing = route_vocals(a, vocals, n, encoder)
        proof['vocal_stem_sha256'] = sha(vocal_source); proof['vocal_routing'] = routing
        np.savez_compressed(output/'performance_curves.npz', **arrays)
        (output/'verification.json').write_text(json.dumps(proof, indent=2)+'\n')
        print(row['id'], row['title'], {k:v['active_frames'] for k,v in proof['stems'].items()},
              'two voice candidates:', routing['two_voice_candidates'], flush=True)


def math_ceil_frames(duration):
    return int(np.ceil(duration*20))


if __name__ == '__main__':
    main()
