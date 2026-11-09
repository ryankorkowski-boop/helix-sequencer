"""Report the actual background-vocal classifier features on a song or stem.

Run from the repository root: python -m debug.bgvocal_diagnostics 'song.mp3'
By default, use the local HPSS/frequency-masked vocal proxy, just as generation
without Demucs does. --vocal-stem inspects an already separated vocal stem.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

import numpy as np

from core.audio_intelligence import (
    _background_vocal_frame_features, _local_stem_separation, load_audio_analysis_config,
)


def print_distributions(path: Path) -> None:
    threshold = load_audio_analysis_config().background_vocal_score_threshold
    features = _background_vocal_frame_features(path)
    print(f'Frames: {len(features.get("score", []))}')
    for name in ('rms01', 'multi_pitch01', 'chroma_entropy', 'score'):
        values = features.get(name, np.array([]))
        if not len(values):
            print(f'{name}: no frames')
            continue
        stats = np.quantile(values, [0, 0.5, 0.9, 1])
        print(f'{name}: min={stats[0]:.6f} median={stats[1]:.6f} p90={stats[2]:.6f} max={stats[3]:.6f}')
    if features:
        print(f'fraction score >= {threshold:.2f}: {np.mean(features["score"] >= threshold):.6f}')
        print(f'fraction multi_pitch01 >= 0.99: {np.mean(features["multi_pitch01"] >= 0.99):.6f}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('--vocal-stem', action='store_true')
    args = parser.parse_args()
    print(f'Audio: {args.audio}')
    if args.vocal_stem:
        print('Source: provided vocal stem')
        print_distributions(args.audio)
    else:
        print('Source: local HPSS/frequency-masked vocal proxy (not isolated voices)')
        with tempfile.TemporaryDirectory(prefix='helix-bgvocal-') as directory:
            stems = _local_stem_separation(args.audio, Path(directory), None)
            print_distributions(stems['vocals'])


if __name__ == '__main__':
    main()
