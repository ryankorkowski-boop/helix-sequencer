"""Only count contacts on the visible stage member."""
from types import SimpleNamespace
import numpy as np
from core.visible_pitched_contact_audit import visible_pitched_contacts


def test_visible_pianist_does_not_claim_hidden_mallet_strikes():
    p=SimpleNamespace(
        scene=SimpleNamespace(legacy_mallet_player=False),
        key_assignments={'left':[60,None,64], 'right':[72,None,None]},
        mallet_schedule=[{'time':0,'pitch':60,'side':'left'}],
        mallet_targets={'left':(np.zeros(3),np.zeros(3))},
    )
    hit=visible_pitched_contacts(p,0)
    assert hit['key_contact_frames']==2
    assert hit['mallet_contacts']==0
    assert visible_pitched_contacts(p,1)['key_contact_frames']==0
    assert visible_pitched_contacts(p,2)['key_contact_frames']==1


def test_opt_in_legacy_mallet_reports_actual_visible_hit_and_error():
    p=SimpleNamespace(
        scene=SimpleNamespace(legacy_mallet_player=True,bars={72:np.array([1.,2.,3.])}),
        mallet_schedule=[{'time':0.,'pitch':72,'side':'right'}],
        mallet_targets={'right':(np.zeros(3),np.array([1.,2.0845,3.]))},
    )
    hit=visible_pitched_contacts(p,0)
    assert hit['key_contact_frames']==0
    assert hit['mallet_contacts']==1
    assert hit['maximum_mallet_contact_error']<1e-8
    assert visible_pitched_contacts(p,1)['mallet_contacts']==0
