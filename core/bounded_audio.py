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


def dominant_pitch(power, *, sr, hop, fmin, fmax, block_frames=512):
    """Reduce piptrack's frame-local result before allocating the next block."""
    selected = np.full(power.shape[1], np.nan, dtype=float)
    for start in range(0, power.shape[1], block_frames):
        stop = min(start + block_frames, power.shape[1])
        pitches, weights = librosa.piptrack(S=np.sqrt(power[:, start:stop]), sr=sr,
                                          hop_length=hop, fmin=fmin, fmax=fmax)
        values = pitches[np.argmax(weights, axis=0), np.arange(stop-start)]
        selected[start:stop] = np.where(values > 0, values, np.nan)
        del pitches, weights, values
    return selected


def spectral_descriptors(spectrum, *, sr, power=False, block_frames=512, include_contrast=True):
    """Bound frequency workspaces; retain contrast's whole-file dB floor."""
    centroid, bandwidth, flatness = (np.empty(spectrum.shape[1]) for _ in range(3))
    if include_contrast:
        # Pinned librosa 0.10.2 default spectral_contrast band/quantile kernel.
        # Its final power_to_db clips against a GLOBAL maximum. Calling the
        # complete API once per block changes quiet/rest frames. Retain only
        # seven peak/valley curves, then apply the unchanged global dB transform.
        from librosa.util.exceptions import ParameterError
        edges = np.r_[0.0, 200.0 * 2.0 ** np.arange(7)]
        if np.any(edges[:-1] >= .5 * sr):
            raise ParameterError("Frequency band exceeds Nyquist. Reduce either fmin or n_bands.")
        frequencies = librosa.fft_frequencies(sr=sr, n_fft=2*(spectrum.shape[0]-1))
        bands = []
        for k, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
            mask = (frequencies >= low) & (frequencies <= high)
            indices = np.flatnonzero(mask)
            if k > 0:
                mask[indices[0]-1] = True
            if k == 6:
                mask[indices[-1]+1:] = True
            count = int(np.maximum(np.rint(.02*np.sum(mask)), 1))
            bands.append((mask, count))
        peaks = np.zeros((7, spectrum.shape[1]))
        valleys = np.zeros_like(peaks)
    for start in range(0, spectrum.shape[1], block_frames):
        stop = min(start + block_frames, spectrum.shape[1])
        magnitude = spectrum[:, start:stop]
        if power:
            magnitude = np.sqrt(np.maximum(0.0, np.asarray(magnitude, dtype=float)))
        centroid[start:stop] = librosa.feature.spectral_centroid(S=magnitude, sr=sr)[0]
        bandwidth[start:stop] = librosa.feature.spectral_bandwidth(S=magnitude, sr=sr)[0]
        if include_contrast:
            for k, (mask, count) in enumerate(bands):
                band = magnitude[mask, :]
                if k < 6:
                    band = band[:-1, :]
                ordered = np.sort(band, axis=0)
                valleys[k, start:stop] = np.mean(ordered[:count, :], axis=0)
                peaks[k, start:stop] = np.mean(ordered[-count:, :], axis=0)
                del band, ordered
        flatness[start:stop] = librosa.feature.spectral_flatness(S=magnitude)[0]
        del magnitude
    contrast = (librosa.power_to_db(peaks) - librosa.power_to_db(valleys)
                if include_contrast else np.empty((0, spectrum.shape[1])))
    return centroid, bandwidth, contrast, flatness


def positive_flux(power, *, block_frames=512):
    """Keep the preceding frame at each boundary; no new onset or time shift."""
    flux = np.zeros(power.shape[1], dtype=float)
    for start in range(1, power.shape[1], block_frames):
        stop = min(start + block_frames, power.shape[1])
        difference = np.diff(np.asarray(power[:, start-1:stop], dtype=float), axis=1)
        flux[start:stop] = np.sum(np.clip(difference, 0.0, None), axis=0)
    return flux


def mel_spectrogram(y, *, sr, n_fft, hop_length, n_mels, fmin, fmax):
    """Retain the small mel grid while bounding the larger FFT intermediates."""
    blocks = []
    for _, magnitude in magnitude_blocks(y, hop=hop_length, n_fft=n_fft):
        blocks.append(librosa.feature.melspectrogram(S=magnitude**2, sr=sr,
                      n_fft=n_fft, hop_length=hop_length, n_mels=n_mels,
                      fmin=fmin, fmax=fmax, power=2.0))
    return np.concatenate(blocks, axis=1)


def pitch_matrices(magnitude, *, sr, hop_length, fmin, fmax):
    """Preserve required dense pitch outputs with bounded piptrack workspace."""
    pitches, weights = np.empty_like(magnitude), np.empty_like(magnitude)
    for start in range(0, magnitude.shape[1], 512):
        stop = min(start+512, magnitude.shape[1])
        p, w = librosa.piptrack(S=magnitude[:, start:stop], sr=sr,
                               hop_length=hop_length, fmin=fmin, fmax=fmax)
        pitches[:, start:stop], weights[:, start:stop] = p, w
        del p, w
    return pitches, weights


def estimate_tuning(y, *, sr, bins_per_octave):
    """Original whole-song tuning histogram from bounded default pitch frames."""
    pitches, weights = [], []
    for _, magnitude in magnitude_blocks(y):
        p, w = librosa.piptrack(S=magnitude, sr=sr)
        mask = p > 0
        pitches.append(p[mask])
        weights.append(w[mask])
        del p, w, magnitude
    p, w = np.concatenate(pitches), np.concatenate(weights)
    threshold = np.median(w) if w.size else 0.0
    return librosa.pitch_tuning(p[w >= threshold], bins_per_octave=bins_per_octave)
