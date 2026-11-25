"""Run the pinned karaoke model on a verified Demucs vocal stem, offline.

The two outputs are model candidates, not verified individual singer identities.
The input manifest must be source-bound; no normalizing the original stems to
manufacture activity. Raw native separator outputs and their hashes are retained.
"""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import re

from tools.phoneme_source import digest
from tools.qualified_keyboard import verified_piano
from tools.separate_vocal_roles import MODEL

CONFIG = MODEL.removesuffix('.ckpt') + '_config.yaml'


def validate_files(model_dir, expected):
    model_dir, expected = Path(model_dir).resolve(), dict(expected)
    if set(expected) != {MODEL, CONFIG} or any(not re.fullmatch('[0-9a-f]{64}', x) for x in expected.values()):
        raise ValueError('Both full checkpoint and config digests are required')
    for name, sha in expected.items():
        if digest(model_dir/name) != sha:
            raise ValueError('Offline model checksum mismatch: '+name)
    return model_dir


def local_descriptor(model_dir, filename):
    if filename != MODEL:
        raise ValueError('Unexpected karaoke checkpoint request')
    return MODEL, 'MDXC', 'Pinned local Mel-Roformer karaoke', str(model_dir/MODEL), str(model_dir/CONFIG)


def run(audio, stem_manifest, model_dir, output, expected):
    import soundfile as sf
    audio, stem_manifest, output = map(lambda p: Path(p).resolve(), (audio, stem_manifest, output))
    # Reuse the six-stem verifier to check all source hashes, not just vocals.
    verified_piano(audio, stem_manifest)
    manifest = json.loads(stem_manifest.read_text())
    vocals = (stem_manifest.parent/manifest['tracks']['vocals']['path']).resolve()
    duration = sf.info(audio).duration
    info = sf.info(vocals)
    if info.samplerate != 44100 or info.channels != 2 or abs(info.duration-duration) > .05:
        raise ValueError('Combined vocal clock differs from original source')
    model_dir = validate_files(model_dir, expected)
    if importlib.metadata.version('audio-separator') != '0.41.1':
        raise ValueError('Offline adapter expects audio-separator 0.41.1')
    from tools.offline_vocal_candidates import deny_network
    deny_network()
    import onnxruntime as ort
    ort.disable_telemetry_events()
    import torch
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    from audio_separator.separator import Separator
    class LocalSeparator(Separator):
        def download_model_files(self, model_filename):
            return local_descriptor(model_dir, model_filename)
    output.mkdir(parents=True, exist_ok=False)
    separator = LocalSeparator(model_file_dir=str(model_dir), output_dir=str(output),
        output_format='WAV', use_soundfile=True, normalization_threshold=1.0,
        amplification_threshold=0.0)
    separator.load_model(MODEL)
    paths = separator.separate(str(vocals))
    tracks = []
    for name in paths:
        p = (output/Path(name).name).resolve()
        if not p.is_relative_to(output) or not p.is_file() or abs(sf.info(p).duration-duration) > .05:
            raise ValueError('Unexpected karaoke output or duration')
        tracks.append({'path': p.name, 'sha256': digest(p)})
    if len(tracks) != 2 or len({r['sha256'] for r in tracks}) != 2:
        raise ValueError('Expected two distinct model outputs')
    report = dict(schema='helix.offline_karaoke_candidates.v1', source_sha256=digest(audio),
        combined_vocals_sha256=digest(vocals), stem_manifest_sha256=digest(stem_manifest),
        models=expected, outputs=tracks, source_duration_seconds=duration,
        identity_verified=False, status='unmapped_model_candidates', network='denied')
    (output/'candidate_receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('audio', 'stem_manifest', 'model_dir', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--checksums', required=True, type=Path)
    a = p.parse_args()
    hashes = {Path(name).name: sha for sha, name in (line.split(None, 1) for line in a.checksums.read_text().splitlines())}
    print(json.dumps(run(a.audio, a.stem_manifest, a.model_dir, a.output, hashes), indent=2))
