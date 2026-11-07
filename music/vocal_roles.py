"""Evidence-based voice casting; a mixed vocal bus never proves two singers.

Individual/ensemble track labels describe input provenance, not an inference
from pitch or gender. Automatic roles use prominence and phrase participation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import numpy as np
from music.review_score import vocal_clock
from models.band_sampler_logic import SHAPE_NAMES


@dataclass
class VoiceTrack:
    name: str
    audio: np.ndarray
    sample_rate: int
    evidence: str = 'mixed'  # mixed, individual, ensemble
    role: str | None = None  # lead, second, background; only for isolated inputs
    phonemes: tuple[dict, ...] = ()  # verified local-time cues, not guessed text


def _clock(track):
    import librosa
    y = np.asarray(track.audio, dtype=np.float32)
    if y.ndim == 2:
        y = y.mean(axis=1)
    if y.ndim != 1 or len(y)==0 or not np.isfinite(y).all() or track.sample_rate <= 0:
        raise ValueError('Voice audio must be finite mono or frames/channels')
    y = librosa.resample(y, orig_sr=track.sample_rate, target_sr=16000)
    c = vocal_clock(y)
    # Tiny isolated periodic blips are common instrumental bleed. Do not add
    # release padding: both edges stay on the measured source clock.
    active = c['energy'] > 0
    edges = np.flatnonzero(np.diff(np.r_[False, active, False]))
    for a, b in zip(edges[::2], edges[1::2]):
        if b-a < 5:
            c['energy'][a:b] = 0
            c['shapes'][a:b] = 0
    return y, c


def _duplicate(a, b):
    """Reject gain copies and very short delayed copies, including antiphase."""
    n = min(len(a), len(b))
    if not n or max(np.linalg.norm(a[:n]), np.linalg.norm(b[:n])) < 1e-8:
        return False
    a, b = a[:n:8], b[:n:8]
    for lag in range(-60, 61, 3):
        x, y = (a[lag:], b[:len(b)-lag]) if lag >= 0 else (a[:len(a)+lag], b[-lag:])
        denominator = np.linalg.norm(x)*np.linalg.norm(y)
        if denominator > 1e-8 and abs(float(x@y)/denominator) > .965:
            return True
    return False


def route_voices(tracks: list[VoiceTrack], *, duration: float, fps: int = 20):
    if duration <= 0 or fps <= 0:
        raise ValueError('Positive duration and fps required')
    frames = round(duration*fps)
    clocks, waves, metadata, accepted = {}, {}, {}, []
    for track in tracks:
        if track.name in metadata:
            raise ValueError('Voice track names must be unique')
        if track.evidence not in ('mixed', 'individual', 'ensemble'):
            raise ValueError('Unknown voice evidence')
        if track.role not in (None, 'lead', 'second', 'background'):
            raise ValueError('Unknown voice role')
        if track.evidence == 'mixed' and track.role in ('second', 'background'):
            raise ValueError('Mixed bus cannot establish an independent singer')
        wave, c = _clock(track)
        raw_indices = np.floor(np.arange(frames)*100/fps).astype(int)
        indices = np.minimum(raw_indices, len(c['energy'])-1)
        energy, shape = c['energy'][indices].copy(), c['shapes'][indices].copy()
        energy[raw_indices>=len(c['energy'])]=0;shape[raw_indices>=len(c['energy'])]=0
        duplicate = next((name for name in accepted if _duplicate(wave, waves[name])), None)
        metadata[track.name] = dict(evidence=track.evidence, requested_role=track.role,
            sha256=hashlib.sha256(np.asarray(track.audio, '<f4').tobytes()).hexdigest(),
            duplicate_of=duplicate, voiced_fraction=float(np.mean(energy > 0)),
            prominence=float(np.sqrt(np.mean(wave**2))))
        if duplicate:
            continue
        for cue in track.phonemes:
            if not cue.get('verified'):
                raise ValueError('Explicit phoneme cues require verified=True')
            name = cue['shape'].upper()
            if name not in SHAPE_NAMES or not 0 <= cue['start'] < cue['end'] <= duration:
                raise ValueError('Invalid phoneme cue')
            mask = (np.arange(frames)/fps >= cue['start']) & (np.arange(frames)/fps < cue['end'])
            # Verified consonants may be unvoiced: they own their cue interval.
            shape[mask] = SHAPE_NAMES.index(name)
            energy[mask] = np.maximum(energy[mask], .45 if name != 'REST' else 0)
            if name == 'REST': energy[mask] = 0
        clocks[track.name] = (energy, shape)
        waves[track.name] = wave
        accepted.append(track.name)
    isolated = [t for t in tracks if t.name in accepted and t.evidence != 'mixed']
    pool = isolated or [t for t in tracks if t.name in accepted]
    explicit = [t for t in pool if t.role == 'lead']
    if len(explicit) > 1:
        raise ValueError('Only one lead voice allowed; mark the co-lead second')
    candidates=[t for t in pool if t.evidence!='ensemble' and t.role not in ('background','second')]
    lead = (explicit or sorted(candidates, key=lambda t: metadata[t.name]['prominence']*
        metadata[t.name]['voiced_fraction'], reverse=True))[:1]
    roles = {}
    if lead:
        roles[lead[0].name] = 'lead'
        lead_meta = metadata[lead[0].name]
    explicit_second=[t for t in isolated if t.role=='second']
    if len(explicit_second)>1:
        raise ValueError('A duet has one second singer; assign further tracks background roles')
    coequals=[t for t in isolated if t.name not in roles and t.role is None and t.evidence=='individual'
        and lead and metadata[t.name]['voiced_fraction']>=lead_meta['voiced_fraction']*.60
        and metadata[t.name]['prominence']>=lead_meta['prominence']*.55]
    second=(explicit_second or sorted(coequals,key=lambda t:metadata[t.name]['prominence']*
        metadata[t.name]['voiced_fraction'],reverse=True))[:1]
    for track in isolated:
        if track.name in roles: continue
        m = metadata[track.name]
        roles[track.name] = track.role or ('background' if track.evidence == 'ensemble'
                                         else 'second' if second and track.name==second[0].name else 'background')
    lanes = []
    for name, role in roles.items():
        energy, shape = clocks[name]
        lanes.append(dict(name=name, role=role, energy=energy, shapes=shape))
        metadata[name]['resolved_role'] = role
    # Per-frame classification uses independent active tracks, not track count.
    modes = np.full(frames, 'silence', dtype='<U18')
    for i in range(frames):
        active = [lane['role'] for lane in lanes if lane['energy'][i] > 0]
        if active:
            modes[i] = ('duet_background' if all(r in active for r in ('lead','second','background')) else
                        'lead_background' if 'background' in active and 'lead' in active else
                        'duet' if 'second' in active and 'lead' in active else
                        'background' if all(r=='background' for r in active) else 'solo')
    report = dict(schema='helix.voice_roles.v1', input_tracks=metadata,
        voice_identity_resolved=bool(isolated), mixed_bus_only=not bool(isolated),
        independent_tracks=len(isolated), classifications={k:int(np.sum(modes==k)) for k in np.unique(modes)},
        timing_hop_seconds=.01, release_padding_seconds=0,
        phoneme_method='verified cues where supplied; broad AH/EE/OH acoustic estimates elsewhere',
        limitation='Mixed bus singing is supported; singer count, duet identity and backing parts remain unresolved without independent sources.')
    return lanes, modes, report
