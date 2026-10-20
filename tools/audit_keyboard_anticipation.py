"""Compare real-source native pose preparation with/without rest anticipation.

This audits source hand contacts and musical cue parity, not native video,
pitch ground truth, or physical-device performance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np

from models import keyboard_motion_plan as motion
from tools.native_source_pose_band import prepare

DRUM_PARTS = {'KICK', 'SNARE_LEFT', 'SNARE_RIGHT', 'HI_HAT', 'TOM_HIGH',
              'TOM_MID', 'TOM_FLOOR', 'CYMBAL_LEFT', 'CYMBAL_RIGHT'}


def musical_cues(path):
    with np.load(path) as data:
        return {key: data[key].copy() for key in data.files
                if key.split('::', 1)[-1].startswith(('NOTE_', 'STRING_', 'MOUTH_'))
                or key.split('::', 1)[-1] in DRUM_PARTS}


def cue_digest(cues):
    digest = hashlib.sha256()
    for key in sorted(cues):
        value = cues[key]
        digest.update(key.encode())
        digest.update(str((value.shape, value.dtype.str)).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def audit(source_root, output):
    output.mkdir(parents=True, exist_ok=False)
    reports = {}
    original = motion.plan_keyboard_hands

    def reactive(*args, **kwargs):
        kwargs['anticipation_frames'] = 0
        return original(*args, **kwargs)

    try:
        for name in ('baseline', 'candidate'):
            motion.plan_keyboard_hands = reactive if name == 'baseline' else original
            began = time.perf_counter()
            proof = prepare(source_root, output / name, eid='E14')
            reports[name] = dict(
                seconds=time.perf_counter() - began,
                audio_sha256=proof['audio_sha256'],
                contact=proof['keyboard_motion_proof']['keyboard_contact_report'])
    finally:
        motion.plan_keyboard_hands = original

    before = musical_cues(output / 'baseline' / 'expected_cues.npz')
    after = musical_cues(output / 'candidate' / 'expected_cues.npz')
    parity = (set(before) == set(after) and bool(before)
              and all(np.array_equal(before[key], after[key]) for key in before))
    baseline, candidate = (reports[name]['contact'] for name in ('baseline', 'candidate'))
    contacts_before = sum(baseline[side]['contact_frames'] for side in ('left', 'right'))
    contacts_after = sum(candidate[side]['contact_frames'] for side in ('left', 'right'))
    preserved_activity = all(baseline[side]['source_active_frames'] ==
                             candidate[side]['source_active_frames']
                             for side in ('left', 'right'))
    improvement = (contacts_after > contacts_before
                   and all(candidate[side]['contact_frames'] >= baseline[side]['contact_frames']
                           for side in ('left', 'right')))
    source_matches = reports['baseline']['audio_sha256'] == reports['candidate']['audio_sha256']
    voice_path = source_root / 'analysis/E14/voice_roles.json'
    voice_report = json.loads(voice_path.read_text()) if voice_path.is_file() else {}
    voice_activity = {}
    with np.load(source_root / 'analysis/E14/voice_roles.npz') as voices:
        for name in ('energy', 'shapes'):
            values = voices[name]
            voice_activity[name] = dict(
                shape=list(values.shape),
                active_frames_per_lane=[int(np.count_nonzero(values[:, i]))
                                        for i in range(values.shape[1])])
    vocal_evidence = dict(
        routing_report=voice_report,
        measured_lanes=voice_activity,
        report_matches_original_audio=(
            voice_report.get('source_sha256') == reports['candidate']['audio_sha256']))
    result = dict(schema='helix.keyboard_source_contact_audit.v1',
                  passed=bool(parity and source_matches and preserved_activity and improvement),
                  musical_cues_unchanged=bool(parity),
                  musical_cue_lanes=len(before),
                  baseline_cue_sha256=cue_digest(before),
                  candidate_cue_sha256=cue_digest(after),
                  source_identity_preserved=source_matches,
                  vocal_source_evidence=vocal_evidence,
                  source_active_frames_preserved=preserved_activity,
                  total_contacts_before=contacts_before, total_contacts_after=contacts_after,
                  source_contact_improved=improvement, runs=reports,
                  native_xlights_video_verified=False,
                  physical_hardware_tested=False,
                  musical_ground_truth_verified=False,
                  limitation='Source pose contacts only; medoid native rendering and owner review remain pending.')
    (output / 'keyboard-source-contact-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    return 0 if audit(args.source_root, args.output)['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
