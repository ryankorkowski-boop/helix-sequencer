"""Reproduce optional source separation and acoustic clocks for the owner test.

Requires audio-separator0.47.1 with its CPU dependencies in a separate environment.
No model weights are redistributed. Outputs remain estimates requiring review.
"""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import numpy as np
from tools.phoneme_source import digest, EXPECTED_SHA256, FIXTURE

MODELS = {
    'UVR-MDX-NET-Inst_HQ_3.onnx': '317554b07fe1ea5279a77f2b1520a41ea4b93432560c4ffd08792c30fddf9adc',
    'UVR_MDXNET_KARA_2.onnx': 'bf32e15105a09c0f7dddd2b67346146334d6f3ecb399ed7638eba2ab07cbf5f4',
}


def separate(audio: Path, output: Path, models: Path):
    import librosa
    import soundfile as sf
    from audio_separator.separator import Separator
    from music.review_score import vocal_clock
    from music.vocal_roles import _duplicate
    from models.band_sampler_logic import SHAPE_NAMES
    if digest(audio) != EXPECTED_SHA256:
        raise ValueError('Original Phoneme Test Hook identity mismatch')
    output.mkdir(parents=True, exist_ok=False)
    models.mkdir(parents=True, exist_ok=True)
    separator = Separator(output_dir=str(output), model_file_dir=str(models),
                          output_format='WAV', normalization_threshold=1.0)
    def load(name):
        if (models / name).exists() and digest(models / name) != MODELS[name]:
            raise ValueError('Cached separation model hash mismatch: ' + name)
        separator.load_model(model_filename=name)
        if digest(models / name) != MODELS[name]:
            raise ValueError('Downloaded separation model hash mismatch: ' + name)
    load('UVR-MDX-NET-Inst_HQ_3.onnx')
    files = separator.separate(str(audio))
    vocals = next(output / name for name in files if '(Vocals)' in name)
    load('UVR_MDXNET_KARA_2.onnx')
    files = separator.separate(str(vocals))
    rows, arrays, waves = {}, {}, {}
    for role, marker in [('estimated_lead', '_(Vocals)_UVR_MDXNET_KARA_2'),
                         ('estimated_backing', '_(Instrumental)_UVR_MDXNET_KARA_2')]:
        original = next(output / name for name in files if marker in name)
        path = output / (role + '.wav')
        shutil.copyfile(original, path)
        y, _ = librosa.load(path, sr=16000, mono=True)
        clock = vocal_clock(y)
        waves[role] = y
        arrays.update({role+'_'+key:value for key,value in clock.items()})
        rows[role] = dict(file=path.name, sha256=digest(path), seconds=sf.info(path).duration,
                          voiced_seconds_estimate=float(np.count_nonzero(clock['energy'] > 0)/100),
                          rms=float(np.sqrt(np.mean(y*y))),
                          shape_counts={SHAPE_NAMES[i]:int(np.sum(clock['shapes'] == i)) for i in np.unique(clock['shapes'])})
    archive = output / 'acoustic_vocal_clocks.npz'
    np.savez_compressed(archive, **arrays)
    report = dict(schema='helix.phoneme-vocal-separation-diagnostic.v1', audio_sha256=EXPECTED_SHA256,
                  pipeline=list(MODELS), models=MODELS, tracks=rows, clock_sha256=digest(archive),
                  clock_hop_seconds=.01, analysis_estimates_not_ground_truth=True,
                  audio_separator_version=importlib.metadata.version('audio-separator'),
                  gain_or_short_delay_duplicate=_duplicate(*waves.values()),
                  independent_backing_verified=False, exact_phoneme_boundaries_verified=False,
                  limitation='Residual may contain lead/reverb/instrument leakage. Broad acoustic vowel colors are estimates, not verified individual singers or lexical phoneme boundaries.')
    (output / 'diagnostic.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--audio', type=Path, default=FIXTURE)
    parser.add_argument('--models', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(separate(args.audio.resolve(), args.output.resolve(), args.models.resolve()), indent=2))
