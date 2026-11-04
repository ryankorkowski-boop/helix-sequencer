from pathlib import Path
import sys,json,dataclasses
sys.path.insert(0,sys.argv[1])
from tools.drummer_ground_truth_oracle import fixture_events,TARGETS
from audio.drum_classification import DrumEvent,empty_drum_streams,stream_key_for_type
from core.snowman_band import _build_intelligent_drum_cues
from mapping.drum_mapper import map_events_to_drummer_v3_poses
streams=empty_drum_streams()
for i,event in enumerate(fixture_events()):
 target=event.target;info={}
 if target=='HI_HAT':kind='hihat'
 elif target.startswith('TOM_'):kind='tom';info={'tom_class':target.split('_',1)[1].lower(),'tom_class_confidence':1.0}
 elif target.startswith('CYMBAL_'):kind='cymbal'
 else:kind=target.lower()
 streams[stream_key_for_type(kind)].append(DrumEvent(event.time,.9,1.0,info,i,kind,'canonical_event_oracle'))
cues,kit,debug=_build_intelligent_drum_cues([],drum_event_streams=streams,kicks=[],snares=[],hats=[],releases=[])
actions=map_events_to_drummer_v3_poses([e for values in streams.values() for e in values])
actual=[(a['timestamp_ms'],a['component'].removeprefix('HX_SNOWMAN_DRUMMER_V3_')) for a in actions]
expected=[(round(e.time*1000),e.target) for e in fixture_events()]
assert sorted(actual)==sorted(expected),(actual,expected)
assert len(cues)==68
result={'events':68,'targets':list(TARGETS),'exact_fixture_mapping':True,'mapped_events':actual,'cues':cues,'debug':debug}
Path(sys.argv[2]).write_text(json.dumps(result,sort_keys=True,indent=2,default=lambda x:dataclasses.asdict(x))+'\n')
