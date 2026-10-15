"""Compile observed drum/vocal cues for the explicit ten-drum/six-mouth kit.

This opt-in contract is separate from the historical twelve-string drummer.
It consumes classified cues; it does not infer instruments or backing voices.
"""
from __future__ import annotations

import math
import numpy as np

from core.ac_cymbal_shimmer import cymbal_shimmer
from core.ctb16pc_drummer_chorus import active_mouth_circuit
from core.physical_band_circuits import DRUMMER


def compile_ctb16pc_sequence(hits, *, duration, vocals=(), contact_hold=.035, dim=.18):
    """Return 100 Hz intensity values, with one exclusive backing-mouth pose.

    Cymbal hits may include ``tail_amplitudes`` and ``tail_fps`` measured from
    the accepted cymbal source. Without these, only a contact flash is emitted.
    No decay or vocal evidence is invented from the mixed recording.
    """
    if (not math.isfinite(duration) or duration < .01
            or not math.isfinite(contact_hold) or not .01 <= contact_hold <= .1
            or not math.isfinite(dim) or not 0 < dim < 1):
        raise ValueError("Invalid duration, contact hold, or dim intensity")
    frames = math.ceil(duration * 100)
    levels = np.zeros((frames, 16), dtype=np.uint8)
    levels[:, 0] = round(dim * 100)
    names = {c.name: i for i, c in enumerate(DRUMMER)}
    routes = {"kick": "KICK", "hi_hat": "HI_HAT", "hihat": "HI_HAT",
              "tom_high": "TOM_HIGH", "tom_mid": "TOM_MID",
              "tom_floor": "TOM_FLOOR", "tom_low": "TOM_FLOOR",
              "cymbal_left": "CYMBAL_LEFT", "cymbal_right": "CYMBAL_RIGHT"}

    def span(start, end):
        if not all(math.isfinite(t) for t in (start, end)) or not 0 <= start < end <= duration:
            raise ValueError("Cue interval must be finite and inside the sequence")
        a = min(frames - 1, round(start * 100))
        return a, min(frames, max(a + 1, round(end * 100)))

    routed = []
    for hit in hits:
        time, velocity = float(hit["time"]), float(hit.get("velocity", 1))
        if not math.isfinite(time) or not 0 <= time < duration:
            raise ValueError("Drum onset must be inside the sequence")
        if not math.isfinite(velocity) or not 0 < velocity <= 1:
            raise ValueError("Drum velocity must be finite and in (0, 1]")
        target = hit["target"].lower().removeprefix("hx_snowman_drummer_v3_hit_")
        if target == "snare":
            if hit.get("side") not in ("left", "right"):
                raise ValueError("Snare requires an explicit source hand")
            name = "SNARE_" + hit["side"].upper()
        elif target in routes:
            name = routes[target]
        else:
            raise ValueError(f"Unmapped physical drum target: {target}")
        a, b = span(time, min(duration, time + contact_hold))
        routed.append((a, b, names[name], velocity, hit, time, target))
    routed.sort(key=lambda row: row[0])
    for i, (a, b, channel, velocity, hit, time, target) in enumerate(routed):
        if "tail_amplitudes" in hit:
            if not target.startswith("cymbal_"):
                raise ValueError("Measured cymbal tails require a cymbal target")
            fps = float(hit.get("tail_fps", 40))
            envelope = cymbal_shimmer(hit["tail_amplitudes"], fps=fps)
            stop = min(frames, round((time + len(envelope) / fps) * 100))
            for tick in range(a, stop):
                sample = min(len(envelope) - 1, max(0, math.floor((tick / 100 - time) * fps + 1e-9)))
                levels[tick, channel] = max(levels[tick, channel], round(envelope[sample] * velocity))
        else:
            # Preserve a dark tick before a repeated contact, including rapid
            # kicks. Refuse onsets beyond the LMS centisecond resolution.
            next_start = next((r[0] for r in routed[i + 1:] if r[2] == channel), None)
            if next_start is not None:
                if next_start - a < 2:
                    raise ValueError("Repeated contacts need at least 20 ms for distinct LMS flashes")
                b = min(b, next_start - 1)
            levels[a:b, channel] = np.maximum(levels[a:b, channel], round(velocity * 100))

    for cue in vocals:
        a, b = span(float(cue["start"]), float(cue["end"]))
        chorus, layers = cue.get("chorus", False), cue.get("vocal_layers", 0)
        if not isinstance(chorus, bool) or type(layers) is not int or layers < 0:
            raise ValueError("Backing vocals need explicit chorus and vocal-layer evidence")
        circuit = active_mouth_circuit(chorus=chorus, vocal_layers=layers,
                                      detected_phoneme=cue.get("phoneme"))
        if circuit is None:
            continue
        channel = circuit - 1
        others = np.delete(levels[a:b, 10:], channel - 10, axis=1)
        if others.any():
            raise ValueError("Conflicting simultaneous backing-mouth poses")
        levels[a:b, channel] = 100
    return levels
