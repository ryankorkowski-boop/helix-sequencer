"""Regression gates for the owner-rejected 16-panel Helix Motion pilot.

This tests native prop topology and source routing. A passing test does not
replace true native xLights rendering or the owner's artistic approval.
"""
import pytest

from models.advanced_full_song_showcase import build_showcase


def test_final_four_have_independent_native_props_and_source_roles():
    names = set()
    for number in (13, 14, 15, 16):
        calls = []
        def band(g, plan, **kwargs):
            calls.append((g, kwargs))
            return ('canonical-band-required',)
        g, cast = build_showcase(number, {'cues': {}}, duration=1., native_band=band)
        current = {m.name for m in g.models}
        assert len(current) == len(g.models), f'Duplicate native model in panel {number}'
        assert all(m.points.size and m.channels > 0 for m in g.models)
        assert len(g.models) >= 25, f'Panel {number} too sparse for hero showcase'
        assert len({m.zone for m in g.models}) >= 4
        roles = {m.details.get('musical_role') for m in g.models}
        assert {'guitarist', 'bassist', 'keyboardist', 'drummer'} <= roles
        assert all(m.details.get('source_display_floor', 1) <= .25 for m in g.models)
        assert not calls if number != 16 else len(calls) == 1
        assert (cast is not None) == (number == 16)
        if calls:
            assert calls[0][1]['rock'] is False
            assert calls[0][1]['duration'] == 1.
        signature = frozenset((m.name, m.zone) for m in g.models)
        assert signature not in names, 'One advanced panel duplicates another'
        names.add(signature)


def test_advanced_panels_do_not_invent_voice_events():
    from tools.source_spatial_direction import schedule
    g, _ = build_showcase(14, {'cues': {}}, duration=1.,
                          native_band=lambda *args, **kwargs: None)
    plan = {'cues': {role: [] for role in ('guitarist', 'bassist', 'keyboardist', 'drummer')}}
    for m in g.models:
        assert schedule(m, plan, {}, 1000) == [], 'No audio events means no decorative fake beat'


def test_residential_inventory_and_original_ac_addresses():
    from collections import Counter
    from pathlib import Path
    from core.model_parser import parse_layout
    from models.full_song_layouts import NAMES, build

    assert len(NAMES) == len(set(NAMES)) == 16
    for panel, channels in ((1, 16), (2, 64), (3, 256)):
        garden, cast = build(panel, {}, duration=1)
        assert cast is None
        assert sum(model.channels for model in garden.models) == channels
        if panel == 3:
            original = parse_layout(Path(__file__).resolve().parents[1] / 'xlights_rgbeffects.xml')
            assert {m.name: m.start for m in garden.models} == {
                m.name: m.start_channel for m in original.models.values() if not m.is_submodel
            }

    for panel, count in ((4, 0), (5, 0), (6, 1), (7, 2), (8, 0), (9, 0), (10, 0), (12, 2)):
        garden, _ = build(panel, {}, duration=1)
        assert sum(m.zone == 'MEGA_TREES' for m in garden.models) == count
        assert len({m.name for m in garden.models}) == len(garden.models)
        if panel in (8, 9):
            faces = [m for m in garden.models if m.details.get('generic_singer')]
            assert Counter(m.details['generic_singer'] for m in faces) == {
                'estimated_lead': 1, 'estimated_backing': 1,
            }
            assert all(m.attrs['BlackTransparency'] == '100' for m in faces)


def test_showcase_drummer_exports_source_depth_and_materials():
    from collections import Counter
    from models.full_song_layouts import build
    from models.source_drummer_3d import SOURCE_SHA256
    from tools.render_drummer_v3_preview import TARGETS

    plan = {'cues': {'drummer': [
        dict(start_ms=150, end_ms=270, kind='kick', velocity=.8),
        dict(start_ms=450, end_ms=570, kind='hihat', velocity=.8),
        dict(start_ms=700, end_ms=820, kind='snare', velocity=.8),
    ]}}
    garden, (drummer, states, proof) = build(11, plan, duration=1)
    assert Counter(m.details['review_role'] for m in garden.models) == {
        role: 1 for role in ('drummer', 'bass', 'guitar', 'piano', 'lead', 'harmony')
    }
    assert proof['source_sha256'] == SOURCE_SHA256
    assert all(item['watertight'] and item['depth'] > 0 for item in proof['closed_components'])
    assert proof['resolved_strikes'] == 3
    assert len(set(states)) > 1
    assert all(drummer.submodels[target + '_SURFACE'] for target in TARGETS)
    assert len({drummer.colors[n - 1] for n in drummer.submodels['BASE_DIM']}) > 40
    kick = drummer.points[[n - 1 for n in drummer.submodels[TARGETS[0] + '_SURFACE']]]
    hat = drummer.points[[n - 1 for n in drummer.submodels[TARGETS[2] + '_SURFACE']]]
    assert kick[:, 1].mean() < hat[:, 1].mean()
    assert kick[:, 2].max() - kick[:, 2].min() > 2



def test_showcase_facades_follow_each_house_and_stay_behind_its_lights(tmp_path):
    import xml.etree.ElementTree as ET
    from models.full_song_layouts import build
    from tools.native_residential_context import add_showcase_context

    for panel, count in ((1, 1), (4, 1), (7, 1), (13, 3)):
        folder = tmp_path / str(panel)
        folder.mkdir()
        layout = folder / 'xlights_rgbeffects.xml'
        layout.write_text('<xrgb><models /></xrgb>')
        garden, _ = build(panel, {}, duration=1)
        add_showcase_context(folder, garden)
        add_showcase_context(folder, garden)
        root = ET.parse(layout)
        assert list(root.find('models')) == []
        objects = root.findall('./view_objects/view_object')
        assert len(objects) == count
        for obj in objects:
            prefix = obj.get('name').removesuffix(' ambient facade')
            vertices = [
                [float(value) for value in row.split()[1:]]
                for row in (folder / obj.get('ObjFile')).read_text().splitlines()
                if row.startswith('v ')
            ]
            roof = next(model for model in garden.models if model.name == prefix + '_ROOF')
            assert max(z for _, _, z in vertices) < min(roof.points[:, 2])
            assert max(y for _, y, _ in vertices) == pytest.approx(max(roof.points[:, 1]), abs=1e-5)
            assert min(x for x, _, _ in vertices) == pytest.approx(min(roof.points[:, 0]), abs=1e-5)



def test_qualified_vocal_layouts_have_ten_distinct_native_mouths():
    from models.full_song_layouts import build
    from models.band_sampler_logic import NATIVE_SHAPE_NAMES

    for panel in (8, 9, 11):
        garden, _ = build(panel, {}, duration=1, native_extended_mouths=True)
        singers = [model for model in garden.models if model.details.get('generic_singer')
                   or model.details.get('review_role') in ('lead', 'harmony')]
        assert len(singers) == 2
        for singer in singers:
            parts = [tuple(singer.submodels['MOUTH_' + name]) for name in NATIVE_SHAPE_NAMES]
            assert all(parts) and len(set(parts)) == 10
            assert not set(singer.submodels.get('BODY', ())) & set().union(*map(set, parts))


def test_showcase_faces_fit_house_and_use_separate_yard_groups():
    import numpy as np
    from models.full_song_layouts import build

    for panel, max_height in ((8, 15), (9, 24)):
        garden, _ = build(panel, {}, duration=1)
        faces = [model for model in garden.models if model.details.get('showcase_face')]
        assert len(faces) == 2
        assert all(np.ptp(model.points[:, 1]) <= max_height for model in faces)
        assert {model.details.get('showcase_group', '').split('_')[0] for model in garden.models} >= {
            'FACADE', 'FOREGROUND', 'YARD',
        }


def test_showcase_bass_and_guitar_use_original_attacks_and_string_contacts():
    from types import SimpleNamespace
    from xml.etree import ElementTree as ET
    from tools.canonical_band_cues import export_instruments

    models = [
        SimpleNamespace(name='Bass', details={'review_role': 'bass', 'native_string_contacts': True},
                        submodels={'STRING_0': [1], 'ARM_PLUCK_STRING_0': [2],
                                   'ARM_FINGER_STRING_0_FRET_4': [3]}),
        SimpleNamespace(name='Guitar', details={'review_role': 'guitar', 'native_string_contacts': True},
                        submodels={'STRING_0': [1], 'ARM_STRUM_STRING_0': [2],
                                   'ARM_FINGER_STRING_0_FRET_4': [3]}),
    ]
    root = ET.fromstring('<xsequence><head><sequenceDuration>1</sequenceDuration></head>'
                         '<DisplayElements/><ElementEffects/></xsequence>')
    timing = {'source_start_ms': 100, 'source_end_ms': 260, 'start_ms': 170, 'end_ms': 510}
    plan = {'cues': {'bassist': [dict(timing, kind='pluck', pitch_midi=32)],
                     'guitarist': [dict(timing, kind='picking', pitch_midi=44)]}}
    receipt = export_instruments(root, SimpleNamespace(models=models), plan)
    for model in models:
        assert receipt['models'][model.name]['arm_gestures'] == 2
        assert receipt['models'][model.name]['mapped_events'] == 1
        elements = root.findall(f'./ElementEffects/Element[@name="{model.name}/STRING_0"]/EffectLayer/Effect')
        assert [(e.get('startTime'), e.get('endTime')) for e in elements] == [('100', '260')]
