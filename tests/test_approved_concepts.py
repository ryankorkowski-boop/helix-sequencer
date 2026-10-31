"""Native geometry, binding and preservation contracts for the selected batch."""
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from models.approved_concepts import ROOT, build_concept, catalog
from tools.build_approved_concepts import export


@pytest.mark.parametrize('concept',catalog(),ids=lambda c:c['id']+'_'+c['name'])
def test_native_geometry_and_channel_map(concept):
    g=build_concept(concept)
    assert len({m.name for m in g.models})==len(g.models)
    end=0
    for m in g.models:
        assert m.start==end+1
        end=m.start+m.channels-1
        assert np.isfinite(m.points).all()
        assert all(1<=n<=len(m.points) for nodes in m.submodels.values() for n in nodes)
        assert m.display=='Custom'
        if 'CustomModelCompressed' not in m.attrs:continue
        raw=np.array([[int(x) for x in token.split(',')] for token in m.attrs['CustomModelCompressed'].split(';')])
        assert np.array_equal(raw[:,0],np.arange(1,len(m.points)+1))
        assert len(np.unique(raw[:,1:],axis=0))==len(raw)
        widths=np.array([int(m.attrs['parm1']),int(m.attrs['parm2']),int(m.attrs['Depth'])])
        local=np.c_[raw[:,2],widths[1]-1-raw[:,1],widths[2]-1-raw[:,3]]-(widths-1)/2
        scale=np.array([float(m.attrs['Scale'+axis]) for axis in 'XYZ'])
        origin=np.array([float(m.attrs['WorldPos'+axis]) for axis in 'XYZ'])
        np.testing.assert_allclose(local*scale+origin,m.points,atol=1e-6)
    assert end==sum(m.channels for m in g.models)


@pytest.mark.parametrize('concept',catalog(),ids=lambda c:c['id'])
def test_portable_native_bindings(tmp_path,concept):
    g,xsq,manifest=export(concept,tmp_path)
    layout=ET.parse(tmp_path/'xlights_rgbeffects.xml').getroot()
    models={m.get('name'):m for m in layout.findall('models/model')}
    assert len(models)==len(g.models)
    for m in models.values():
        assert m.get('Controller')==''
        for key in ('CustomBkgImage','HelixVisualSource'):
            if m.get(key):assert (tmp_path/m.get(key)).is_file()
        assert (tmp_path/'models'/(m.get('name')+'.xmodel')).is_file()
    for group in layout.findall('modelGroups/modelGroup'):
        for name in group.get('models').split(','):
            base,_,sub=name.partition('/')
            assert base in models
            if sub:assert models[base].find(f'subModel[@name="{sub}"]') is not None
    sequence=ET.parse(xsq).getroot()
    assert sequence.findtext('head/sequenceType')=='Animation'
    assert sequence.findtext('head/sequenceDuration')=='24.000'
    assert not sequence.findtext('head/mediaFile')
    assert len(ET.parse(tmp_path/'xlights_networks.xml').getroot())==0
    db=sequence.findall('EffectDB/Effect');palettes=sequence.findall('ColorPalettes/ColorPalette')
    for element in sequence.findall('ElementEffects/Element'):
        model=models[element.get('name')]
        for layer in element.findall('SubModelEffectLayer'):
            assert model.find(f'subModel[@name="{layer.get("name")}"]') is not None
        for effect in element.findall('.//Effect'):
            assert effect.get('name')=='On'
            assert 0<=int(effect.get('ref'))<len(db)
            assert 0<=int(effect.get('palette'))<len(palettes)
            start,end=int(effect.get('startTime')),int(effect.get('endTime'))
            assert 0<=start<end<=24000
            assert start%50==end%50==0
    assert manifest['native_families']==['Custom']
    assert not manifest['native_coverage_complete']


def test_stage_drummer_has_unchanged_canonical_ranges():
    from tools.render_drummer_v3_preview import _expand_ranges
    source=ET.parse(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel').getroot()
    for c in [c for c in catalog() if int(c['id']) in (15,16,31,32,55)]:
        g=build_concept(c)
        drummer=next(m for m in g.models if m.details.get('canonical_drummer'))
        assert drummer.attrs['CustomModel']==source.get('CustomModel')
        for sub in source.findall('subModels/subModel'):
            assert set(drummer.submodels[sub.get('name')])==_expand_ranges(sub.get('line0'))
        assert drummer.submodels['BODY_KEEPALIVE']
        assert drummer.attrs['ModelBrightness']=='100'


def test_approval_catalog_contains_each_design_once():
    assert [int(c['id']) for c in catalog()]==list(range(1,63))


def test_replacement_poses_have_dark_holds_and_complete_cycles(tmp_path):
    # A full native render checks these schedules again against actual FSEQ values.
    from tools.build_approved_concepts import pose_intervals
    for c in catalog()[42:]:
        g=build_concept(c)
        poses=[m for m in g.models if 'pose_index' in m.details]
        if int(c['id']) in (57,58):
            assert all('assembly_index' in m.details or 'domino_index' in m.details for m in g.models)
            continue
        assert poses
        for m in poses:
            intervals=pose_intervals(m)
            assert intervals
            assert all(a%600==b%600==0 and a<b<=24000 for a,b in intervals)
            assert sum(b-a for a,b in intervals)<24000
        tracks={m.details['pose_track'] for m in poses}
        for track in tracks:
            group=[m for m in poses if m.details['pose_track']==track]
            assert {m.details['pose_index'] for m in group}==set(range(group[0].details['pose_count']))
