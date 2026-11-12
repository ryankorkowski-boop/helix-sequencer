"""Regression gates for the owner-rejected 16-panel Helix Motion pilot.

This tests native prop topology and source routing. A passing test does not
replace true native xLights rendering or the owner's artistic approval.
"""
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
