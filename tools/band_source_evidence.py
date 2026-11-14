"""Build and validate optional source-separated evidence for native band review."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json

import numpy as np
import soundfile as sf

from tools.phoneme_source import digest


def apply_evidence(plan, audio, evidence):
    """Replace only the four instrument cues when the evidence matches this audio."""
    payload = json.loads(Path(evidence).read_text())
    if payload.get('audio_sha256') != digest(audio):
        raise ValueError('Band instrument evidence has a different soundtrack')
    result = deepcopy(plan)
    duration = round(sf.info(audio).duration * 1000)
    for role in ('drummer', 'bassist', 'guitarist', 'keyboardist'):
        events = payload['cues'][role]
        if any(item.get('performer') != role or
               not 0 <= item['start_ms'] < item['end_ms'] <= duration for item in events):
            raise ValueError('Invalid source-bound instrument cue for ' + role)
        result['cues'][role] = events
    if 'bass_tuning_midi' in payload:
        tuning = payload['bass_tuning_midi']
        if (not isinstance(tuning, list) or len(tuning) != 4
                or any(type(pitch) is not int or not 12 <= pitch <= 60 for pitch in tuning)
                or tuning != sorted(set(tuning))):
            raise ValueError('Bass tuning requires four ascending, distinct open-string MIDI pitches')
        result['bass_tuning_midi'] = tuning
    return result


def instrument_evidence(audio, stems, transcript, output, *, bass_tuning_midi=None):
    from audio.drum_transcription import load_drum_transcription
    from core.snowman_band import _build_intelligent_drum_cues
    from audio.drum_classification import empty_drum_streams, stream_key_for_type
    from core.source_ownership import ownership_from_stem
    from dataclasses import asdict
    from models.band_instrument_logic import compile_note_events
    from tools.analyze_band_instruments import estimate
    from tools.analyze_band_upgrade import mono

    duration = sf.info(audio).duration
    duration_ms = round(duration * 1000)
    audio_hash = digest(audio)
    events, audit = load_drum_transcription(transcript, audio)
    source = json.loads(Path(transcript).read_text())
    if source['analysis_audio_sha256'] != digest(stems/'drums.wav'):
        raise ValueError('Drummer evidence was generated from a different drum stem')
    streams = empty_drum_streams()
    for event in events:
        if event.timestamp < duration:
            streams[stream_key_for_type(event.drum_type)].append(event)
    drums, _, _ = _build_intelligent_drum_cues(
        [SimpleNamespace(label='SOURCE', start_ms=0, end_ms=duration_ms)],
        drum_event_streams=streams, kicks=[], snares=[], hats=[], releases=[])
    cues = {'drummer': [dict(c, end_ms=min(duration_ms, c['end_ms']))
                        for c in drums if c['start_ms'] < duration_ms]}
    receipts = {}
    mix = mono(audio)
    mix_rms = float(np.sqrt(np.mean(mix**2)))
    for stem, role, kind in (('bass','bassist','pluck'), ('guitar','guitarist','picking'),
                             ('piano','keyboardist','pitched_note')):
        path = stems/(stem+'.wav')
        wave = mono(path)
        if abs(len(wave) - len(mix)) > 1:
            raise ValueError('Instrument stem has a different duration: ' + stem)
        relative = float(np.sqrt(np.mean(wave**2))) / max(mix_rms, 1e-9)
        cues[role] = []
        receipts[role] = dict(sha256=digest(path), rms_to_mix=relative, audible_candidate=relative >= .015)
        if relative < .015:
            continue
        notes, velocity, attacks, _ = estimate(wave, round(duration*20), stem)
        owner = asdict(ownership_from_stem(stem, .8))
        for event in compile_note_events(notes, velocity, attacks, stem+'_stem_harmonic_estimate'):
            start = round(event.start * 1000)
            end = min(duration_ms, round(event.end * 1000))
            if start >= end:
                continue
            cues[role].append(dict(performer=role, kind=kind, pitch_midi=event.pitch,
                                   velocity=event.velocity, start_ms=start, end_ms=end,
                                   source_start_ms=start, source_end_ms=end, source_owner=owner))
    receipt = dict(audio_sha256=audio_hash, cues=cues, stems=receipts,
                   drums=dict(source=source['provenance']['engine'],
                              rejected=audit['rejection_counts'], sha256=digest(stems/'drums.wav')))
    if bass_tuning_midi is not None:
        receipt['bass_tuning_midi'] = list(bass_tuning_midi)
    Path(output).write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def corroborate_vocals(audio, uvr, independent_vocals, output):
    """Require agreement with a separately separated vocal bus at the original clock."""
    from math import gcd
    from scipy.signal import resample_poly
    from music.review_score import vocal_clock
    from music.vocal_roles import _duplicate

    def mono16(path):
        signal, rate = sf.read(path, dtype='float32', always_2d=True)
        common = gcd(rate, 16000)
        return resample_poly(signal.mean(axis=1), 16000//common, rate//common)

    receipt = json.loads((uvr/'diagnostic.json').read_text())
    if receipt['audio_sha256'] != digest(audio):
        raise ValueError('Vocal evidence has a different soundtrack')
    clock_path = uvr/'acoustic_vocal_clocks.npz'
    names = ('estimated_lead','estimated_backing')
    paths = [uvr/(name+'.wav') for name in names]
    if receipt['clock_sha256'] != digest(clock_path) or any(
            receipt['tracks'][name]['sha256'] != digest(path) for name, path in zip(names, paths)):
        raise ValueError('Vocal clocks or separated tracks do not match their receipt')
    vocal_ref = mono16(independent_vocals)
    reference = vocal_clock(vocal_ref)
    with np.load(clock_path, allow_pickle=False) as source:
        arrays = {key: source[key].copy() for key in source.files}
    waves = [mono16(path) for path in paths]
    if any(len(wave) != len(vocal_ref) for wave in waves):
        raise ValueError('Vocal candidate durations differ')
    duplicate = _duplicate(*waves)
    raw_clocks = [vocal_clock(wave) for wave in waves]

    def frames(signal):
        padded = np.pad(signal, (640, 640))
        return np.lib.stride_tricks.sliding_window_view(padded, 1280)[::160][:len(reference['energy'])]

    target = frames(vocal_ref)
    target_rms = np.sqrt(np.mean(target**2, axis=1))
    for index, (name, wave, clock) in enumerate(zip(names, waves, raw_clocks)):
        candidate = frames(wave)
        candidate_rms = np.sqrt(np.mean(candidate**2, axis=1))
        agreement = np.mean(candidate * target, axis=1) / np.maximum(1e-9, candidate_rms * target_rms)
        proportion = candidate_rms / np.maximum(1e-6, target_rms)
        supported = ((target_rms >= .012) & (agreement >= (.65 if index else .50))
                     & (proportion >= (.24 if index else .18))
                     & (clock['periodicity'] >= .37) & (clock['energy'] > 0))
        if index and duplicate:
            supported[:] = False
        arrays[name+'_energy'] = np.where(supported, clock['energy'], 0)
        arrays[name+'_shapes'] = np.where(supported, clock['shapes'], 0)
        arrays[name+'_acoustic_corroboration'] = np.where(supported, np.clip(agreement, .70, 1), 0)
    output.mkdir(parents=True, exist_ok=True)
    archive = output/'acoustic_vocal_clocks.npz'
    np.savez_compressed(archive, **arrays)
    receipt.update(clock_sha256=digest(archive), independent_vocal_bus_sha256=digest(independent_vocals),
                   vocal_corroboration='aligned waveform and voiced energy agreement across UVR and Demucs',
                   limitation='Model-derived acoustic vocal activity. Singer identity and lexical phonemes remain unverified.')
    (output/'diagnostic.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    instruments = commands.add_parser('instruments')
    for name in ('audio', 'stems', 'transcript', 'output'):
        instruments.add_argument(name, type=Path)
    instruments.add_argument('--bass-tuning-midi', type=int, nargs=4)
    vocals = commands.add_parser('vocals')
    for name in ('audio', 'uvr', 'independent_vocals', 'output'):
        vocals.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.command == 'instruments':
        instrument_evidence(args.audio, args.stems, args.transcript, args.output,
                            bass_tuning_midi=args.bass_tuning_midi)
    else:
        corroborate_vocals(args.audio, args.uvr, args.independent_vocals, args.output)
