"""Decode the existing tagged XSQ strike holds for a separate 3D review rig.

Idle artwork colors are not hit evidence. Cymbal decay lights its surface,
but must never extend the arm's scheduled strike hold.
"""
from __future__ import annotations

import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

TARGETS = ('KICK', 'SNARE', 'HI_HAT', 'TOM_HIGH', 'TOM_MID', 'TOM_FLOOR',
           'CYMBAL_LEFT', 'CYMBAL_RIGHT')
PREFIX = 'HX_SNOWMAN_DRUMMER_V3_'


def decode_review_schedule(path: Path, frames: int):
    root = ET.parse(path).getroot()
    db = [e.text or '' for e in root.findall('./EffectDB/Effect')]
    strikes = np.zeros((frames, 8), dtype=np.float32)
    lighting = np.zeros_like(strikes)
    hands = np.zeros(frames, dtype=np.int8)
    unique = set()
    for e in root.findall('.//Effect'):
        component = e.get('sourceComponent', '')
        target = component.removeprefix(PREFIX)
        if target not in TARGETS:
            continue
        role = e.get('sourceRole')
        if role not in ('visual_geometry', 'visual_cymbal_decay'):
            continue
        if e.get('sourcePose') == 'shared_actuator_union':
            continue
        lo = max(0, int(e.get('startTime')) // 50)
        hi = min(frames, math.ceil(int(e.get('endTime')) / 50))
        if hi <= lo:
            continue
        settings = dict(field.split('=', 1) for field in db[int(e.get('ref'))].split(',') if '=' in field)
        intensity = float(settings.get('HELIX_DrummerIntensity',
                                      float(settings.get('E_TEXTCTRL_Eff_On_Start', '100')) / 100))
        intensity = float(np.clip(intensity, 0, 1))
        k = TARGETS.index(target)
        if role == 'visual_cymbal_decay':
            # Visual decay approximates the existing source envelope; the native
            # shimmer raster is intentionally not described as reproduced.
            decay = np.linspace(intensity, 0, hi-lo, endpoint=False)
            lighting[lo:hi, k] = np.maximum(lighting[lo:hi, k], decay)
        else:
            strikes[lo:hi, k] = np.maximum(strikes[lo:hi, k], intensity)
            lighting[lo:hi, k] = np.maximum(lighting[lo:hi, k], intensity)
            hand = e.get('sourceHand')
            if target == 'SNARE' and hand in ('left', 'right'):
                hands[lo:hi] = int(hand == 'right')
            unique.add((target, lo, hi, round(intensity, 3), hand))
    return lighting, strikes, hands, {'unique_strike_holds': len(unique),
                                     'idle_colors_used_as_strikes': False,
                                     'cymbal_decay_moves_arms': False}
