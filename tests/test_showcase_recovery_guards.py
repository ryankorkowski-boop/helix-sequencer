import json
import xml.etree.ElementTree as ET
import pytest
from tools.combine_native_stage import combine
from tools.recover_showcase_source_cache import recover


def band(tmp_path):
    b=tmp_path/'band';b.mkdir();(b/'media').mkdir();(b/'media/audio.wav').write_bytes(b'retained audio')
    root=ET.Element('xrgb');models=ET.SubElement(root,'models')
    for r in ['DRUMMER','BASS','GUITAR','PIANO','XYLOPHONE','LEAD','HARMONY']:
        ET.SubElement(models,'model',name='HX_SNOW_'+r)
    ET.ElementTree(root).write(b/'xlights_rgbeffects.xml')
    return b


def test_embedded_wrong_audio_leaves_no_candidate(tmp_path):
    b=band(tmp_path);s=tmp_path/'scene';s.mkdir();(s/'audio.wav').write_bytes(b'other song')
    out=tmp_path/'output'
    with pytest.raises(ValueError,match='identical original excerpts'):combine(s,b,out)
    assert not out.exists()


@pytest.mark.parametrize('scale',[0,-1,float('nan'),float('inf')])
def test_invalid_stage_scale_fails_before_mutation(tmp_path,scale):
    out=tmp_path/'output'
    with pytest.raises(ValueError,match='positive and finite'):combine(tmp_path/'missing',tmp_path/'missing_band',out,scale=scale)
    assert not out.exists()


def test_missing_musician_is_rejected_before_copy(tmp_path):
    b=band(tmp_path);p=b/'xlights_rgbeffects.xml';t=ET.parse(p);m=t.getroot().find('models');m.remove(m[-1]);t.write(p)
    out=tmp_path/'output'
    with pytest.raises(ValueError,match='seven-performer'):combine(tmp_path/'missing',b,out)
    assert not out.exists()


def test_recovered_analysis_must_match_audio_before_creating_cache(tmp_path):
    a=tmp_path/'archive';m=a/'05_Source_Excerpt_Manifests';c=m/'Analysis/E01';c.mkdir(parents=True)
    (m/'selected_excerpts.json').write_text(json.dumps([{'excerpt_id':'E01'}]))
    for name,key in [('verification.json','source_sha256'),('vocals.json','audio_sha256')]:
        (c/name).write_text(json.dumps({key:'incorrect'}))
    audio=a/'07_Layouts_and_Sequences/E01';audio.mkdir(parents=True);(audio/'audio.wav').write_bytes(b'audio')
    out=tmp_path/'recovered'
    with pytest.raises(ValueError,match='hash mismatch'):recover(a,out,['E01'])
    assert not (out/'analysis/E01').exists()
    assert not (out/'sources/E01').exists()
