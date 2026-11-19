import numpy as np
from models.flourish_showcase import build_flourish_garden,envelope
from models.ultimate_showcase import family,NATIVE_TYPES
from tools.build_helpers.ultimate_showcase_preview import read_fseq


def test_ordered_paths_preserve_native_families_and_channels():
    g=build_flourish_garden()
    assert set(NATIVE_TYPES)=={family(m.display) for m in g.models}
    assert len({m.name for m in g.models})==len(g.models)
    flows=[m for m in g.models if 'musical_flow' in m.details]
    assert len(flows)==80 and len({m.zone for m in flows})==6
    end=1
    for model in g.models:
        assert model.start==end
        end+=model.channels
        if model.details.get('musical_flow'):
            nodes=model.attrs['CustomModelCompressed'].split(';')
            assert len(nodes)==len(model.points)
            assert len({n.split(',',1)[1] for n in nodes})==len(nodes)


def test_flourishes_follow_measured_onsets_and_order():
    g=build_flourish_garden();a=next(m for m in g.models if m.name=='HX_FLOW_SPIRAL_1_01');b=next(m for m in g.models if m.name=='HX_FLOW_SPIRAL_1_12')
    no_attacks=envelope(a,100,[],np.ones(100))
    assert np.allclose(no_attacks,.07)
    first=envelope(a,100,[(1.,1.)],np.zeros(100));last=envelope(b,100,[(1.,1.)],np.zeros(100))
    assert first.argmax()==20 and last.argmax()==33
    assert np.allclose(first[:20],.07) and np.allclose(last[:33],.07)


def test_fseq_preserves_brightness_without_uint8_overflow(tmp_path,monkeypatch):
    from models.ultimate_showcase import Garden
    from tools import render_flourish_showcase as tool
    g=Garden();g.custom('TEST',[(0,0,0),(1,0,0)],'TEST','Palette test',['#FFFFFF','#FFD98A'],{})
    g.models[0].start=1
    monkeypatch.setattr(tool,'OUT',tmp_path)
    levels=np.array([[100,50,0]],np.uint8)
    frames,step=read_fseq(tool.write_fseq(g,levels))
    assert step==50
    assert frames.tolist()==[[255,255,255,255,217,138],[127,127,127,127,108,69],[0,0,0,0,0,0]]
