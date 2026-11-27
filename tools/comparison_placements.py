"""Place ordinary comparison props with the existing layout-aware Prime sequencer."""
from __future__ import annotations

import copy
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from core.audio_run_cache import AudioRunCache
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_snowman_ensemble import NativeSequence
from tools.run_showcase_audio_batch import model_routes
from tools.showcase_audio_native import native_music_xsq


def uses_prime(model):
    details = model.details
    if model.kind not in ('pixel', 'ac'):
        return False
    if any(details.get(key) for key in ('review_role', 'generic_singer', 'keyboard_pitch_rungs',
                                        'percussion_component', 'spatial_showcase_native_xyz')):
        return False
    if details.get('musical_role') in ('lead', 'harmony'):
        return False
    # Preserve literal keyboard banks on the canonical controller map.
    return not (details.get('original_start_channel') and
                (model.name.isdigit() or 'candy cane' in model.name.lower()))


def import_placements(sequence, native, models):
    """Import direct model/submodel rows, preserving clocks, layer order and native tables."""
    settings = [node.text or '' for node in native.findall('EffectDB/Effect')]
    palettes = [node.text or '' for node in native.findall('ColorPalettes/ColorPalette')]
    counts = {}
    for row in native.findall('ElementEffects/Element'):
        name = row.get('name')
        if name not in models or row.get('type') != 'model':
            continue
        target = sequence.elements[name]
        for layer in row:
            effects = layer.findall('Effect')
            if not effects:
                continue
            if layer.tag == 'SubModelEffectLayer' and layer.get('name') not in models[name].submodels:
                raise ValueError(f'Unknown Prime target {name}/{layer.get("name")}')
            if layer.tag == 'EffectLayer' and not list(target[0]):
                target.remove(target[0])
            for effect in effects:
                effect.set('settings', settings[int(effect.attrib.pop('ref'))])
                effect.set('palette', palettes[int(effect.get('palette'))])
                effect.set('id', str(sequence.identifier))
                sequence.identifier += 1
                effect.set('sourceMethod', 'layout_prime_placement')
            target.append(layer)
            counts[name] = counts.get(name, 0) + len(effects)
    return counts


def compose_yard(sequence, audio: Path, cache: AudioRunCache):
    """Sequence only ordinary physical targets. Source-owned instruments keep their own rows."""
    from core import effect_engine as engine

    yard = copy.copy(sequence.g)
    yard.models = [model for model in yard.models if uses_prime(model)]
    if not yard.models:
        return {}
    with tempfile.TemporaryDirectory(prefix='helix-yard-') as work:
        folder = Path(work)
        write_layout(yard, folder, include_demo=False)
        duration = sequence.duration / 1000
        template = folder / 'template.xsq'
        seed = NativeSequence(yard, duration, audio.name, yard.title)
        # Prime removes the one-millisecond library seed after discovering native defaults.
        layer = seed.elements[yard.models[0].name].find('EffectLayer')
        ET.SubElement(layer, 'Effect', name='On', startTime='0', endTime='1',
                      settings='E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100',
                      palette=f'C_BUTTON_Palette1={yard.palette[0]},C_CHECKBOX_Palette1=1')
        seed.write(template)
        tuning = engine.RuntimeTuning(
            layout_file=folder/'xlights_rgbeffects.xml', template_guidance=False,
            workspace_history_enabled=False, learning_memory_enabled=False,
            matrix_intelligence=False, polish_enabled=False, variant_count=1,
            birdsong_enabled=False, birdsong_auto=False, audio_reactive_profile='showcase',
            audio_reactive_intensity=1.6, spatial_awareness=.85, chase_style='radial_out',
            model_overrides=model_routes(yard, include_ac=True), max_layers_per_prop=3,
            ac_lights_only=all(m.kind == 'ac' for m in yard.models),
        )
        raw = folder / 'yard.xsq'
        engine.run_variant(engine.VARIANTS['v27.3'], template, audio, raw, engine.base.UserProfile(),
                           tuning=tuning, analysis_cache=cache)
        output = folder / 'native.xsq'
        native_music_xsq(raw, output, yard, audio, duration, include_ac=True)
        return import_placements(sequence, ET.parse(output).getroot(), {m.name: m for m in yard.models})
