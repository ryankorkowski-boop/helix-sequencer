import pytest
from core.drummer_physical_wiring import compile_contact_intervals


def test_eight_rapid_kicks_keep_eight_independent_contact_starts():
    times = [2 + i * .060 for i in range(8)]
    result = compile_contact_intervals([dict(time=t, target='kick') for t in times], duration=3)
    assert [e['start'] for e in result['circuits']['kick']] == times
    assert len(result['source_onsets']) == 8
    assert all(e['end'] < following['start'] for e, following in
               zip(result['circuits']['kick'], result['circuits']['kick'][1:]))


def test_two_snare_hands_cymbal_contacts_and_idle_are_mutually_exclusive():
    result = compile_contact_intervals([dict(time=.2, target='snare', side='left'),
        dict(time=.2, target='cymbal_right')], duration=1)
    for side in ['left', 'right']:
        assert all(not e['start'] <= .21 < e['end'] for e in result['circuits'][side+'_stick_idle'])
        assert any(e['start'] <= .5 < e['end'] for e in result['circuits'][side+'_stick_idle'])
    assert result['circuits']['body_kit_dim'] == [dict(start=0., end=1, brightness=.18)]


def test_unknown_drum_and_unspecified_snare_hand_fail_before_export():
    for hit in [dict(time=.1, target='tom'), dict(time=.1, target='snare')]:
        with pytest.raises(ValueError):
            compile_contact_intervals([hit], duration=1)
