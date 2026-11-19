from pathlib import Path
import pytest

from tools.validate_xsq_structure import ValidationError, validate_xsq

def test_native_xlights_timing_rows_are_accepted(tmp_path):
    p=tmp_path/'native.xsq'
    p.write_text("""<xsequence><DisplayElements>
    <Element type="timing" name="Beats"/>
    </DisplayElements><ElementEffects>
    <Element type="timing" name="Beats"><EffectLayer><Effect name="On" startTime="0" endTime="500"/></EffectLayer></Element>
    <Element type="model" name="HX_INFINITY_SPIRAL_TREE_0001"><EffectLayer><Effect name="Bars" startTime="0" endTime="500"/></EffectLayer></Element>
    </ElementEffects></xsequence>""")
    validate_xsq(p)

def test_empty_native_timing_placeholders_fail(tmp_path):
    p=tmp_path/'empty.xsq'
    p.write_text("""<xsequence><DisplayElements><Element type="timing" name="Beats"/></DisplayElements>
    <ElementEffects><Element type="timing" name="Beats"><EffectLayer/></Element>
    <Element type="model" name="Prop"><EffectLayer/></Element></ElementEffects></xsequence>""")
    with pytest.raises(ValidationError,match="timing"):
        validate_xsq(p)

def test_legacy_phoneme_timing_still_accepted(tmp_path):
    p=tmp_path/'legacy.xsq'
    p.write_text("""<xsequence><timingtrack name="Vocal"><phoneme index="1" start="0" duration="0.2"/></timingtrack>
    <effects><Element type="model" name="Singer"/></effects></xsequence>""")
    validate_xsq(p)
