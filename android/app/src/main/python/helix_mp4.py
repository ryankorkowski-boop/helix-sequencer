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


# ISO BMFF size=1 uses a 64-bit largesize; size=0 extends to the enclosing EOF.
# Android MediaMuxer reserves a largesize mdat even for small recordings.
import math
import os
import shutil
import tempfile

MAX_METADATA_BYTES = 64 * 1024 * 1024
UINT32_MAX = 0xffffffff


def _header(read, start, end):
    if not 0 <= start <= end or end - start < 8:
        raise ValueError('Truncated MP4 box header')
    raw = read(start, 8)
    if len(raw) != 8:
        raise ValueError('Truncated MP4 box header')
    size, kind = struct.unpack('>I4s', raw)
    header = 8
    to_eof = size == 0
    if size == 1:
        if end - start < 16:
            raise ValueError('Truncated MP4 extended size')
        raw = read(start + 8, 8)
        if len(raw) != 8:
            raise ValueError('Truncated MP4 extended size')
        size = struct.unpack('>Q', raw)[0]
        header = 16
    elif to_eof:
        size = end - start
    if kind == b'uuid':
        header += 16
    if size < header or size > end - start:
        raise ValueError('Invalid MP4 box boundary')
    return start, size, kind, header, to_eof


def _boxes(data, start=0, end=None):
    end = len(data) if end is None else end
    if not 0 <= start <= end <= len(data):
        raise ValueError('Invalid MP4 container boundary')
    while start < end:
        item = _header(lambda p, n: data[p:p+n], start, end)
        yield item
        start += item[1]


def boxes(data, start=0, end=None):
    """Compatibility iterator returning validated (position, total size, type)."""
    for p, n, kind, _header_size, _to_eof in _boxes(data, start, end):
        yield p, n, kind


def box(kind, payload):
    size = len(payload) + 8
    if size <= UINT32_MAX:
        return struct.pack('>I4s', size, kind) + payload
    return struct.pack('>I4sQ', 1, kind, size + 8) + payload


def _child(data, start, end, kind):
    matches = [item for item in _boxes(data, start, end) if item[2] == kind]
    if len(matches) != 1:
        raise ValueError('MP4 requires exactly one ' + kind.decode('ascii') + ' box')
    return matches[0]


def _time_scale(data, item):
    p, n, _kind, h, _eof = item
    payload = data[p+h:p+n]
    if len(payload) < 4 or payload[0] not in (0, 1):
        raise ValueError('Unsupported MP4 time header version')
    offset = 12 if payload[0] == 0 else 20
    duration_size = 4 if payload[0] == 0 else 8
    if len(payload) < offset + 4 + duration_size:
        raise ValueError('Truncated MP4 time header')
    scale = struct.unpack_from('>I', payload, offset)[0]
    if not scale:
        raise ValueError('MP4 time scale must be positive')
    return scale


def _duration(piece, duration, *, track=False):
    """Patch version 0/1 durations, upgrading v0 when 32 bits cannot hold it."""
    _p, n, kind, h, _eof = next(_boxes(piece))
    payload = bytearray(piece[h:n])
    if len(payload) < 4 or payload[0] not in (0, 1):
        raise ValueError('Unsupported MP4 time header version')
    version = payload[0]
    offset = (20 if version == 0 else 28) if track else (16 if version == 0 else 24)
    width = 4 if version == 0 else 8
    if len(payload) < offset + width:
        raise ValueError('Truncated MP4 duration')
    if version == 0 and duration > UINT32_MAX:
        creation, modification = struct.unpack_from('>II', payload, 4)
        # Preserve track id/reserved or movie timescale, and every trailing field.
        middle = payload[12:offset]
        payload = bytearray(b'\x01' + bytes(payload[1:4]) +
                            struct.pack('>QQ', creation, modification) + middle +
                            struct.pack('>Q', duration) + payload[offset+4:])
    else:
        struct.pack_into('>I' if version == 0 else '>Q', payload, offset, duration)
    return box(kind, bytes(payload))


def _edited_moov(original, samples, sample_rate, seconds):
    root = next(_boxes(original))
    if root[2] != b'moov' or root[1] != len(original):
        raise ValueError('Invalid MP4 movie container')
    children = list(_boxes(original, root[3]))
    scale = _time_scale(original, _child(original, root[3], len(original), b'mvhd'))
    duration = round(seconds * scale)
    if not 0 < duration <= 0xffffffffffffffff:
        raise ValueError('MP4 presentation duration is out of range')
    result, audio_tracks = [], 0
    for p, n, kind, h, _eof in children:
        piece = original[p:p+n]
        if kind == b'mvhd':
            piece = _duration(piece, duration)
        elif kind == b'trak':
            parts = list(_boxes(piece, h))
            mdia = _child(piece, h, len(piece), b'mdia')
            q, m, _k, mh, _e = mdia
            handler = _child(piece, q+mh, q+m, b'hdlr')
            t, z, _k, hh, _e = handler
            if z-hh < 12:
                raise ValueError('Truncated MP4 handler')
            if piece[t+hh+8:t+hh+12] == b'soun':
                audio_tracks += 1
                media_scale = _time_scale(piece, _child(piece, q+mh, q+m, b'mdhd'))
                offset = round(samples * media_scale / sample_rate)
                if offset > 0x7fffffffffffffff:
                    raise ValueError('MP4 audio edit offset is out of range')
                version = int(duration > UINT32_MAX or offset > 0x7fffffff)
                payload = struct.pack('>II', version << 24, 1)
                payload += struct.pack('>Qqhh' if version else '>Iihh', duration, offset, 1, 0)
                edit = box(b'edts', box(b'elst', payload))
                # tkhd is mandatory; retaining the original mdhd preserves media samples.
                _child(piece, h, len(piece), b'tkhd')
                pieces = []
                for t, z, k, _ch, _ce in parts:
                    if k != b'edts':
                        child = piece[t:t+z]
                        # A terminal size=0 child must become finite before an
                        # edit sibling is appended, or it would swallow edts.
                        if _ce:
                            child = struct.pack('>I', z) + child[4:]
                        pieces.append(_duration(child, duration, track=True) if k == b'tkhd' else child)
                piece = box(b'trak', b''.join(pieces) + edit)
        result.append(piece)
    if audio_tracks != 1:
        raise ValueError('MP4 requires exactly one audio track for measured synchronization')
    return box(b'moov', b''.join(result))


def add_audio_edit(movie, samples, sample_rate, seconds):
    """Atomically append an edit without moving media or changing chunk offsets.

    Metadata RAM is bounded. Validate the whole file before writing; normalize any
    terminal size=0 box so it cannot swallow the appended moov. An EOF media box
    larger than 4 GiB needs relocation and is safely rejected by this mobile editor.
    Explicit 64-bit media boxes of any size remain supported.
    """
    if (not isinstance(samples, int) or samples < 0 or sample_rate <= 0 or
            not math.isfinite(seconds) or seconds <= 0):
        raise ValueError('Invalid MP4 synchronization parameters')
    path = Path(movie)
    with path.open('rb') as source:
        length = source.seek(0, 2)
        def read(p, n):
            source.seek(p)
            return source.read(n)
        cursor, metadata, eof_boxes = 0, [], []
        while cursor < length:
            item = _header(read, cursor, length)
            p, n, kind, h, to_eof = item
            if kind == b'moof':
                raise ValueError('Fragmented MP4 is not supported by this presentation editor')
            if kind == b'moov':
                metadata.append(item)
            if to_eof:
                if n > UINT32_MAX:
                    raise ValueError('EOF MP4 box exceeds 32 bits; relocation is required')
                eof_boxes.append((p, n))
            cursor += n
        if len(metadata) != 1:
            raise ValueError('MP4 requires exactly one movie metadata box')
        position, size, _kind, _h, _eof = metadata[0]
        if size > MAX_METADATA_BYTES:
            raise ValueError('MP4 metadata exceeds mobile memory limit')
        original = read(position, size)
        revised = _edited_moov(original, samples, sample_rate, seconds)
        # Never expose a partially patched MP4, even after write failure.
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.mp4-edit-', delete=False) as target:
                temp_name = target.name
                source.seek(0)
                shutil.copyfileobj(source, target, length=1024*1024)
                for p, n in eof_boxes:
                    target.seek(p)
                    target.write(struct.pack('>I', n))
                target.seek(position+4)
                target.write(b'free')
                target.seek(0, 2)
                target.write(revised)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temp_name, path)
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)


def synchronize(movie, source, decoded, seconds):
    delay, rate, confidence = measure_delay(source, decoded, seconds)
    add_audio_edit(movie, delay, rate, seconds)
    return {'encoder_delay_samples': delay, 'sample_rate': rate,
            'alignment_correlation': confidence}

