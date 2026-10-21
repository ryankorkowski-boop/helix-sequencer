"""Compile fresh separated sampler stems into the existing Helix band contract."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import librosa
import numpy as np
import soundfile as sf

from tools.analyze_band_upgrade import mono, curve, sha
from tools.analyze_band_instruments import estimate
from tools.analyze_band_samplers import mallet_cues
from models.band_instrument_logic import compile_note_events, event_curves, chord_route
from models.band_sampler_logic import held_bass_heights
from music.review_score import vocal_clock, pitched_roles
from tools.prepare_vocal_roles import prepare as prepare_voices


def analyze(root: Path) -> dict:
    root = root.resolve()
    audio = root / 'Helix_Starred_All_Songs.wav'
    stems = root / 'stems/htdemucs_6s' / audio.stem
    folder = root / 'analysis/sampler'
    folder.mkdir(parents=True, exist_ok=True)
    source = sha(audio)
    duration = sf.info(audio).duration
    n = math.ceil(duration * 20)
    waves = {kind: mono(stems / (kind + '.wav')) for kind in
             ('bass', 'guitar', 'piano', 'other', 'vocals')}
    if any(abs(len(w) / 16000 - duration) > .025 for w in waves.values()):
        raise ValueError('Separated stems must match the full sampler clock')
    arrays, events, counts = {}, {}, {}
    mallet, _, _, candidates = mallet_cues(waves['other'], waves['vocals'], n)
    arrays['keyboard_mallet_energy'] = mallet
    for kind in ('bass', 'guitar', 'piano', 'other'):
        notes, velocities, attacks, stats = estimate(waves[kind], n, kind)
        lane = compile_note_events(notes, velocities, attacks, kind + '_stem_harmonic_estimate')
        events[kind] = lane
        counts[kind] = dict(stats, events=len(lane))
        if kind == 'other':
            continue
        grid, velocity, attack, phase = event_curves(lane, n, 1 if kind == 'bass' else 6,
                                                    .22 if kind == 'bass' else .16)
        for name, value in [('notes', grid), ('note_levels', velocity), ('attack', attack),
                            ('phase', phase), ('energy', velocity.max(axis=1))]:
            arrays[kind + '_' + name] = value
        if kind != 'piano':
            routes = np.full((n, 1 if kind == 'bass' else 6, 3), -1, np.int16)
            for i, row in enumerate(grid):
                for j, route in enumerate(chord_route(tuple(int(x) for x in row if x >= 0), kind)):
                    routes[i, j] = route
            arrays[kind + '_routes'] = routes
        print(kind, len(lane), flush=True)
    arrays['bass_height'] = held_bass_heights(arrays['bass_notes'], arrays['bass_energy'])
    # Reuse the source classifier; never turn a mixed vocal bus into two people.
    config = root / 'vocal_sources.json'
    config.write_text(json.dumps(dict(source_audio=str(audio), duration=duration,
        tracks=[dict(name='mixed_vocals', path=str(stems / 'vocals.wav'), evidence='mixed')]), indent=2))
    voice_report = prepare_voices(config, folder)
    with np.load(folder / 'voice_roles.npz') as z:
        energy, shapes = z['energy'].copy(), z['shapes'].copy()
    arrays.update(vocal_energy=energy[:, 0], mouth_lanes=shapes,
                  vocal_route=np.zeros(n, np.int8), lexical_vocal_activity=np.zeros(n, bool))
    np.savez_compressed(folder / 'performance_curves.npz', **arrays)
    np.savez_compressed(folder / 'vocal_clock.npz', **vocal_clock(waves['vocals']))
    (folder / 'vocals.json').write_text(json.dumps(dict(audio_sha256=source,
        words=[], lines=[], mouths=[], verified_lyrics=False,
        method='source vocal stem acoustic visemes; no invented lexical transcription'), indent=2))
    (folder / 'note_events.json').write_text(json.dumps({k: [e.to_dict() for e in v]
        for k, v in events.items() if k != 'other'}, indent=2))
    onsets = librosa.onset.onset_detect(y=waves['piano'] + waves['other'], sr=16000,
                                       hop_length=160, units='time')
    keys, mallets, corrections = pitched_roles(events['piano'], events['other'], candidates,
                                              mallet, onsets, duration=duration)
    (folder / 'pitched_roles.json').write_text(json.dumps(dict(source_sha256=source,
        keyboard=[e.to_dict() for e in keys], mallets=[e.to_dict() for e in mallets],
        instrument_identity_verified=False, onset_corrections=len(corrections)), indent=2))
    report = dict(source_sha256=source, duration_seconds=duration, frames=n,
        stems={k: dict(sha256=sha(stems / (k + '.wav'))) for k in waves},
        mallet_attacks=candidates, notes=counts, vocals=voice_report,
        independent_backing_verified=False, musical_accuracy_independently_verified=False)
    (folder / 'verification.json').write_text(json.dumps(report, indent=2))
    source_folder = root / 'sources/sampler'
    source_folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio, source_folder / 'audio.wav')
    manifest = [dict(excerpt_id='sampler', filename='All 16 Starred songs',
                     sha256=source, start_seconds=0, end_seconds=duration)]
    (root / 'sources/selected_excerpts.json').write_text(json.dumps(manifest, indent=2))
    base = source_folder / 'base.xsq'
    xml = ET.Element('xsequence')
    ET.SubElement(xml, 'ElementEffects')
    ET.ElementTree(xml).write(base)
    # Feed the actual drum stem through the retained classifier and scheduler.
    from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3
    drums = inject_drummer_v3(base, source_folder / 'drummer.xsq', stems / 'drums.wav')
    (folder / 'drummer_analysis.json').write_text(json.dumps(drums, indent=2))
    print('analysis_complete', n, drums['event_count'], flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    analyze(p.parse_args().root)
