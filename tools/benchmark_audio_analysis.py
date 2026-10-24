"""Reproduce warmed DSP timing and feature equivalence against a Git revision.

Usage: python -m tools.benchmark_audio_analysis fixtures/audio/Phoneme_Test_Hook.mp3
       --baseline-ref 8c61452713bd06273e94e8607a828c8341ada9f3 --report benchmark.json
Only trusted repository revisions should be executed as a baseline.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

import numpy as np
from xlights import xsq_writer
from tools.phoneme_source import digest


def benchmark(audio: Path, baseline_ref: str, repeats: int = 3) -> dict:
    source_hash = digest(audio)
    code = subprocess.check_output(['git', 'show', baseline_ref + ':xlights/xsq_writer.py'], text=True)
    with tempfile.TemporaryDirectory(prefix='helix-dsp-baseline-') as folder:
        path = Path(folder) / 'baseline.py'
        path.write_text(code)
        spec = importlib.util.spec_from_file_location('helix_dsp_baseline', path)
        baseline = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = baseline
        spec.loader.exec_module(baseline)
        # The first pass includes native-code import/JIT caches for both paths.
        baseline.analyze(audio)
        xsq_writer.analyze(audio)
        timings = {'baseline': [], 'candidate': []}
        for _ in range(repeats):
            for key, module in [('baseline', baseline), ('candidate', xsq_writer)]:
                began = time.perf_counter()
                result = module.analyze(audio)
                timings[key].append(time.perf_counter() - began)
                if key == 'baseline':
                    previous = result
                else:
                    assert result.onset_ms == previous.onset_ms
                    assert result.beat_ms == previous.beat_ms
                    for name in ('y', 'times_s', 'centroid', 'rms01', 'bass01', 'vocal01', 'pitch_hz'):
                        np.testing.assert_array_equal(getattr(result, name), getattr(previous, name))
        assert digest(audio) == source_hash
        medians = {k: statistics.median(v) for k, v in timings.items()}
        return dict(audio_sha256=source_hash, duration_seconds=result.dur_s, baseline_ref=baseline_ref,
                    timings_seconds=timings, medians_seconds=medians,
                    speedup=medians['baseline']/medians['candidate'],
                    exact_feature_and_event_equivalence=True, source_unchanged=True,
                    scope='xsq_writer.analyze only; full production CLI includes harmonic/stem/routing work')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('--baseline-ref', required=True)
    parser.add_argument('--repeats', type=int, choices=range(1, 11), default=3)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = benchmark(args.audio, args.baseline_ref, args.repeats)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
