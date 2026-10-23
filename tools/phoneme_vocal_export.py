"""Export source-separated acoustic estimates without claiming voice ground truth."""
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from core.native_face_instructions import face_template
from core.singing_face_discovery import detect_singing_faces
from models.band_sampler_logic import SHAPE_NAMES
from tools.phoneme_source import digest, EXPECTED_SHA256
from xlights.xsq_writer import EffectTemplate, add_effect

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/audio/phoneme_vocal_separation'


def static_materials(garden):
    """Use only authored body nodes/colors, with no musical activity implied."""
    for model in garden.models:
        groups = {}
        for node in model.submodels.get('BASE_DIM' if model.details['review_role'] == 'drummer' else 'BODY', []):
            groups.setdefault(model.colors[node-1], []).append(node)
        for color, nodes in groups.items():
            model.submodels['STATIC_RGB_' + color.removeprefix('#')] = nodes


def _element(root, name):
    effects = root.find('ElementEffects')
    found = next((e for e in effects if e.get('name') == name), None)
    if found is None:
        ET.SubElement(root.find('DisplayElements'), 'Element', type='model', name=name, visible='1', collapsed='1')
        found = ET.SubElement(effects, 'Element', type='model', name=name)
    return found


def _clear(element):
    count = 0
    for layer in list(element):
        if layer.tag in {'EffectLayer', 'SubModelEffectLayer'}:
            count += len(layer.findall('Effect'))
            element.remove(layer)
    return count


def export(root, layout: Path, garden, *, fixture: Path = FIXTURE):
    report = json.loads((fixture / 'diagnostic.json').read_text())
    clocks = fixture / 'acoustic_vocal_clocks.npz'
    if report.get('audio_sha256') != EXPECTED_SHA256 or digest(clocks) != report.get('clock_sha256'):
        raise ValueError('Separated vocal cache does not match original source/receipt')
    duration_ms = round(float(root.findtext('head/sequenceDuration')) * 1000)
    duration = duration_ms / 1000
    faces = detect_singing_faces(layout)
    result = dict(source=report, independent_backing_verified=False,
                  exact_phoneme_boundaries_verified=False, removed_decorative_mouth_effects=0,
                  vocal_method='source-separated vocal estimates; broad acoustic vowel colors; no verified lexical phones', models={})
    with np.load(clocks, allow_pickle=False) as cache:
        for role, source in [('LEAD', 'estimated_lead'), ('HARMONY', 'estimated_backing')]:
            target = 'HX_SNOW_' + role
            energy, shapes = cache[source + '_energy'], cache[source + '_shapes']
            if (energy.ndim != 1 or energy.shape != shapes.shape or abs(len(energy)*.01-duration) > .02
                    or not np.isfinite(energy).all() or not np.isfinite(shapes).all()
                    or np.any(energy < 0) or np.any(energy > 1) or np.any(shapes != np.floor(shapes))
                    or np.any(shapes < 0) or np.any(shapes >= len(SHAPE_NAMES))):
                raise ValueError('Invalid source-separated vocal clock')
            for element in root.find('ElementEffects'):
                name = element.get('name', '')
                if name == target or name.startswith(target + '/MOUTH_'):
                    result['removed_decorative_mouth_effects'] += _clear(element)
            layer = ET.SubElement(_element(root, target), 'EffectLayer', name='Helix source-separated vocal estimate')
            active = (energy > 0) & (shapes != SHAPE_NAMES.index('REST'))
            values = np.where(active, shapes, SHAPE_NAMES.index('REST'))
            cuts = np.r_[0, np.flatnonzero(np.diff(values)) + 1, len(values)]
            count, sounding, rest = 0, 0, 0
            for a, b in zip(cuts[:-1], cuts[1:]):
                start, end = int(a)*10, min(duration_ms, int(b)*10)
                if end <= start:
                    continue
                shape = SHAPE_NAMES[int(values[a])]
                mouth = {'AH': 'A', 'EE': 'E', 'OH': 'O'}.get(shape, shape)
                cue = dict(target_model=target, mouth_shape='mouth_' + mouth,
                           face_definition='Helix independent phonemes')
                template = face_template(cue, faces, 'C_BUTTON_Palette1=#F1C383,C_CHECKBOX_Palette1=1')
                if template is None:
                    raise ValueError('Source singer has no exact native mapping for ' + shape)
                effect = add_effect(layer, start, end, 'Faces', template)
                effect.set('sourceMethod', 'two_stage_UVR_acoustic_estimate')
                effect.set('sourceTrackSHA256', report['tracks'][source]['sha256'])
                count += 1
                sounding += shape != 'REST'
                rest += shape == 'REST'
            result['models'][target] = dict(faces_effect_count=count, non_rest_effect_count=sounding,
                                            rest_effect_count=rest, source_track_sha256=report['tracks'][source]['sha256'])
    for model in garden.models:
        for part, nodes in model.submodels.items():
            if not part.startswith('STATIC_RGB_') or not nodes:
                continue
            element = _element(root, model.name + '/' + part)
            _clear(element)
            layer = ET.SubElement(element, 'EffectLayer', name='Helix authored material; nonmusical illumination')
            color = '#' + part.removeprefix('STATIC_RGB_')
            effect = add_effect(layer, 0, duration_ms, 'On', EffectTemplate(
                settings='E_TEXTCTRL_Eff_On_Start=70,E_TEXTCTRL_Eff_On_End=70',
                palette='C_BUTTON_Palette1='+color+',C_CHECKBOX_Palette1=1'))
            effect.set('sourceRole', 'static_authored_material')
    return result
