"""Reconstruct hash-pinned vocal candidates with networking denied during inference.

This optional analysis produces estimates, never evidence of individual singers.
Weights must already exist locally; this command never downloads them.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
from pathlib import Path
import socket
import sys

import numpy as np
from scipy.signal import get_window, resample_poly
import soundfile as sf

from tools.phoneme_source import EXPECTED_SHA256, digest

MODELS = {
    'UVR-MDX-NET-Inst_HQ_3.onnx': ('317554b07fe1ea5279a77f2b1520a41ea4b93432560c4ffd08792c30fddf9adc', 6144, 3072, 1.022),
    'UVR_MDXNET_KARA_2.onnx': ('bf32e15105a09c0f7dddd2b67346146334d6f3ecb399ed7638eba2ab07cbf5f4', 5120, 2048, 1.065),
}
VAD_SHA256 = '1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3'


def deny_network():
    """Add a Linux process restriction; fail closed if it cannot be installed."""
    if sys.platform != 'linux':
        raise RuntimeError('Offline inference requires the Linux network restriction')
    lib = ctypes.CDLL('libseccomp.so.2', use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)
    if not ctx:
        raise RuntimeError('Could not initialize offline inference restriction')
    try:
        for name in (b'socket', b'connect', b'sendto', b'sendmsg'):
            number = lib.seccomp_syscall_resolve_name(name)
            if number < 0 or lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0):
                raise RuntimeError('Could not deny network syscall ' + name.decode())
        if lib.seccomp_load(ctx):
            raise RuntimeError('Could not enforce offline inference restriction')
    finally:
        lib.seccomp_release(ctx)
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except PermissionError:
        return
    else:
        probe.close()
        raise RuntimeError('Offline restriction probe unexpectedly succeeded')


def stft(wave, n_fft, hop=1024):
    padded = np.pad(wave, ((0, 0), (n_fft // 2, n_fft // 2)), mode='reflect')
    frames = np.lib.stride_tricks.sliding_window_view(padded, n_fft, axis=-1)[:, ::hop]
    return np.fft.rfft(frames * get_window('hann', n_fft), axis=-1).transpose(0, 2, 1)


def istft(spectrum, n_fft, hop=1024):
    frames = np.fft.irfft(spectrum.transpose(0, 2, 1), n=n_fft, axis=-1)
    window = get_window('hann', n_fft)
    size = (frames.shape[1] - 1) * hop + n_fft
    output = np.zeros((frames.shape[0], size))
    weight = np.zeros(size)
    for i in range(frames.shape[1]):
        start = i * hop
        output[:, start:start+n_fft] += frames[:, i] * window
        weight[start:start+n_fft] += window ** 2
    output /= np.maximum(weight, 1e-12)
    return output[:, n_fft//2:-n_fft//2].astype('f4')


def separate(wave, path, n_fft, dim_f, ort):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])
    chunk, trim = 1024 * 255, n_fft // 2
    step = chunk * 3 // 4
    padded = np.pad(wave, ((0, 0), (trim, chunk)))
    output = np.zeros_like(padded)
    weights = np.zeros(padded.shape[-1], 'f4')
    for start in range(0, padded.shape[-1], step):
        length = min(chunk, padded.shape[-1] - start)
        block = np.pad(padded[:, start:start+length], ((0, 0), (0, chunk-length)))
        spectrum = stft(block, n_fft)
        channels = np.stack((spectrum.real, spectrum.imag), axis=1).reshape(4, n_fft//2+1, 256)
        tensor = channels[None, :, :dim_f].astype('f4')
        tensor[:, :, :3] = 0
        predicted = session.run(None, {session.get_inputs()[0].name: tensor})[0]
        full = np.zeros((4, n_fft//2+1, 256), 'f4')
        full[:, :dim_f] = predicted[0]
        complex_spectrum = full.reshape(2, 2, n_fft//2+1, 256)
        decoded = istft(complex_spectrum[:, 0] + 1j * complex_spectrum[:, 1], n_fft)
        window = np.hanning(length).astype('f4')
        output[:, start:start+length] += decoded[:, :length] * window
        weights[start:start+length] += window
        print(path.name, start, padded.shape[-1], flush=True)
    return (output / np.maximum(weights, 1e-9))[:, trim:trim+wave.shape[-1]]


def vad(wave, path, ort):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])
    mono = resample_poly(wave.mean(axis=0), 160, 441).astype('f4')
    state = np.zeros((2, 1, 128), 'f4')
    context = np.zeros((1, 64), 'f4')
    values = []
    for start in range(0, len(mono), 512):
        block = np.pad(mono[start:start+512], (0, max(0, start+512-len(mono))))[None]
        value, state = session.run(None, {'input': np.concatenate((context, block), axis=1),
                                          'state': state, 'sr': np.array(16000, dtype='i8')})
        values.append(float(value.reshape(-1)[0]))
        context = block[:, -64:]
    return np.asarray(values, 'f4')


def run(audio, output, models):
    if digest(audio) != EXPECTED_SHA256:
        raise ValueError('Original owner source hash mismatch')
    for name, (sha, *_parameters) in MODELS.items():
        if digest(models / name) != sha:
            raise ValueError('Model checksum mismatch: ' + name)
    if digest(models / 'silero_vad.onnx') != VAD_SHA256:
        raise ValueError('VAD model checksum mismatch')
    output.mkdir(parents=True, exist_ok=False)
    wave, sr = sf.read(audio, dtype='float32', always_2d=True)
    if sr != 44100:
        from math import gcd
        common = gcd(sr, 44100)
        wave = resample_poly(wave, 44100//common, sr//common, axis=0)
    wave = wave.T
    deny_network()
    import onnxruntime as ort
    ort.disable_telemetry_events()
    name = 'UVR-MDX-NET-Inst_HQ_3.onnx'
    _, n_fft, dim_f, gain = MODELS[name]
    instrumental = separate(wave, models/name, n_fft, dim_f, ort)
    vocals = wave - instrumental * gain
    name = 'UVR_MDXNET_KARA_2.onnx'
    _, n_fft, dim_f, gain = MODELS[name]
    backing = separate(vocals, models/name, n_fft, dim_f, ort)
    lead = vocals - backing * gain
    probabilities = {}
    tracks = {}
    for name, candidate in [('mixed_source', wave), ('estimated_vocals', vocals),
                            ('estimated_lead', lead), ('estimated_backing', backing)]:
        probabilities[name] = vad(candidate, models/'silero_vad.onnx', ort)
        if name != 'mixed_source':
            path = output/(name+'.wav')
            sf.write(path, candidate.T, 44100, subtype='FLOAT')
            tracks[name] = {'sha256': digest(path), 'file': path.name}
    np.savez_compressed(output/'presence_probabilities.npz', **probabilities)
    report = dict(source_audio_sha256=EXPECTED_SHA256, networking='denied by Linux seccomp during inference',
                  telemetry='disabled before session creation', models=MODELS, vad_sha256=VAD_SHA256,
                  tracks=tracks, vad_hop_seconds=.032,
                  presence_probabilities_sha256=digest(output/'presence_probabilities.npz'),
                  independent_backing_verified=False,
                  limitation='Model-derived candidates and speech VAD probabilities are not verified singer identity or singing ground truth.')
    (output/'candidate_receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    screen_candidates(output, output)
    return report


def screen_candidates(candidates, output):
    """Bind screened clocks to exact source, candidate bytes and probability bytes."""
    from music.review_score import vocal_clock
    from music.vocal_presence import screen_clock
    from music.vocal_roles import _duplicate
    receipt = json.loads((candidates/'candidate_receipt.json').read_text())
    if receipt['source_audio_sha256'] != EXPECTED_SHA256:
        raise ValueError('Candidate source identity mismatch')
    probabilities = candidates/'presence_probabilities.npz'
    if receipt['presence_probabilities_sha256'] != digest(probabilities):
        raise ValueError('Presence probability receipt mismatch')
    arrays, tracks, waves = {}, {}, []
    with np.load(probabilities, allow_pickle=False) as evidence:
        for lane in ('estimated_lead', 'estimated_backing'):
            path = candidates/(lane+'.wav')
            if receipt['tracks'][lane]['sha256'] != digest(path):
                raise ValueError('Candidate track bytes differ from receipt')
            wave, sr = sf.read(path, dtype='float32', always_2d=True)
            if sr != 44100:
                raise ValueError('Candidate sample clock changed')
            mono = resample_poly(wave.mean(axis=1), 160, 441)
            waves.append(mono)
            clock = screen_clock(vocal_clock(mono), evidence[lane])
            arrays.update({lane+'_'+key: value for key, value in clock.items()})
            tracks[lane] = dict(file=path.name, sha256=digest(path), seconds=len(wave)/sr,
                voiced_seconds_estimate=float(np.count_nonzero(clock['energy'])/100), presence_screened=True)
    output.mkdir(parents=True, exist_ok=True)
    archive = output/'acoustic_vocal_clocks.npz'
    np.savez_compressed(archive, **arrays)
    report = dict(receipt, schema='helix.phoneme-vocal-separation-diagnostic.v2',
        audio_sha256=EXPECTED_SHA256, clock_sha256=digest(archive), clock_hop_seconds=.01,
        analysis_estimates_not_ground_truth=True, exact_phoneme_boundaries_verified=False,
        gain_or_short_delay_duplicate=_duplicate(*waves), engine_events_modified=False)
    report['tracks'] = tracks
    report['presence_screening'] = dict(model='Silero VAD', threshold=.15,
        probability_hop_seconds=.032, context_frames=2, minimum_acoustic_frames=5,
        ending_specific_rule=False, independent_backing_verified=False)
    report['limitation'] = ('Per-source MDX candidates screened by speech VAD reduce instrumental/reverb openings. '
        'Singing may be missed; individual singer identity and lexical phonemes remain unverified. '
        'No source audio or instrumental event timing changed.')
    (output/'diagnostic.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--models', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(run(a.audio, a.output, a.models), indent=2))
