"""Align original waveform evidence with before/after family and target decisions."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks, stft


def audit(audio, before_path, after_path, output):
    before, after = (json.loads(Path(p).read_text()) for p in (before_path, after_path))
    digest = hashlib.sha256(Path(audio).read_bytes()).hexdigest()
    assert before['analysis']['audio_sha256'] == after['analysis']['audio_sha256'] == digest
    original, sr = sf.read(audio, always_2d=True)
    original = original.mean(axis=1)
    start, end = after['analysis']['source_calibration']['scope_seconds']
    # Source timing evidence is independent of either network's timestamps.
    hop = round(sr / 1000)
    envelope = np.sqrt((original[:len(original)//hop*hop].reshape(-1, hop)**2).mean(axis=1))
    rises = np.maximum(np.diff(uniform_filter1d(envelope, 4), prepend=0), 0)
    peaks, _ = find_peaks(rises, distance=55, prominence=.003)
    peak_times = (peaks + .5) * hop / sr
    prior = {r['source_onset_index']: r for r in before['analysis']['onset_audit']}
    changes = []
    for row in after['analysis']['onset_audit']:
        decision = row['primary'].get('source_calibration')
        if not decision:
            continue
        old = prior[row['source_onset_index']]
        nearby = peak_times[np.abs(peak_times - row['timestamp']) <= .04]
        source_attack = float(nearby[np.argmin(np.abs(nearby - row['timestamp']))]) if len(nearby) else None
        changes.append(dict(timestamp=row['timestamp'], source_onset_index=row['source_onset_index'],
                            independent_source_attack=source_attack,
                            timing_error_ms=(row['timestamp']-source_attack)*1000 if source_attack is not None else None,
                            before=dict(family=old['drum_family'], rejection=old['rejection_reason'], target=old['physical_target']),
                            after=dict(family=row['drum_family'], tom_class=row['primary']['tom_class'],
                                       rejection=row['rejection_reason'], scheduler=row['scheduler_decision'],
                                       target=row['physical_target']), source_calibration=decision))
    summary = dict(audio_sha256=digest, scope_seconds=[start, end],
                   before_scheduled=before['event_count'], after_scheduled=after['event_count'],
                   before_counts=before['scheduled_drum_type_counts'], after_counts=after['scheduled_drum_type_counts'],
                   changes=changes, correction_decisions=dict(Counter(r['after']['scheduler'] for r in changes)),
                   review_status="source_inspected_inference_pending_user_listening",
                   limitation="Family label comes from user passage listening; individual inferred matches and rendered animation still await approval.")
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    (output / 'Before_After.json').write_text(json.dumps(summary, indent=2)+'\n')
    with (output / 'Source_Calibration_Audit.csv').open('w', newline='') as handle:
        columns = ['timestamp', 'source_onset_index', 'independent_source_attack', 'timing_error_ms',
                   'original_family', 'original_rejection', 'tom_class', 'physical_target',
                   'scheduler', 'similarity', 'margin', 'exemplar_timestamp']
        writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader()
        for row in changes:
            writer.writerow(dict(timestamp=row['timestamp'], source_onset_index=row['source_onset_index'],
                                 independent_source_attack=row['independent_source_attack'], timing_error_ms=row['timing_error_ms'],
                                 original_family=row['before']['family'], original_rejection=row['before']['rejection'],
                                 tom_class=row['after']['tom_class'], physical_target=row['after']['target'],
                                 scheduler=row['after']['scheduler'], similarity=row['source_calibration']['similarity'],
                                 margin=row['source_calibration']['margin'], exemplar_timestamp=row['source_calibration']['exemplar']['timestamp']))
    plot_start, plot_end = 31.8, 35.65
    clip = original[round(plot_start*sr):round(plot_end*sr)]
    freqs, times, spec = stft(clip, sr, nperseg=2048, noverlap=1792)
    times += plot_start
    fig, axes = plt.subplots(5, 1, figsize=(16, 12), sharex=True)
    axes[0].plot(np.arange(len(clip))/sr+plot_start, clip, lw=.4)
    axes[0].set_ylabel('Original waveform')
    axes[1].pcolormesh(times, freqs, 20*np.log10(np.maximum(abs(spec), 1e-8)),
                       vmin=-75, vmax=-12, shading='auto')
    axes[1].set_ylim(0, 1800); axes[1].set_ylabel('Original Hz')
    for lo, hi in ((60, 400), (400, 1000), (1000, 5000), (5000, 16000)):
        energy = (abs(spec[(freqs >= lo)&(freqs < hi)])**2).sum(axis=0)
        axes[2].plot(times, energy, label=f'{lo}–{hi} Hz')
    axes[2].legend(ncol=4); axes[2].set_ylabel('Source band energy')
    targets = ['KICK', 'SNARE', 'HI_HAT', 'TOM_HIGH', 'TOM_MID', 'TOM_FLOOR', 'CYMBAL_LEFT', 'CYMBAL_RIGHT']
    for ax, report, title in ((axes[3], before, 'Before: physical hits'), (axes[4], after, 'After: physical hits')):
        for row in report['event_audit']:
            if not row['scheduled']:
                continue
            target = row['physical_component'].removeprefix('HX_SNOWMAN_DRUMMER_V3_')
            if target in targets:
                ax.scatter(row['timestamp'], targets.index(target), s=26)
        ax.set_yticks(range(len(targets)), targets); ax.set_ylabel(title)
    for row in changes:
        for ax in axes:
            ax.axvline(row['timestamp'], color='#cf743a', alpha=.25, lw=.5)
    for ax in axes:
        ax.set_xlim(plot_start, plot_end); ax.grid(alpha=.12)
    axes[-1].set_xlabel('Original source seconds; user-labelled high-tom passage, animation awaits approval')
    fig.suptitle('Missed ending attacks: source evidence and physical placements')
    fig.tight_layout(); fig.savefig(output/'Ending_Before_After.png'); plt.close(fig)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path); p.add_argument('before', type=Path); p.add_argument('after', type=Path)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    result = audit(args.audio, args.before, args.after, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'changes'}, indent=2))
