"""Final band driver sharing absolute note cues with the native helix export."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from tools.readable_band_performance import ReadablePerformance
from tools.musical_band_performance import MusicalBandPerformance
from music.magic_keyboard import magic_keyboard_events
from music.unified_mallet import unified_mallet_schedule, bar_pitch


class FinalBandPerformance(MusicalBandPerformance):
    def __init__(self, row, scene, analysis_root, casting=None):
        super().__init__(row, scene, analysis_root, casting)
        eligible = [e for lane, values in self.events.items()
                    if lane not in ("bass", "guitar", "drums", "vocals") for e in values]
        self.keyboard_events = magic_keyboard_events(eligible, self.mallet_schedule, duration=self.n/20)
        reachable = {}
        for rig in scene.rigs:
            if rig['role'] == 'xylophone':
                reachable[rig['side']] = {p for p,center in scene.bars.items()
                    if np.linalg.norm(center+(0,.0275+.057+.2598076211,-.15)-rig['shoulder']) < sum(rig['link_lengths'])-1e-7}
        self.mallet_schedule, self.mallet_motion_omissions = unified_mallet_schedule(
            self.keyboard_events, duration=self.n/20, low=min(scene.bars), high=max(scene.bars), reachable=reachable)
        self.mallet_proof.update(accepted=len(self.mallet_schedule), unified_pitched_sources=True,
            octave_folding="pitch-class-preserving nearest playable octave; absolute MIDI retained for helix",
            motion_omissions=len(self.mallet_motion_omissions))
        self._bar_levels = np.zeros((self.n, len(scene.bars)), dtype=np.float32)
        for e in self.keyboard_events:
            p = bar_pitch(e.pitch, min(scene.bars), max(scene.bars))
            start = max(0, round(e.start*20)); end = min(self.n, max(start+1, round(e.end*20)))
            self._bar_levels[start:end, p-min(scene.bars)] = np.maximum(
                self._bar_levels[start:end, p-min(scene.bars)], e.velocity)
        # Precompute the same short mallet decay once. Scanning every source
        # event for every rendered frame previously dominated dense passages.
        for hit in self.mallet_schedule:
            start=max(0,round(hit['time']*20))
            for i in range(start,min(self.n,start+7)):
                age=i/20-hit['time']
                if 0<=age<.30:
                    p=hit['pitch']-min(scene.bars)
                    self._bar_levels[i,p]=max(self._bar_levels[i,p],hit['velocity']*np.exp(-age/.105))
        # True separate source lanes are optional, explicitly source-bound and
        # never inferred from duplicated lyrics, pitch/gender or refrains.
        path = Path(analysis_root)/row["id"]/"independent_voices.npz"
        self.independent_voices_verified = False
        if path.exists():
            proof = json.loads(path.with_suffix(".json").read_text())
            with np.load(path) as data:
                mouths, energy = data["mouth_lanes"], data["voice_energy"]
            if proof.get("source_sha256") != row["sha256"] or not proof.get("independent_sources"):
                raise ValueError("Independent voice evidence is not bound to this source")
            if mouths.shape != (self.n, 2) or energy.shape != mouths.shape:
                raise ValueError("Independent voice lanes are unaligned")
            if not np.isfinite(energy).all() or np.any((energy<0)|(energy>1)) or np.any((mouths<0)|(mouths>6)):
                raise ValueError("Invalid independent voice data")
            self.voice_lanes = mouths.astype(np.int8); self.voice_energy = energy.copy()
            self.independent_voices_verified = bool(proof.get("listening_verified"))

    def levels(self, i):
        levels = np.pad(ReadablePerformance.levels(self,i),(0,64))
        # Held notes and release remain tied to musical events. The hidden
        # keyboard has no separately visible performer.
        levels[128:128+len(self.scene.bars)] = self._bar_levels[i]
        return levels
