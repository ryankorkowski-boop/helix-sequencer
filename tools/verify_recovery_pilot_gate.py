"""Require hash-bound timing/reference evidence before scaling rejected pilots."""
import argparse
import json
from pathlib import Path
from tools.phoneme_source import digest,EXPECTED_SHA256


def check(show):
    show=Path(show);manifest=json.loads((show/'run_manifest.json').read_text())
    native=manifest.get('native_preview',{})
    evidence=show/'pilot_acceptance.json'
    if not evidence.is_file():raise ValueError('Pilot acceptance evidence missing: vocal timing and approved-reference identity gates remain open; do not scale to the full collection')
    r=json.loads(evidence.read_text())
    if native.get('status')!='success' or not Path(native.get('mp4','')).is_file():raise ValueError('Pilot has no successful native movie')
    # Alternate owner audio must pass the same gate without borrowing the old
    # Phoneme hash, filename or acceptance receipt.
    sequence_name=manifest.get('sequence_file','Phoneme_Test_Hook_Helix.xsq')
    if not isinstance(sequence_name,str) or Path(sequence_name).name!=sequence_name or not sequence_name.endswith('.xsq'):
        raise ValueError('Pilot sequence must be a local XSQ filename')
    source_hash=manifest.get('audio_sha256',EXPECTED_SHA256)
    expected=dict(audio_sha256=source_hash,xsq_sha256=digest(show/sequence_name),
                  layout_sha256=digest(show/'xlights_rgbeffects.xml'),native_movie_sha256=digest(Path(native['mp4'])))
    if any(r.get(k)!=v for k,v in expected.items()):raise ValueError('Pilot acceptance is stale or belongs to a different source/movie')
    if native.get('audio_sha256')!=source_hash:
        raise ValueError('Pilot native soundtrack does not match its source')
    reference=r.get('approved_reference_sha256','')
    if len(reference)!=64 or any(c not in '0123456789abcdef' for c in reference):raise ValueError('Actual approved-reference asset hash required')
    if not (r.get('reference_frame_comparison_passed') is True and r.get('full_recording_vocal_presence_verified') is True
            and r.get('phantom_opening_count')==0 and r.get('independent_singer_routes_preserved') is True):
        raise ValueError('Canonical reference or full-recording vocal acceptance failed')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('show',type=Path)
    a=p.parse_args();check(a.show)
