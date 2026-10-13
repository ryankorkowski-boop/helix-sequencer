"""Measure native AAC priming and express it as an ISO MP4 presentation edit."""
from pathlib import Path
import struct
import numpy as np
import soundfile as sf
from scipy.signal import correlate


def measure_delay(source, decoded, seconds):
    with sf.SoundFile(source) as src, sf.SoundFile(decoded) as dst:
        if src.samplerate != dst.samplerate:
            raise ValueError('AAC decoder changed sample rate')
        rate = src.samplerate
        limit = min(len(src), int(seconds * rate))
        # Select an energetic window, bounded to six seconds of RAM even for long previews.
        for start in range(0, limit, rate * 4):
            src.seek(start)
            reference = src.read(min(rate * 4, limit-start), dtype='float32', always_2d=True).mean(axis=1)
            if len(reference) < 128 or np.max(np.abs(reference)) < .0001:
                continue
            dst.seek(start)
            actual = dst.read(len(reference)+rate//2, dtype='float32', always_2d=True).mean(axis=1)
            if len(actual) < len(reference):
                raise ValueError('AAC output is shorter than source presentation')
            scores = correlate(actual, reference, mode='valid', method='fft')
            delay = int(np.argmax(scores))
            matched = actual[delay:delay+len(reference)]
            confidence = float(np.corrcoef(reference, matched)[0, 1])
            if not np.isfinite(confidence) or confidence < .85:
                raise ValueError('Cannot verify native AAC timing (correlation %.3f)' % confidence)
            return delay, rate, confidence
    return 0, rate, 1.0  # Silence has no audible synchronization offset.


def boxes(data, start=0, end=None):
    end = len(data) if end is None else end
    while start < end:
        size, kind = struct.unpack_from('>I4s', data, start)
        if size < 8 or start+size > end:
            raise ValueError('Unsupported or corrupt MP4 box')
        yield start, size, kind
        start += size


def box(kind, payload):
    return struct.pack('>I4s', len(payload)+8, kind)+payload


def add_audio_edit(movie, samples, sample_rate, seconds):
    """Append a revised moov without moving media or invalidating chunk offsets."""
    path = Path(movie)
    with path.open('r+b') as f:
        length = f.seek(0, 2); cursor = 0; original = None
        while cursor < length:
            f.seek(cursor); size, kind = struct.unpack('>I4s', f.read(8))
            if size < 8: raise ValueError('Unsupported MP4 top-level size')
            if kind == b'moov':
                f.seek(cursor); original = f.read(size); position = cursor; break
            cursor += size
        if original is None: raise ValueError('MP4 lacks movie metadata')
        mvhd = next((p,n) for p,n,k in boxes(original,8) if k == b'mvhd')
        p,n = mvhd
        if original[p+8] != 0: raise ValueError('Unsupported movie time header')
        scale = struct.unpack_from('>I',original,p+20)[0]
        duration = round(seconds*scale)
        children=[];edited=False
        for p,n,kind in boxes(original,8):
            data=bytearray(original[p:p+n])
            if kind == b'mvhd': struct.pack_into('>I',data,24,duration)
            if kind == b'trak':
                parts=list(boxes(data,8))
                mdia=next((q,m) for q,m,k in parts if k == b'mdia')
                q,m=mdia; sub=list(boxes(data,q+8,q+m))
                handler=next(t for t,z,k in sub if k == b'hdlr')
                if data[handler+16:handler+20] == b'soun':
                    mdhd=next(t for t,z,k in sub if k == b'mdhd')
                    if data[mdhd+8] != 0: raise ValueError('Unsupported audio time header')
                    media_scale=struct.unpack_from('>I',data,mdhd+20)[0]
                    offset=round(samples*media_scale/sample_rate)
                    edit=box(b'edts',box(b'elst',struct.pack('>II Ii hh',0,1,duration,offset,1,0)))
                    pieces=[]
                    for t,z,k in parts:
                        if k == b'edts': continue
                        piece=bytearray(data[t:t+z])
                        if k == b'tkhd':
                            if piece[8] != 0: raise ValueError('Unsupported track time header')
                            struct.pack_into('>I',piece,28,duration)
                        pieces.append(bytes(piece))
                    data=box(b'trak',b''.join(pieces)+edit);edited=True
            children.append(bytes(data))
        if not edited: raise ValueError('MP4 lacks audio track')
        # Original moov becomes same-size free space; media offsets stay exact.
        f.seek(position+4);f.write(b'free');f.seek(0,2);f.write(box(b'moov',b''.join(children)))


def synchronize(movie, source, decoded, seconds):
    delay, rate, confidence=measure_delay(source,decoded,seconds)
    add_audio_edit(movie,delay,rate,seconds)
    return {'encoder_delay_samples':delay,'sample_rate':rate,'alignment_correlation':confidence}
