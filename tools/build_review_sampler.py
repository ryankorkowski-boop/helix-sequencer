"""Build a reproducible owner-source sampler from high-energy/flux excerpts."""
import argparse
import hashlib
import json
from pathlib import Path
from math import gcd
import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
from tools.phoneme_source import digest


def activity_start(wave, sr, seconds):
    mono = wave.mean(axis=1)
    stride = max(1, sr//8000)
    mono = mono[::stride]
    rate = sr/stride
    hop = max(1, round(rate/2))
    size = len(mono)//hop
    frames = mono[:size*hop].reshape(size, hop)
    rms = np.sqrt(np.mean(frames**2, axis=1))
    spectrum = np.abs(np.fft.rfft(frames*np.hanning(hop), axis=1))
    flux = np.r_[0, np.mean(np.maximum(0, np.diff(spectrum, axis=0)), axis=1)]
    score = .7*rms/max(float(rms.max()), 1e-8)+.3*flux/max(float(flux.max()), 1e-8)
    width = round(seconds*2)
    if len(score) < width:
        raise ValueError('Source is shorter than the requested excerpt')
    windows = np.convolve(score, np.ones(width)/width, mode='valid')
    # Avoid file-edge artifacts; every other activity window remains eligible.
    margin = min(6, max(0, (len(windows)-1)//2))
    eligible = windows[margin:len(windows)-margin] if margin else windows
    return (int(np.argmax(eligible))+margin)/2


def build(config, output, seconds=16):
    if not isinstance(seconds, int) or seconds <= 0:
        raise ValueError('Positive whole-second excerpt length required')
    rows = json.loads(Path(config).read_text())
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    if not isinstance(rows,list) or not rows:
        raise ValueError('At least one source recording is required')
    pieces, clips, duplicates, seen = [], [], [], {}
    for row in rows:
        path = Path(row['local_path'])
        if digest(path) != row['sha256']:
            raise ValueError('Owner source checksum mismatch: '+row['title'])
        wave, sr = sf.read(path, dtype='float32', always_2d=True)
        if wave.shape[1] not in (1, 2) or not np.isfinite(wave).all():
            raise ValueError('Finite mono/stereo source required')
        identity=(sr,wave.shape,hashlib.sha256(np.asarray(wave,'<f4').tobytes()).hexdigest())
        if identity in seen:
            duplicates.append(dict(title=row['title'],sha256=row['sha256'],duplicate_of=seen[identity]))
            continue
        seen[identity]=row['title']
        if 'start_seconds' in row:
            start=float(row['start_seconds'])
            if not np.isfinite(start) or start<0 or start+seconds>len(wave)/sr:
                raise ValueError('Configured excerpt is outside the source recording')
            selection='Explicit source-clock interval; selection evidence retained in source configuration'
        else:
            start = activity_start(wave, sr, seconds)
            selection='Maximum activity window'
        first, count = round(start*sr), round(seconds*sr)
        cut = wave[first:first+count]
        common = gcd(sr, 44100)
        cut = resample_poly(cut, 44100//common, sr//common, axis=0)
        if cut.shape[1] == 1: cut = np.repeat(cut, 2, axis=1)
        # Short edit fades prevent hard-cut clicks; no gain normalization.
        fade = round(.02*44100)
        cut[:fade] *= np.linspace(0, 1, fade)[:, None]
        cut[-fade:] *= np.linspace(1, 0, fade)[:, None]
        clips.append(dict(**row, source_sample_rate=sr, source_start_sample=first,
            source_end_sample=first+count, source_start_seconds=start, duration_seconds=seconds,
            selection_method=selection,
            sampler_start_seconds=sum(len(p) for p in pieces)/44100, edge_fade_seconds=.02))
        pieces.append(cut)
    audio = output/'Helix_Starred_New_Review.wav'
    combined=np.concatenate(pieces)
    peak=float(np.max(np.abs(combined)))
    # MP3 decoding and resampling can overshoot full scale. Attenuate only
    # when needed; PCM16 conversion must never silently clip a source excerpt.
    gain=min(1.,.98/max(peak,1e-12))
    sf.write(audio, combined*gain, 44100, subtype='PCM_16')
    report = dict(schema='helix.owner-review-sampler.v1', audio=audio.name,
        audio_sha256=digest(audio), duration_seconds=sf.info(audio).duration,
        source_selection='Owner Starred catalog; distinct Drive IDs; SHA256 verified before decoding',
        excerpt_selection=f'Maximum {seconds}-second mean of normalized RMS (70%) and positive spectral flux (30%); half-second candidate grid',
        original_source_files_modified=False, gain_normalization=False,
        peak_before_encoding=peak,output_gain=gain,attenuation_only=True,
        duplicates_omitted=duplicates,clips=clips)
    (output/'Sampler_Provenance.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path); parser.add_argument('output', type=Path)
    parser.add_argument('--seconds-per-song', type=int, default=16)
    args = parser.parse_args()
    print(json.dumps(build(args.config, args.output, args.seconds_per_song), indent=2))
