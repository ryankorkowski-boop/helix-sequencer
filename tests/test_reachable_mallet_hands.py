from music.note_events import NoteEvent
from music.unified_mallet import unified_mallet_schedule


def note(time,pitch=72):
    return NoteEvent(time,time+.1,pitch,.8,source='other_stem_screened_mallet_estimate')


def test_reachable_mid_register_single_notes_use_both_hands_without_new_hits():
    events=[note(t) for t in (.1,.3,.5,.7)]
    schedule,omitted=unified_mallet_schedule(events,duration=1,
        reachable={'left':{72},'right':{72}})
    assert [h['side'] for h in schedule]==['left','right','left','right']
    assert [h['source_time'] for h in schedule]==[e.start for e in events]
    assert [h['source_pitch'] for h in schedule]==[e.pitch for e in events]
    assert omitted==[]


def test_hand_preference_cannot_override_physical_reach():
    schedule,omitted=unified_mallet_schedule([note(.1),note(.3),note(.5)],duration=1,
        reachable={'left':set(),'right':{72}})
    assert [h['side'] for h in schedule]==['right']*3
    assert omitted==[]


def test_two_simultaneous_notes_keep_independent_reachable_contacts():
    schedule,omitted=unified_mallet_schedule([note(.1,69),note(.1,75)],duration=1,
        reachable={'left':{69,75},'right':{69,75}})
    assert {(h['side'],h['source_pitch']) for h in schedule}=={('left',69),('right',75)}
    assert [h['source_time'] for h in schedule]==[.1,.1] and omitted==[]
