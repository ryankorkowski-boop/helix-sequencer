"""Expose source-estimate activity and known-nonvocal conflicts without muting it."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.phoneme_vocal_export import FIXTURE
from tools.phoneme_source import digest,EXPECTED_SHA256


def intervals(active,hop_ms=10):
    active=np.asarray(active,dtype=bool)
    cuts=np.r_[0,np.flatnonzero(np.diff(active))+1,len(active)]
    return [(int(a)*hop_ms,int(b)*hop_ms) for a,b in zip(cuts[:-1],cuts[1:]) if active[a]]


def audit(fixture=FIXTURE,nonvocal_intervals=()):
    fixture=Path(fixture);receipt=json.loads((fixture/'diagnostic.json').read_text())
    clock=fixture/'acoustic_vocal_clocks.npz'
    if receipt['audio_sha256']!=EXPECTED_SHA256 or receipt['clock_sha256']!=digest(clock):
        raise ValueError('Vocal clock/source provenance mismatch')
    result=dict(schema='helix.vocal-clock-conflict-audit.v1',audio_sha256=EXPECTED_SHA256,
        clock_sha256=digest(clock),clock_hop_ms=10,native_frame_ms=50,lanes={},
        activity_masks_changed=False,source_separation_verified=False,passed=False,
        reason='Presence and voice identity are estimates; owner timing rejection remains open')
    with np.load(clock,allow_pickle=False) as cache:
        for lane in ('estimated_lead','estimated_backing'):
            energy=cache[lane+'_energy'];active=energy>0
            conflicts=[]
            for a,b in nonvocal_intervals:
                for start,end in intervals(active):
                    if max(a,start)<min(b,end):conflicts.append([max(a,start),min(b,end)])
            result['lanes'][lane]=dict(active_intervals_ms=intervals(active),
                ending_active_intervals_ms=[(a,b) for a,b in intervals(active) if b>32000],
                verified_nonvocal_conflicts_ms=conflicts,
                source_track_sha256=receipt['tracks'][lane]['sha256'],
                native_quantization_uncertainty_ms=50)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(audit(),indent=2)+'\n')
