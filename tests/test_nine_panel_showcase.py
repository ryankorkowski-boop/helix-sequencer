import pytest

from models.nine_panel_showcase import NAMES, build


def test_nine_panel_order():
    assert len(NAMES) == 9
    assert NAMES[4] == 'Canonical snowman band'
    assert NAMES[5:] == ('Fire & Ice', 'Celestial Orrery', 'Quantum City', 'Infinite Kingdom')


@pytest.mark.parametrize('number,channels', [(1, 16), (2, 256)])
def test_legacy_ac_budget(number, channels):
    garden, band = build(number, {}, duration=30)
    assert band is None
    assert sum(model.channels for model in garden.models) == channels


@pytest.mark.parametrize('number', [3, 4, 6, 7, 8, 9])
def test_distinct_native_geometry(number):
    garden, band = build(number, {}, duration=30)
    assert band is None
    assert len(garden.models) > 0
    assert len({m.name for m in garden.models}) == len(garden.models)
    assert all(len(m.points) and m.channels > 0 for m in garden.models)
    assert all(m.start >= 1 for m in garden.models)
    if number == 4:
        assert any(m.details.get('generic_singer') for m in garden.models)
    if number == 9:
        assert len({m.zone for m in garden.models if 'DISTRICT' in m.zone}) >= 8


def test_starter_house_independent_source_banks():
    garden, _ = build(3, {}, duration=30)
    by_name = {m.name:m for m in garden.models}
    assert {m.details['musical_role'] for m in garden.models} == {
        'guitarist', 'keyboardist', 'bassist', 'drummer'}
    for role in ('guitarist', 'keyboardist'):
        bank = [m for m in garden.models if m.details['musical_role'] == role]
        assert len(bank) == 2
        assert {m.details['source_route_rank'] for m in bank} == {0,1}
        assert all(m.details['source_route_count'] == 2 for m in bank)
    assert by_name['HOME_DOOR'].details['percussion_component'] == 'cymbal'
