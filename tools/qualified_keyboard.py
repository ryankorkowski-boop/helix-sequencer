"""Optional six-source Demucs keyboard evidence; do not relabel mixed notes.

The checkpoint hash prefix is the one embedded in upstream Demucs' filename.
Pitch confidence remains the existing Helix magnitude heuristic, not a
calibrated probability of acoustic instrument identity.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

from tools.phoneme_source import digest

MODEL = 'htdemucs_6s'
WEIGHT = '5c90dfd2-34c22ccb.th'
WEIGHT_SHA256 = '34c22ccb381c6f9fdbf324f04e1e2fe21aaaf293f5ded163a162697ff9a02ddd'
ROLES = ('vocals', 'drums', 'bass', 'other', 'guitar', 'piano')


def separate(audio: Path, output: Path, weight: Path) -> Path:
    import soundfile as sf
    audio, output, weight = (Path(p).resolve() for p in (audio, output, weight))
    weight_sha = digest(weight)
    if weight.name != WEIGHT or weight_sha != WEIGHT_SHA256:
        raise ValueError('Wrong six-source Demucs checkpoint')
    output.mkdir(parents=True, exist_ok=False)
    # Supply the verified checkpoint via Demucs' local model repository,
    # so inference cannot silently substitute another network.
    repo = output / 'model'
    repo.mkdir()
    (repo / (MODEL + '.yaml')).write_text("models: ['5c90dfd2']\n")
    import shutil
    shutil.copyfile(weight, repo / WEIGHT)
    source_sha = digest(audio)
    # PyTorch >=2.6 defaults to weights-only. Allow only the two classes
    # declared in this pinned official checkpoint, not arbitrary pickle code.
    loader = ("import torch; from demucs.htdemucs import HTDemucs; "
              "from fractions import Fraction; from demucs.separate import main; "
              "torch.serialization.add_safe_globals([HTDemucs, Fraction]); main()")
    subprocess.run([sys.executable, '-c', loader, '--repo', str(repo),
                    '-n', MODEL, '--device', 'cpu', '--shifts', '0',
                    '--overlap', '.1', '--segment', '7', '-j', '0',
                    '-o', str(output / 'stems'), str(audio)], check=True)
    folder = output / 'stems' / MODEL / audio.stem
    duration = sf.info(audio).duration
    tracks = {}
    for role in ROLES:
        path = folder / (role + '.wav')
        info = sf.info(path)
        if info.samplerate != 44100 or info.channels != 2 or abs(info.duration-duration) > .05:
            raise ValueError('Invalid stem clock: ' + role)
        tracks[role] = {'path': str(path.relative_to(output)), 'sha256': digest(path)}
    if digest(audio) != source_sha:
        raise ValueError('Audio changed during separation')
    manifest = output / 'keyboard_stems.json'
    manifest.write_text(json.dumps(dict(schema='helix.keyboard_stems.v1', model=MODEL,
        source_sha256=source_sha, weight_sha256=weight_sha, tracks=tracks,
        instrument_identity_verified=False), indent=2)+'\n')
    return manifest


def verified_piano(audio, manifest):
    import soundfile as sf
    audio, manifest = Path(audio), Path(manifest)
    root = manifest.resolve().parent
    data = json.loads(manifest.read_text())
    if (data.get('schema') != 'helix.keyboard_stems.v1' or data.get('model') != MODEL
            or data.get('source_sha256') != digest(audio)
            or data.get('weight_sha256') != WEIGHT_SHA256):
        raise ValueError('Foreign or unqualified keyboard stem evidence')
    tracks = data['tracks']
    if set(tracks) != set(ROLES):
        raise ValueError('Incomplete six-source separation')
    hashes = set()
    for role, entry in tracks.items():
        path = (root / entry['path']).resolve()
        if not path.is_relative_to(root) or path.name != role+'.wav' or digest(path) != entry['sha256']:
            raise ValueError('Invalid or changed source stem: '+role)
        hashes.add(entry['sha256'])
        if role == 'piano':
            piano = path
    if len(hashes) != len(ROLES):
        raise ValueError('Duplicated source stems')
    info = sf.info(piano)
    if info.channels != 2 or info.samplerate != 44100 or abs(info.duration-sf.info(audio).duration) > .05:
        raise ValueError('Piano clock differs from source')
    return piano


def cues(audio, manifest):
    import numpy as np
    import soundfile as sf
    from core.audio_intelligence import _extract_note_candidates, AudioAnalysisConfig
    from core.snowman_band import _build_keyboard_note_cues
    piano = verified_piano(audio, manifest)
    y, sr = sf.read(piano, dtype='float32', always_2d=True)
    y = y.mean(axis=1)
    if not np.isfinite(y).all():
        raise ValueError('Nonfinite piano samples')
    # The existing pitch confidence is relative to peak magnitude, so do
    # not normalize numerical residual/silent stems into active notes.
    if not len(y) or float(np.sqrt(np.mean(y*y))) < .0005:
        return [], {'status':'inaudible_stem_abstention', 'accepted':0,
                    'instrument_identity_verified':False}
    events, _ = _extract_note_candidates(y, sr, source_stem='piano', config=AudioAnalysisConfig())
    selected = _build_keyboard_note_cues(events, [], require_source_ownership=True)
    duration = round(len(y)/sr*1000)
    selected = [dict(e, end_ms=min(e['end_ms'], duration)) for e in selected
                if 21 <= e['pitch_midi'] <= 108 and 0 <= e['start_ms'] < duration]
    return selected, dict(status='estimated_stem_notes', candidates=len(events), accepted=len(selected),
        stem_sha256=digest(piano), manifest_sha256=digest(Path(manifest)),
        instrument_identity_verified=False, confidence_kind='relative pitch magnitude, not calibrated ownership')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path); p.add_argument('output', type=Path)
    p.add_argument('weight', type=Path)
    a = p.parse_args(); print(separate(a.audio, a.output, a.weight))
