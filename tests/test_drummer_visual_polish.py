from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import map_events_to_drummer_v3_poses
from tools.build_drummer_v3_assets import _downsample_exact_mask, _nodes_from_overlay
from tools.drummer_v3_visual_masks import exact_geometry, target_surface_key
from tools.render_drummer_v3_preview import (
    TARGETS, _expand_ranges, compose_lighting, load_component_masks,
    parse_snare_hands, snare_hand_for_frame,
)

ROOT = Path(__file__).resolve().parents[1]


def test_snare_alternation_is_independent_of_other_hits_and_preserves_music():
    events = [DrumEvent(t, .7, .8, {}, i, kind) for i, (t, kind) in enumerate([
        (11.0, 'kick'), (11.48, 'snare'), (11.48, 'hihat'),
        (12.45, 'snare'), (12.5, 'kick'), (12.95, 'snare')])]
    mapped = map_events_to_drummer_v3_poses(reversed(events))
    snares = [row for row in mapped if row['drum_type'] == 'snare']
    assert [row['hand'] for row in snares] == ['left', 'right', 'left']
    assert [row['timestamp_ms'] for row in snares] == [11480, 12450, 12950]
    assert all(row['component'] == TARGETS[1] and row['end_ms']-row['timestamp_ms'] == 125 for row in snares)
    assert len(mapped) == len(events)


def test_idle_has_no_raised_arms_or_sticks_and_keeps_the_face():
    source, masks = load_component_masks()
    idle = np.asarray(compose_lighting(source, masks, []))
    for x, y in [(235, 232), (369, 225), (388, 155), (195, 195), (255, 254)]:
        assert idle[y, x, :3].max() <= 10, (x, y, idle[y, x])
    # Source face/hat remain recognisable, with no wholesale body deletion.
    assert idle[178:196, 276:319, :3].mean() > 15


def test_snare_shell_is_visible_through_kick_for_either_hand():
    source, masks = load_component_masks()
    surface = np.asarray(masks[target_surface_key(TARGETS[1])]) > 0
    # Explicit lower-shell anchors, absent from the photographed snare.
    assert surface[297, 283] and surface[282, 235] and surface[282, 331]
    for hand in ('left', 'right'):
        snare = np.asarray(compose_lighting(source, masks, [TARGETS[1]], snare_hand=hand))
        combo = np.asarray(compose_lighting(source, masks, [TARGETS[0], TARGETS[1]], snare_hand=hand))
        assert np.all(combo[surface] >= snare[surface])
        r, g, b = snare[297, 283, :3]
        assert r > 200 and b > 180 and g < 160


def test_native_strikes_keep_every_projected_arm_node():
    source, _ = load_component_masks()
    geometry = exact_geometry(source)
    root = ET.parse(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel').getroot()
    nodes = {s.get('name'): _expand_ranges(s.get('line0')) for s in root.findall('./subModels/subModel')}
    for name, art in geometry['actuators'].items():
        projected = _nodes_from_overlay(_downsample_exact_mask(art.getchannel('A'), 96, 72), 96, 72)
        assert projected == nodes['HX_SNOWMAN_DRUMMER_V3_'+name]


def test_native_and_preview_share_alternating_snare_metadata(tmp_path, monkeypatch):
    import tools.integrate_drummer_v3_into_xsq as integration
    audio = tmp_path/'stub.wav'; audio.touch()
    base = tmp_path/'base.xsq'; base.write_text('<xsequence><ElementEffects/></xsequence>')
    events = [DrumEvent(t, .8, .8, {}, i, 'snare') for i, t in enumerate([11.48, 12.45, 12.95])]
    monkeypatch.setattr(integration, '_analyze_real_audio', lambda p: (events, {}))
    output = tmp_path/'out.xsq'; integration.inject_drummer_v3(base, output, audio)
    root = ET.parse(output).getroot()
    for part, starts in [('SNARE_ARM_STICK', ['11480','12950']), ('SNARE_RIGHT_ARM_STICK',['12450'])]:
        for color in ('NEUTRAL', 'WOOD'):
            effects = root.findall(f'./ElementEffects/Element[@name="HX_SNOWMAN_DRUMMER_V3_{part}_{color}"]/EffectLayer/Effect')
            assert [e.get('startTime') for e in effects] == starts
    hits = parse_snare_hands(output)
    assert [snare_hand_for_frame(hits,t,60) for t in (11480,12450,12950)] == ['left','right','left']
    # This rendering starts late in the song: do not restart hand alternation.
    assert snare_hand_for_frame(hits,12448,60) == 'right'


def test_right_snare_is_a_distinct_complete_source_pose():
    source, masks = load_component_masks()
    left = np.asarray(compose_lighting(source,masks,[TARGETS[1]],snare_hand='left')).astype(int)
    right = np.asarray(compose_lighting(source,masks,[TARGETS[1]],snare_hand='right')).astype(int)
    assert (left[200:249,200:275,:3]-right[200:249,200:275,:3]).max() > 80
    assert (right[202:250,298:355,:3]-left[202:250,298:355,:3]).max() > 80
