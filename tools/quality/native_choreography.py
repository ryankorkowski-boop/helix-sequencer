"""Measure rendered FSEQ choreography, not preview brightness or intended cues.

For authored Helix layouts, use the channel spans and model centers from the
exported manifest. RGB statistics exclude AC and non-light control models.
Model-centroid travel is a proxy for inter-prop motion, not proof of musical
accuracy or native per-pixel geometry. No controller safety claim is made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np


class ChoreographyObserver:
    def __init__(self, models):
        self.models = sorted((m for m in models if m.get('kind') in ('pixel', 'ac')),
                             key=lambda m: int(m['start_channel']))
        if not self.models:
            raise ValueError('No mapped lighting models')
        self.previous = None
        self.previous_center = None
        self.samples = 0
        self.changes = 0
        self.broadcast = 0
        self.white_frames = 0
        self.peak_white = 0.0
        self.travel = np.zeros(3)
        self.model_activity = np.zeros(len(self.models), dtype=int)
        self.model_changed = np.zeros(len(self.models), dtype=int)
        self.mean_changes = 0.0
        self.ac_sync = 0
        self.rgb_sync = 0

    def begin(self, destinations, channels, frames, step):
        addresses, lengths, rgb_offsets, centers, kinds = [], [], [], [], []
        last = 0
        cursor = 0
        for model in self.models:
            a, b = int(model['start_channel']), int(model['end_channel'])
            if a <= last or b < a or b > channels:
                raise ValueError('Lighting model channels overlap or exceed FSEQ')
            last = b
            width = b - a + 1
            rgb = model['kind'] == 'pixel'
            if rgb and (width % 3 or width != 3 * int(model['nodes'])):
                raise ValueError('RGB channel span does not match model node count')
            if rgb:
                rgb_offsets.extend(range(cursor, cursor + width))
            addresses.extend(range(a-1, b))
            cursor += width
            lengths.append(width)
            kinds.append(rgb)
            center = np.asarray(model['bounds_ft'], dtype=float).mean(axis=0)
            if center.shape != (3,) or not np.isfinite(center).all():
                raise ValueError('Invalid authored model bounds')
            centers.append(center)
        ids = np.asarray(addresses, dtype=int)
        pos = np.searchsorted(destinations, ids)
        safe = np.minimum(pos, len(destinations)-1)
        self.missing_channels = int(np.count_nonzero((pos >= len(destinations)) | (destinations[safe] != ids)))
        # Sparse omissions are actual zero-valued channels, not invented data.
        self.positions = np.where((pos < len(destinations)) & (destinations[safe] == ids),
                                  pos, len(destinations))
        self.rgb_offsets = np.asarray(rgb_offsets, dtype=int)
        self.lengths = np.asarray(lengths)
        self.starts = np.r_[0, np.cumsum(self.lengths)[:-1]]
        self.rgb_models = np.asarray(kinds, dtype=bool)
        self.centers = np.asarray(centers)
        self.extent = np.ptp(self.centers, axis=0)
        self.step = step
        self.expected_frames = frames

    def frame(self, decoded):
        values = np.r_[decoded, np.uint8(0)][self.positions]
        means = np.add.reduceat(values.astype(np.float32), self.starts) / self.lengths
        self.model_activity += means >= 8
        if self.rgb_offsets.size:
            pixels = values[self.rgb_offsets].reshape(-1, 3)
            high, low = pixels.max(axis=1), pixels.min(axis=1)
            white = float(np.mean((low >= 192) & ((high-low) <= 24)))
            self.peak_white = max(self.peak_white, white)
            self.white_frames += white >= .5
        if self.previous is not None:
            delta = means - self.previous
            changed = np.abs(delta) >= 24
            self.model_changed += changed
            self.mean_changes += float(changed.mean())
            self.changes += 1
            # Same-direction substantial changes across most props, not just
            # simultaneous note activity. Measure AC separately from RGB.
            def sync(mask):
                part = delta[mask]
                return len(part) >= 4 and max(np.mean(part >= 24), np.mean(part <= -24)) >= .75
            self.broadcast += sync(np.ones(len(delta), dtype=bool))
            self.ac_sync += sync(~self.rgb_models)
            self.rgb_sync += sync(self.rgb_models)
        weight = np.maximum(means - 8, 0)
        if weight.sum() > 0:
            center = (weight @ self.centers) / weight.sum()
            if self.previous_center is not None:
                self.travel += np.abs(center - self.previous_center)
            self.previous_center = center
        else:
            self.previous_center = None
        self.previous = means
        self.samples += 1

    def result(self):
        if self.samples != self.expected_frames:
            raise ValueError('Incomplete native choreography observation')
        n = max(1, self.changes)
        normalized = np.divide(self.travel, self.extent, out=np.zeros(3), where=self.extent > 0)
        warnings = []
        if self.white_frames / self.samples >= .10:
            warnings.append('sustained_broad_rgb_white')
        if self.broadcast / n >= .10:
            warnings.append('frequent_same_direction_whole_layout_changes')
        if self.ac_sync / n >= .10:
            warnings.append('frequent_ac_bank_synchrony')
        if self.rgb_sync / n >= .10:
            warnings.append('frequent_rgb_model_synchrony')
        if not self.model_changed.any():
            warnings.append('no_substantial_model_level_changes')
        return dict(schema='helix.native_choreography.v1', basis='decoded_native_fseq_and_authored_model_spans',
                    frames=self.samples, frame_ms=self.step, mapped_models=len(self.models),
                    mapped_ac_models=int((~self.rgb_models).sum()), mapped_rgb_models=int(self.rgb_models.sum()),
                    sparse_omitted_channels=self.missing_channels,
                    peak_white_rgb_pixel_fraction=round(self.peak_white, 6) if self.rgb_offsets.size else None,
                    broad_white_frame_fraction=round(self.white_frames / self.samples, 6) if self.rgb_offsets.size else None,
                    same_direction_model_transition_fraction=round(self.broadcast / n, 6),
                    ac_synchronized_transition_fraction=round(self.ac_sync / n, 6),
                    rgb_synchronized_transition_fraction=round(self.rgb_sync / n, 6),
                    mean_changed_model_fraction=round(self.mean_changes / n, 6),
                    normalized_centroid_travel_xyz=normalized.round(6).tolist(),
                    models_ever_active=int(np.count_nonzero(self.model_activity)),
                    models_with_substantial_changes=int(np.count_nonzero(self.model_changed)),
                    warnings=warnings, owner_approved=False,
                    limitation='Model-center motion proxy; thresholds are review heuristics, not musical, vocal, or controller safety acceptance.')


def inspect_choreography(fseq, manifest):
    from tools.quality.native import read_frames
    from tools.quality.native_stream import inspect_stream
    fseq, manifest = Path(fseq), Path(manifest)
    models = json.loads(manifest.read_text())['models']
    observer = ChoreographyObserver(models)
    with fseq.open('rb') as stream:
        header = stream.read(32)
    if len(header) >= 32 and header[:4] == b'PSEQ' and header[7] == 2 and header[20] & 15 in (0, 1):
        native = inspect_stream(fseq, observer=observer)
        sha = native['sha256']
    else:
        import hashlib
        data, channels, frames, step = read_frames(fseq)
        observer.begin(np.arange(channels), channels, frames, step)
        for frame in np.frombuffer(data, dtype=np.uint8).reshape(frames, channels):
            observer.frame(frame)
        with fseq.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    result = observer.result()
    result['fseq_sha256'] = sha
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fseq', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = inspect_choreography(args.fseq, args.manifest)
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
