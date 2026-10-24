import numpy as np
from tools.audit_vocal_clock import intervals,audit


def test_silence_and_rest_transitions_have_no_hold_or_offset():
    assert intervals(np.zeros(100))==[]
    assert intervals([0,1,1,0,0,1,0])==[(10,30),(50,60)]


def test_real_ending_conflict_is_reported_without_blanket_muting_or_claimed_pass():
    result=audit(nonvocal_intervals=[(33100,34450)])
    assert result['passed'] is False
    assert result['activity_masks_changed'] is False
    for lane in result['lanes'].values():
        assert lane['verified_nonvocal_conflicts_ms']
    lead=result['lanes']['estimated_lead'];backing=result['lanes']['estimated_backing']
    assert lead['active_intervals_ms']!=backing['active_intervals_ms']
    assert lead['source_track_sha256']!=backing['source_track_sha256']
