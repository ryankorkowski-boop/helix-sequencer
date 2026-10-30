"""Bound spectral workspace without changing sample clocks or DSP parameters."""
from __future__ import annotations

from core.lazy_imports import LazyModule

librosa = LazyModule("librosa")
np = LazyModule("numpy")


def hpss(y, sr):
    """Default librosa HPSS with aligned context and original-length outputs.

    The default 31-frame median has finite support. The context also covers
    analysis/synthesis windows; only interior samples are copied, once. Short
    inputs keep the original single call. No resampling, crossfade or padding
    is introduced at chunk boundaries.
    """
    if len(y) <= 30 * sr:
        return librosa.effects.hpss(y)
    hop, context = 512, 64 * 512
    core = max(hop, int(sr * 8) // hop * hop)
    harmonic, percussive = np.empty_like(y), np.empty_like(y)
    for start in range(0, len(y), core):
        stop = min(start + core, len(y))
        left, right = max(0, start - context), min(len(y), stop + context)
        harm, perc = librosa.effects.hpss(y[left:right])
        harmonic[start:stop] = harm[start-left:stop-left]
        percussive[start:stop] = perc[start-left:stop-left]
        del harm, perc
    return harmonic, percussive


def magnitude_blocks(y, *, hop=512, n_fft=2048, block_frames=512):
    """Yield default centered-STFT magnitudes on the unchanged full-file grid."""
    frame_count = 1 + len(y) // hop
    for start in range(0, frame_count, block_frames):
        stop = min(start + block_frames, frame_count)
        left = max(0, start * hop - n_fft)
        right = min(len(y), stop * hop + n_fft)
        spectrum = librosa.stft(y[left:right], n_fft=n_fft, hop_length=hop)
        offset = (start * hop - left) // hop
        yield start, np.abs(spectrum[:, offset:offset+stop-start])
