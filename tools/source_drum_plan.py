"""Use a source-bound learned percussion transcript in the production band plan.

The existing typed drum mapper and effect/motion builders remain authoritative.
No beat-grid filler, inferred physical tom identities or count tuning is added.
"""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import hashlib

from audio.drum_classification import empty_drum_streams, stream_key_for_type
from audio.drum_transcription import load_drum_transcription
from core.snowman_band import _build_intelligent_drum_cues


def bind(plan, transcript, audio):
    events, diagnostic=load_drum_transcription(transcript,audio)
    streams=empty_drum_streams()
    for event in events:
        streams[stream_key_for_type(event.drum_type)].append(event)
    parts=[SimpleNamespace(start_ms=round(p['start_time']*1000),
                           end_ms=round(p['end_time']*1000),label=p['name'])
           for p in plan.get('global_timeline',{}).get('song_parts',[])]
    cues,kit,debug=_build_intelligent_drum_cues(parts,drum_event_streams=streams,
        kicks=[],snares=[],hats=[],releases=[])
    # Source-local timestamps must remain valid even without song-part metadata.
    import soundfile as sf
    duration_ms=round(sf.info(audio).duration*1000)
    for cue in cues:
        if not 0<=cue['start_ms']<duration_ms:
            raise ValueError('Percussion timestamp outside the original source')
        cue['end_ms']=min(duration_ms,cue['end_ms'])
    result=deepcopy(plan)
    result['cues']['drummer']=cues
    result['kit']=kit
    receipt=dict(audio_sha256=diagnostic['audio_sha256'],
        transcript_sha256=hashlib.sha256(Path(transcript).read_bytes()).hexdigest(),
        source_engine=diagnostic['analysis_engine'],source_event_count=len(events),
        mapped_event_count=len(cues),source_diagnostic=diagnostic,mapping=debug,
        independent_accuracy_verified=False)
    result.setdefault('debug',{})['source_bound_percussion']=receipt
    return result,receipt
