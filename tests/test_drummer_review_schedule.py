import xml.etree.ElementTree as ET

import numpy as np

from models.drummer_review_schedule import decode_review_schedule


def fixture(tmp_path):
    root=ET.Element('xsequence');db=ET.SubElement(root,'EffectDB')
    ET.SubElement(db,'Effect').text='HELIX_DrummerIntensity=0.8'
    ET.SubElement(db,'Effect').text='E_TEXTCTRL_Eff_On_Start=100'
    layer=ET.SubElement(root,'EffectLayer')
    def effect(target,start,end,role='visual_geometry',hand=None,pose='hit',ref='0'):
        fields={'sourceComponent':'HX_SNOWMAN_DRUMMER_V3_'+target,
                'sourceRole':role,'sourcePose':pose,'startTime':str(start),
                'endTime':str(end),'ref':ref}
        if hand:fields['sourceHand']=hand
        ET.SubElement(layer,'Effect',fields)
    effect('CYMBAL_LEFT',500,650)
    effect('CYMBAL_LEFT',500,1500,'visual_cymbal_decay',ref='1')
    effect('SNARE',100,200,hand='left');effect('SNARE',300,400,hand='right')
    effect('SNARE',100,200,hand='left')  # Neutral/wood duplicate is one strike.
    effect('TOM_HIGH',0,1500,'idle_artwork')
    effect('TOM_FLOOR',0,1500,pose='shared_actuator_union')
    p=tmp_path/'original.xsq';ET.ElementTree(root).write(p);return p


def test_idle_artwork_and_shared_actuator_union_do_not_invent_hits(tmp_path):
    light,strikes,hands,proof=decode_review_schedule(fixture(tmp_path),30)
    assert not strikes[:,3:6].any()
    assert not strikes[0].any()
    assert proof['unique_strike_holds']==3
    assert proof['idle_colors_used_as_strikes'] is False


def test_cymbal_light_decay_cannot_hold_the_arm_up(tmp_path):
    light,strikes,hands,proof=decode_review_schedule(fixture(tmp_path),30)
    assert np.allclose(strikes[10:13,6],.8)
    assert not strikes[13:,6].any()
    assert light[13,6]>.7 and light[29,6]>0
    assert proof['cymbal_decay_moves_arms'] is False


def test_snare_hands_preserve_original_hold_windows(tmp_path):
    light,strikes,hands,proof=decode_review_schedule(fixture(tmp_path),30)
    assert np.array_equal(np.flatnonzero(strikes[:,1]),[2,3,6,7])
    assert not hands[2:4].any() and hands[6:8].all()
