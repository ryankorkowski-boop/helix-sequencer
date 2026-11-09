from pathlib import Path

from tools.build_source_ac_review import geometry
from tools.source_spatial_direction import schedule


ROOT = Path(__file__).resolve().parents[1]


def test_original_note_and_cane_circuits_use_keyboard_source():
    models = geometry(ROOT / 'xlights_rgbeffects.xml').models
    notes = [m for m in models if m.name.isdigit() or 'Candy Cane' in m.name]
    assert len(notes) == 64
    assert all(m.details['musical_role'] == 'keyboardist' for m in notes)


def test_measured_build_onsets_travel_without_broadcast_or_filling_rests():
    models = geometry(ROOT / 'xlights_rgbeffects.xml').models
    bank = [m for m in models if m.name.startswith('North Candy Cane')]
    assert len(bank) == 16
    cues = [dict(start_ms=100+i*300, end_ms=260+i*300, pitch_midi=60,
                 velocity=.8, section='build') for i in range(6)]
    plan = dict(cues={'keyboardist': cues})
    events = {m.name: schedule(m, plan, {}, 2000) for m in bank}
    primary = []
    for cue in cues:
        active = [(m, e) for m in bank for e in events[m.name]
                  if e['source_start_ms'] == cue['start_ms']]
        assert 1 < len(active) < len(bank)
        assert all(cue['start_ms'] <= e['start_ms'] < e['end_ms'] <= cue['end_ms']
                   for _, e in active)
        primary.append(next(m.details['source_route_rank'] for m, e in active
                            if e['propagation_delay_ms'] == 0))
    assert primary == list(range(6))
    assert len({tuple((e['start_ms'], e['end_ms']) for e in rows)
                for rows in events.values()}) > 6
    assert all(not schedule(m, dict(cues={'keyboardist': []}), {}, 2000) for m in bank)


def test_explicit_synchronized_accent_and_pitch_roles_remain_deterministic():
    models = geometry(ROOT / 'xlights_rgbeffects.xml').models
    bank = [m for m in models if m.name.startswith('North Candy Cane')]
    cue = dict(start_ms=100, end_ms=260, pitch_midi=60, velocity=.8, section='chorus',
               synchronized_accent=True)
    plan = dict(cues={'keyboardist': [cue]})
    forward = {m.name: schedule(m, plan, {}, 1000) for m in bank}
    reverse = {m.name: schedule(m, plan, {}, 1000) for m in reversed(bank)}
    assert forward == reverse
    assert all(len(events) == 1 and events[0]['start_ms'] == 100
               for events in forward.values())


def test_drum_banks_keep_component_ownership_and_original_channel_colors():
    models = geometry(ROOT / 'xlights_rgbeffects.xml').models
    bank = [m for m in models if m.details['musical_role'] == 'drummer']
    cue = dict(start_ms=100, end_ms=260, velocity=.8, kind='snare', section='verse')
    plan = dict(cues={'drummer': [cue]})
    events = [(m, schedule(m, plan, {}, 1000)) for m in bank]
    assert any(rows for _, rows in events)
    assert all(not rows or m.details['percussion_component'] == 'snare' for m, rows in events)
    assert {m.start for m in models} == set(range(1,257))
    assert all(m.kind == 'ac' and m.channels == 1 for m in models)
