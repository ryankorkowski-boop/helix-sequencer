from pathlib import Path
import xml.etree.ElementTree as ET
from tools.export_drummer_only_xsq import export


def test_isolation_removes_other_effects_corrects_media_and_preserves_hits(tmp_path,monkeypatch):
    source=tmp_path/'integrated.xsq';output=tmp_path/'isolated.xsq'
    source.write_text('''<xsequence><head><mediaFile>C:/obsolete.wav</mediaFile><sequenceDuration>132</sequenceDuration></head><DisplayElements><Element name="House"/></DisplayElements><ElementEffects><Element name="House"><EffectLayer><Effect name="On" startTime="0" endTime="100"/></EffectLayer></Element><Element name="HX_SNOWMAN_DRUMMER_V3_KICK"><EffectLayer visible="0"><Effect name="On" startTime="11000" endTime="11150" source="HelixDrummerV3"/></EffectLayer></Element><Element name="HX_SNOWMAN_DRUMMER_V3_KICK_SURFACE"><EffectLayer visible="1"><Effect name="On" startTime="11000" endTime="11150" source="HelixDrummerV3"/></EffectLayer></Element></ElementEffects></xsequence>''')
    monkeypatch.setattr('tools.export_drummer_only_xsq.librosa.get_duration',lambda **kw:237.44)
    export(source,output,Path('Helix Audiolights.mp3'))
    root=ET.parse(output).getroot()
    assert root.findtext('./head/mediaFile')=='Helix Audiolights.mp3'
    assert root.findtext('./head/sequenceDuration')=='237.440'
    assert {e.get('name') for e in root.findall('./DisplayElements/Element')}=={'HX_SNOWMAN_DRUMMER_V3_KICK','HX_SNOWMAN_DRUMMER_V3_KICK_SURFACE'}
    assert len(root.findall('./ElementEffects/Element'))==2
    assert source.read_text().find('obsolete.wav')>0
