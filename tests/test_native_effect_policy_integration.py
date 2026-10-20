"""Behavior of the guarded production adapter, templates and style precedence."""
from types import SimpleNamespace
from pathlib import Path
import xml.etree.ElementTree as ET

from core.effect_engine import RuntimeTuning, pick_runtime_effect, resolve_effect_template
from core.model_parser import Model
from core.helix_effect_adapter import automatic_template_choice, native_template_choice
from xlights import xsq_writer as writer


def model(kind='icicle', rgb=True, *, submodel=False, pixels=64):
    return Model(name=kind.title(), display_as=kind, type=kind,
        strings=8, nodes_per_string=8, total_pixels=pixels, start_channel=1,
        coordinates=None, end_coordinates=None, orientation=None, wiring=None,
        string_type='RGB Nodes' if rgb else 'Single Color White', color_family=None,
        is_submodel=submodel)


def template(settings='E_SLIDER_Meteors_Count=8'):
    return writer.EffectTemplate(settings=settings, palette='C_BUTTON_Palette1=#00FF00,C_CHECKBOX_Palette1=1')


def automatic(**overrides):
    args=dict(model=model(),requested='On',explicit_tpl=None,layer='motion',family='line',
        label='melody',stem='other',tuning=RuntimeTuning(),history=None,
        supported_effects={'On','Meteors'},template_library={'meteors':template()},asset_roots=())
    args.update(overrides)
    return automatic_template_choice(**args)


def test_meteors_candidate_uses_its_native_template_in_editable_model_row():
    decision=automatic()
    assert decision.choice.effect=='Meteors'
    native=template()
    chosen=resolve_effect_template(effect_name=decision.choice.effect,explicit_tpl=None,
        template_library={'meteors':native},fallback_tpl=template('fallback'))
    root=ET.Element('xsequence');layer=ET.SubElement(ET.SubElement(root,'Element',name=decision.target),'EffectLayer')
    writer.add_effect(layer,100,400,decision.choice.effect,chosen)
    effect=ET.fromstring(ET.tostring(root)).find('./Element/EffectLayer/Effect')
    assert effect.get('name')=='Meteors'
    assert effect.get('startTime')=='100' and effect.get('endTime')=='400'
    assert decision.native_render_verified is False
    assert chosen.settings==native.settings


def test_missing_native_template_does_not_invent_settings():
    assert automatic(template_library={}) is None
    assert automatic(supported_effects={'On'},template_library={}) is None


def test_authored_events_styles_history_and_ac_paths_remain_authoritative():
    assert automatic(requested='Wave') is None
    assert automatic(explicit_tpl=template()) is None
    assert automatic(tuning=RuntimeTuning(preferred_effect_layers=('motion',))) is None
    assert automatic(tuning=RuntimeTuning(motion_effect='Bars')) is None
    assert automatic(tuning=RuntimeTuning(ac_lights_only=True)) is None
    assert automatic(model=model(rgb=False)) is None
    assert automatic(model=model(submodel=True)) is None
    assert automatic(history=SimpleNamespace(family_effects={'line':['Wave']})) is None
    assert automatic(stem='vocals', label='build') is None


def test_shader_requires_native_fs_asset_and_template(tmp_path):
    kwargs=dict(model=model('matrix'),event='build',supported_effects={'Shader','On'},
                template_library={'shader':template('E_0FILEPICKERCTRL_IFS=wave.fs')},asset_roots=(tmp_path,))
    assert native_template_choice(**kwargs) is None
    (tmp_path/'wave.fs').write_text('/* unit asset only: not native compile evidence */')
    decision=native_template_choice(**kwargs)
    assert decision.choice.effect=='Shader'
    assert decision.native_render_verified is False
    kwargs['model']=model('matrix',pixels=1)
    assert native_template_choice(**kwargs) is None


def test_manual_on_is_not_replaced_by_matrix_geometry_defaults():
    tuning=RuntimeTuning(base_effect='On',preferred_effect_layers=('base',))
    effect=pick_runtime_effect(requested='On',layer='base',family='matrix',parsed_model=model('matrix'),
        tuning=tuning,catalog={'effect_names':['On','Color Wash','Wave']},workspace_history=None,fallback='On')
    assert effect=='On'


def test_style_motion_precedes_generic_matrix_default():
    effect=pick_runtime_effect(requested='On',layer='motion',family='matrix',parsed_model=model('matrix'),
        tuning=RuntimeTuning(motion_effect='Wave',preferred_effect_layers=('motion',)),
        catalog={'effect_names':['On','Bars','Wave']},workspace_history=None,fallback='On')
    assert effect=='Wave'


def test_runtime_tuning_and_cli_share_single_variant_default():
    assert RuntimeTuning().variant_count==1
