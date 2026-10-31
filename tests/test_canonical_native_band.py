import xml.etree.ElementTree as ET
import pytest
from models.ultimate_showcase import Garden
from models.canonical_native_band import add_band, visual_identity
from tools.phoneme_vocal_export import export
from tools.build_helpers.ultimate_showcase import write_layout


@pytest.fixture(scope='module')
def garden():
    g = Garden()
    add_band(g)
    return g


def test_actual_solid_surface_cast_and_channels(garden):
    assert {m.name for m in garden.models} == {
        'HX_SNOW_' + r for r in ('DRUMMER','BASS','GUITAR','PIANO','LEAD','HARMONY')}
    for m in garden.models:
        assert len(m.points) > 100
        assert m.details['geometry_source'] == 'models.final_band_scene.FinalBandScene'
        assert m.details['owner_approved_native_visuals'] is False
        assert all(1 <= n <= len(m.points) for nodes in m.submodels.values() for n in nodes)
    for a, b in zip(garden.models, garden.models[1:]):
        assert a.start + a.channels == b.start
    piano = next(m for m in garden.models if m.name.endswith('_PIANO'))
    assert sum(bool(v) for k,v in piano.submodels.items() if k.startswith('NOTE_MIDI_')) >= 24


def test_source_drummer_ranges_preserved_and_native_limitation(garden):
    drummer = garden.models[0]
    assert drummer.details['canonical_drummer']
    for component in ('KICK','HI_HAT','SNARE_LEFT','SNARE_RIGHT','TOM_HIGH','TOM_MID','TOM_FLOOR','CYMBAL_LEFT','CYMBAL_RIGHT'):
        assert drummer.submodels[component]
    assert visual_identity()['canonical_solid_3d_band'] is False
    assert visual_identity()['canonical_surface_geometry'] is True


def test_presence_screened_vocal_cache_maps_to_distinct_singers(garden, tmp_path):
    write_layout(garden, tmp_path, include_demo=False)
    root=ET.Element('xsequence')
    ET.SubElement(ET.SubElement(root,'head'),'sequenceDuration').text='34.88'
    ET.SubElement(root,'DisplayElements'); ET.SubElement(root,'ElementEffects')
    result=export(root,tmp_path/'xlights_rgbeffects.xml',garden)
    for role, expected in [('LEAD',264), ('HARMONY',86)]:
        # Golden counts bind this cache revision to its screened source clocks.
        assert result['models']['HX_SNOW_'+role]['faces_effect_count'] == expected
        singer=next(m for m in garden.models if m.name=='HX_SNOW_'+role)
        assert set(k.removeprefix('MOUTH_') for k in singer.submodels if k.startswith('MOUTH_')) == {
            'AI','E','FV','L','MBP','O','U','WQ','etc','rest'}
        assert singer.details['mouth_scale_relative_to_solid_scene'] <= .5
        dynamic=set().union(*(set(v) for k,v in singer.submodels.items() if k.startswith(('MOUTH_','NOTE_MIDI_','STRING_','ARM_'))))
        assert dynamic.isdisjoint(singer.submodels['BODY'])


def test_dense_native_surface_uses_source_mesh_bounds_and_repeatable_material_light():
    import numpy as np
    from models.final_band_native import SurfaceParts
    from models.band_performance_scene import matrix
    item=dict(kind='sphere',matrix=matrix((1.,2.,3.),(.5,.6,.4)),color=np.array((1.,.8,.6)))
    a,b=(SurfaceParts((0,0,0),surface_spacing=.08) for _ in range(2))
    for parts in (a,b):parts.primitive('BODY',item)
    np.testing.assert_array_equal(a.points,b.points)
    assert a.colors==b.colors
    assert len(a.points)>1000
    np.testing.assert_allclose(np.ptp(a.points,axis=0),(5,6,4),atol=1/16)
    assert len(set(a.colors))>20
    assert all(len(color)==7 and color.startswith('#') for color in a.colors)
