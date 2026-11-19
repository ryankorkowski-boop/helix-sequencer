import xml.etree.ElementTree as ET
import pytest
from core.helixville4_band_stem_map import build_helixville4_band_stem_map
from tools.validate_xsq_structure import validate_xsq, ValidationError


def test_stem_map_uses_actual_v3_model_and_keeps_legacy_default():
    original=build_helixville4_band_stem_map()
    modern=build_helixville4_band_stem_map({'HX_SNOWMAN_DRUMMER_V3':set()})
    old_drums=[t for t in original['targets'] if t['stem'] in ('kick','snare','hihat','cymbals','toms')]
    new_drums=[t for t in modern['targets'] if t['stem'] in ('kick','snare','hihat','cymbals','toms')]
    assert {t['model'] for t in old_drums}=={'HX_SNOWMAN_DRUMMER'}
    assert {t['model'] for t in new_drums}=={'HX_SNOWMAN_DRUMMER_V3'}
    assert next(t for t in new_drums if t['stem']=='toms')['submodels']==[
        'HX_SNOWMAN_DRUMMER_V3_TOM_HIGH','HX_SNOWMAN_DRUMMER_V3_TOM_MID','HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR']


@pytest.mark.parametrize('start,duration',[('nan','1'),('0','inf'),('-1','1'),('0','0')])
def test_invalid_legacy_effects_are_rejected(start,duration,tmp_path):
    path=tmp_path/'legacy.xsq'
    path.write_text(f'<xsequence><timingtrack/><effects><effect index="0" type="face" start="{start}" duration="{duration}"/></effects></xsequence>')
    with pytest.raises(ValidationError):validate_xsq(path)
