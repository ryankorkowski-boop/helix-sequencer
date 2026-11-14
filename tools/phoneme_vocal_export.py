"""Export source-separated acoustic estimates without claiming voice ground truth."""
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from core.native_face_instructions import face_template
from core.singing_face_discovery import detect_singing_faces
from models.band_sampler_logic import NATIVE_SHAPE_NAMES, SHAPE_NAMES
from tools.phoneme_source import digest, EXPECTED_SHA256
from xlights.xsq_writer import EffectTemplate, add_effect, write_timing_track

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/audio/phoneme_vocal_separation'


def screened_lanes(cache, *, fps=100):
    """One policy shared by native Faces and the review CSV, on source time."""
    from music.vocal_qualification import screen_candidate_lanes
    sources = ('estimated_lead', 'estimated_backing')
    energy = np.column_stack([cache[s+'_energy'] for s in sources])
    shapes = np.column_stack([cache[s+'_shapes'] for s in sources])
    probability = np.column_stack([cache[s+'_presence_probability'] for s in sources])
    # The optional acoustic corroboration is confined to the same source clock.
    # Speech VAD alone can miss sustained pitched vocals in a dense mix.
    corroboration = [cache.get(s+'_acoustic_corroboration') for s in sources]
    for i, evidence in enumerate(corroboration):
        if evidence is not None:
            probability[:, i] = np.maximum(probability[:, i], evidence)
    energy, shapes, report = screen_candidate_lanes(energy, shapes, probability, fps=fps)
    return {s: (energy[:, i], shapes[:, i]) for i, s in enumerate(sources)}, report


def static_materials(garden):
    """Use only authored body nodes/colors, with no musical activity implied."""
    for model in garden.models:
        groups = {}
        nodes=set(model.submodels.get('BASE_DIM' if model.details['review_role'] == 'drummer' else 'BODY', []))
        if model.details['review_role'] in ('lead','harmony'):
            # Retain authored wooden arms; generic sequencer accents previously
            # replaced them with flashing red/white detached-looking limbs.
            for part,values in model.submodels.items():
                if part.startswith('ARM_') and part.endswith('_IDLE'):
                    nodes.update(values)
        for node in sorted(nodes):
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


def export(root, layout: Path, garden, *, fixture: Path = FIXTURE,
           expected_sha256=EXPECTED_SHA256, stemless_audio: Path | None = None,
           source_audio: Path | None = None, native_frame_ms: int | None = None):
    report = json.loads((fixture / 'diagnostic.json').read_text())
    clocks = fixture / 'acoustic_vocal_clocks.npz'
    if report.get('audio_sha256') != expected_sha256 or digest(clocks) != report.get('clock_sha256'):
        raise ValueError('Separated vocal cache does not match original source/receipt')
    if stemless_audio is not None and digest(stemless_audio) != expected_sha256:
        raise ValueError('Stemless estimate audio does not match original source')
    qualified = report.get('verification_state') == 'VERIFIED'
    shape_names = NATIVE_SHAPE_NAMES if qualified else SHAPE_NAMES
    if qualified:
        from tools.vocal_analysis_fixture import verify_fixture
        if source_audio is None or stemless_audio is not None:
            raise ValueError('Qualified vocals require original source audio and cannot use stemless replacement')
        verify_fixture(source_audio, fixture, report)
    duration_ms = round(float(root.findtext('head/sequenceDuration')) * 1000)
    duration = duration_ms / 1000
    faces = detect_singing_faces(layout)
    result = dict(source=report, independent_backing_verified=False,
                  exact_phoneme_boundaries_verified=False, removed_decorative_mouth_effects=0,
                  vocal_method='source-separated vocal estimates; broad acoustic vowel colors; no verified lexical phones', models={})
    if qualified:
        result.update(independent_backing_verified=True, vocal_method='qualified independent source vocal clocks')
    with np.load(clocks, allow_pickle=False) as cache:
        lanes = {}
        for source in ('estimated_lead', 'estimated_backing'):
            energy, shapes = cache[source + '_energy'], cache[source + '_shapes']
            if (energy.ndim != 1 or energy.shape != shapes.shape or abs(len(energy)*.01-duration) > .02
                    or not np.isfinite(energy).all() or not np.isfinite(shapes).all()
                    or np.any(energy < 0) or np.any(energy > 1) or np.any(shapes != np.floor(shapes))
                    or np.any(shapes < 0) or np.any(shapes >= len(shape_names))):
                raise ValueError('Invalid source-separated vocal clock')
            lanes[source] = (energy, shapes)
        if stemless_audio is not None:
            from tools.stemless_duet import estimate_duet
            energies = np.column_stack([lanes[s][0] for s in lanes])
            shapes = np.column_stack([lanes[s][1] for s in lanes])
            energies, shapes, estimate = estimate_duet(
                stemless_audio, energies, shapes, frames=len(energies), frame_ms=10)
            result['stemless_estimate'] = dict(estimate, audio_sha256=expected_sha256,
                source_clock_sha256=report['clock_sha256'])
            result['vocal_method'] = 'stemless mixed-audio estimate gated by retained vocal activity'
            for index, source in enumerate(lanes):
                lanes[source] = (energies[:, index], shapes[:, index])
        elif not qualified:
            lanes, confidence = screened_lanes(cache)
            result['confidence_screening'] = confidence
            result['vocal_method'] = 'independent source-separated clocks with per-lane confidence hysteresis'
        for role, source in [('LEAD', 'estimated_lead'), ('HARMONY', 'estimated_backing')]:
            target = 'HX_SNOW_' + role
            energy, shapes = lanes[source]
            track_hash = expected_sha256 if stemless_audio is not None else report['tracks'][source]['sha256']
            for element in root.find('ElementEffects'):
                name = element.get('name', '')
                if name == target or name.startswith(target + '/'):
                    result['removed_decorative_mouth_effects'] += _clear(element)
            layer = ET.SubElement(_element(root, target), 'EffectLayer', name='Helix source-separated vocal estimate')
            active = (energy > 0) & (shapes != SHAPE_NAMES.index('REST'))
            values = np.where(active, shapes, SHAPE_NAMES.index('REST'))
            step = 10
            if native_frame_ms is not None:
                if native_frame_ms < 10 or native_frame_ms % 10:
                    raise ValueError('Native frame duration must be a positive multiple of 10 ms')
                step = native_frame_ms
                # Sample each physical frame at its center. Preserve rests as
                # their own values and prevent sub-frame transitions collapsing.
                starts = np.arange(0, duration_ms, step)
                indices = starts + np.minimum(duration_ms - starts, step) // 2
                values = values[np.minimum(indices // 10, len(values)-1)]
            cuts = np.r_[0, np.flatnonzero(np.diff(values)) + 1, len(values)]
            count, sounding, rest = 0, 0, 0
            timing_name = 'Helix_' + role.title() + '_Phonemes'
            spans = []
            for a, b in zip(cuts[:-1], cuts[1:]):
                start, end = int(a)*step, min(duration_ms, int(b)*step)
                if end <= start:
                    continue
                shape = shape_names[int(values[a])]
                mouth = {'AH': 'A', 'EE': 'E', 'OH': 'O'}.get(shape, shape)
                cue = dict(target_model=target, mouth_shape='mouth_' + mouth,
                           face_definition='Helix independent phonemes')
                template = face_template(cue, faces, 'C_BUTTON_Palette1=#F1C383,C_CHECKBOX_Palette1=1')
                if template is None:
                    raise ValueError('Source singer has no exact native mapping for ' + shape)
                effect = add_effect(layer, start, end, 'Faces', template)
                effect.set('sourceMethod', 'stemless_mixed_audio_estimate' if stemless_audio is not None
                           else 'qualified_source_stem' if qualified else 'two_stage_UVR_acoustic_estimate')
                effect.set('sourceTrackSHA256', track_hash)
                effect.set('sourceTimingTrack', timing_name)
                spans.append((mouth, start, end))
                count += 1
                sounding += shape != 'REST'
                rest += shape == 'REST'
            write_timing_track(root, timing_name, spans)
            result['models'][target] = dict(faces_effect_count=count, non_rest_effect_count=sounding,
                                            rest_effect_count=rest, source_track_sha256=track_hash,
                                            timing_track=timing_name)
    export_static_materials(root, garden, duration_ms)
    return result


def export_static_materials(root, garden, duration_ms):
    """Attach authored material after instrument exporters replace model rows."""
    for model in garden.models:
        for part, nodes in model.submodels.items():
            if not part.startswith('STATIC_RGB_') or not nodes:
                continue
            element = _element(root, model.name + '/' + part)
            _clear(element)
            layer = ET.SubElement(element, 'EffectLayer', name='Helix authored material; nonmusical illumination')
            color = '#' + part.removeprefix('STATIC_RGB_')
            effect = add_effect(layer, 0, duration_ms, 'On', EffectTemplate(
                settings='E_TEXTCTRL_Eff_On_Start=90,E_TEXTCTRL_Eff_On_End=90',
                palette='C_BUTTON_Palette1='+color+',C_CHECKBOX_Palette1=1'))
            effect.set('sourceRole', 'static_authored_material')
