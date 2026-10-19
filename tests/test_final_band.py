import numpy as np
import pytest

from models.final_band_scene import FinalBandScene
from models.distinct_band_stages import DistinctBandScene, TwinBandGarden
from music.note_events import NoteEvent
from music.magic_keyboard import magic_keyboard_events
from music.unified_mallet import unified_mallet_schedule


def test_final_scenes_show_one_keyboardist_instead_of_legacy_mallet_character():
    for rock in (False, True):
        scene = FinalBandScene(rock=rock)
        assert len(scene.visible_roles) == 6
        assert 'piano' in scene.visible_roles and 'xylophone' not in scene.visible_roles
        assert any(o['kind'] != 'hidden' and o.get('performer_role') == 'piano'
                   for o in scene.instances)
        assert not any(o['kind'] != 'hidden' and o.get('performer_role') == 'xylophone'
                       for o in scene.instances)
        assert scene.technical_proof['pitched_character'] == 'piano'
        assert not any(o['kind'] == 'wire_sphere' for o in scene.instances)
        assert all(np.isfinite(o['matrix']).all() for o in scene.instances)
        if rock:
            for role in ('bass', 'guitar', 'lead', 'harmony', 'piano'):
                assert next(o for o in scene.instances if o['name'] == role+'_torso')['kind'] == 'box'
                assert any(o['name'] == role+'_rock_boot' for o in scene.instances)


def test_legacy_six_member_mallet_cast_remains_opt_in():
    scene = FinalBandScene(legacy_mallet_player=True, rock=True)
    assert 'xylophone' in scene.visible_roles and 'piano' not in scene.visible_roles
    assert scene.technical_proof['legacy_mallet_player']
    assert not any(o['kind'] != 'hidden' and o.get('performer_role') == 'piano'
                   for o in scene.instances)
    assert any(o['kind'] != 'hidden' and o.get('performer_role') == 'xylophone'
               for o in scene.instances)
    assert all(p[0] > 5 for p in scene.bars.values())
    assert next(o for o in scene.instances if o['name'] == 'xylophone_torso')['kind'] == 'box'


def test_final_costumes_preserve_approved_guitar_contacts_and_closed_instruments():
    old = DistinctBandScene('ember_amphitheatre')
    new = FinalBandScene(rock=True)
    for a, b in zip(old.strings['guitar'], new.strings['guitar']):
        np.testing.assert_array_equal(a['a'], b['a']); np.testing.assert_array_equal(a['b'], b['b'])
        assert a['ids'] == b['ids']
    for name in ('electric_guitar_body', 'upright_bass_body'):
        a = next(o['mesh'] for o in old.custom if o['name'] == name)
        b = next(o['mesh'] for o in new.custom if o['name'] == name)
        assert b.is_watertight
        np.testing.assert_array_equal(a.vertices, b.vertices)


def test_unified_schedule_preserves_runs_chords_and_source_times_without_filler():
    notes = [NoteEvent(.103, .3, 60, .7, source='piano_stem_harmonic_estimate'),
             NoteEvent(.103, .3, 64, .9, source='horn_harmonic_onset', confidence=.9),
             NoteEvent(.103, .3, 67, .8, source='synth_pitched_onset', confidence=.9),
             NoteEvent(.40, .6, 25, .9, source='piano_stem_harmonic_estimate'),
             NoteEvent(.60, .8, 106, .8, source='piano_stem_harmonic_estimate'),
             NoteEvent(.80, 1., 70, 1, source='drum_pitched', confidence=.99)]
    actual, omitted = unified_mallet_schedule(notes, duration=2)
    assert [h['source_pitch'] for h in actual] == [64, 67, 25, 106]
    assert {h['side'] for h in actual[:2]} == {'left', 'right'}
    assert len(omitted) == 1 and omitted[0]['pitch'] == 60
    assert all(abs(h['display_error_ms']) <= 25 for h in actual)
    assert all(48 <= h['pitch'] <= 96 and h['pitch'] % 12 == h['source_pitch'] % 12 for h in actual)
    assert unified_mallet_schedule([], duration=2) == ([], [])


def test_magic_keyboard_rejects_nonfinite_confidence_fractional_notes_and_duration():
    notes = [NoteEvent(0, .2, 64, source='synth_pitched', confidence=float('nan')),
             NoteEvent(0, .2, 64.5, source='piano_stem_harmonic_estimate')]
    assert magic_keyboard_events(notes, duration=1) == []
    assert magic_keyboard_events([], [dict(source_time=.1, pitch=60, velocity=.8)], duration=1)[0].start == .1
    with pytest.raises(ValueError): magic_keyboard_events([], duration=float('nan'))


def test_final_twin_stages_keep_independent_slot_banks():
    garden = TwinBandGarden(FinalBandScene(), FinalBandScene('circuit_garage', rock=True))
    banks = [{dst['slot'] for dst, src, world in garden.sources if src['slot'] >= 0 and world[0, 3] == x}
             for x in (-10, 10)]
    assert banks[0] and banks[1] and not banks[0] & banks[1]


def test_solid_singer_mouths_attach_to_faces_without_changing_voice_cues():
    from models.expressive_band_face import update_expressive_mouth
    for rock in (False, True):
        scene=FinalBandScene(rock=rock)
        for role in ('lead','harmony'):
            head=next(o for o in scene.instances if o['name']==role+'_head')['matrix']
            ids=scene.expressive_mouths[role];center=ids['center']
            assert np.allclose(center[:2],head[:2,3]+(0,-.12))
            assert 0<center[2]-head[2,3]<=np.linalg.norm(head[:3,2])+.01
            for shape in ('REST','AH','EE','OH','MBP','L'):
                update_expressive_mouth(scene,role,shape,.8)
                assert np.allclose(scene.instances[ids['cavity']]['matrix'][:3,3],center)
                assert scene.instances[ids['lips']]['mouth_shape']==shape
