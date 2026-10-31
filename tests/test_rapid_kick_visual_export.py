from tools.integrate_drummer_v3_into_xsq import _merge_visual_events


def test_rapid_kick_visual_holds_keep_each_observed_onset_and_a_release_gap():
    rows=[dict(start_ms=1900+i*105,end_ms=2050+i*105,intensity=.8,
        source_type='kick',source_pose='kick_hit') for i in range(8)]
    result=_merge_visual_events(rows)
    assert len(result)==8
    assert [r['start_ms'] for r in result]==[r['start_ms'] for r in rows]
    assert all(r['source_pose']=='kick_hit' and r['intensity']==.8 for r in result)
    assert all(a['end_ms']<b['start_ms'] for a,b in zip(result,result[1:]))


def test_shared_arm_geometry_still_uses_a_union_for_overlapping_non_kicks():
    rows=[dict(start_ms=100,end_ms=250,intensity=.6,source_type='snare',source_pose='hit'),
          dict(start_ms=200,end_ms=350,intensity=.8,source_type='tom',source_pose='hit')]
    result=_merge_visual_events(rows)
    assert len(result)==1 and result[0]['end_ms']==350
    assert result[0]['intensity']==.8 and result[0]['source_pose']=='shared_actuator_union'
