"""Pure adapter for connecting model-aware choices to Helix's effect engine.

No sequence is mutated here. Call select_placement before native XSQ insertion;
use the returned effect only after checking the installed xLights catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.model_effect_policy import ModelCapability, EffectChoice, choose_effect


MODEL_ALIASES = {
    'megatree': 'tree', 'mega tree': 'tree', 'mini tree': 'tree',
    'arches': 'arch', 'arch': 'arch', 'single strand': 'line',
    'string': 'line', 'roofline': 'outline', 'house outline': 'outline',
    'spinner': 'spinner', 'snowflake': 'star', 'stars': 'star',
    'pixel matrix': 'matrix', 'matrix': 'matrix', 'icicles': 'icicle',
    'floodlight': 'flood', 'flood': 'flood', 'singing face': 'face',
    'faces': 'face',
}

EVENT_ROLES = {
    'kick': 'hit', 'snare': 'hit', 'drum': 'hit', 'cymbal': 'hit',
    'bass': 'hit', 'note': 'melody', 'piano': 'melody', 'guitar': 'melody',
    'melody': 'melody', 'build': 'build', 'drop': 'build',
    'pad': 'ambient', 'atmosphere': 'ambient', 'ambient': 'ambient',
    'vocal': 'vocal', 'phoneme': 'vocal',
}


@dataclass(frozen=True)
class PlacementDecision:
    target: str
    choice: EffectChoice
    requires_native_validation: bool = True
    native_render_verified: bool = False


def normalize_kind(kind: str, name: str = '') -> str:
    text = (kind or '').strip().lower()
    if text in MODEL_ALIASES:
        return MODEL_ALIASES[text]
    name_lower = name.lower()
    for alias, mapped in sorted(MODEL_ALIASES.items(), key=lambda item: -len(item[0])):
        if alias in name_lower:
            return mapped
    return text if text in {'tree', 'arch', 'line', 'outline', 'spinner', 'matrix', 'icicle', 'star', 'flood', 'face'} else 'line'


def select_placement(*, name: str, display_as: str, pixel_count: int,
                     rgb: bool, event: str, width: int = 1, height: int = 1,
                     supported_effects: set[str] | None = None) -> PlacementDecision:
    """Choose an effect for one model, retaining independent target identity.

    A supplied native effect catalog is authoritative: fallback rather than
    inserting unsupported effects. Unknown catalogs require later validation.
    """
    role = EVENT_ROLES.get(event.lower().strip())
    if role is None:
        raise ValueError(f'Unknown musical event: {event}')
    kind = normalize_kind(display_as, name)
    model = ModelCapability(name=name, kind=kind, pixels=pixel_count,
                            rgb=rgb, width=width, height=height)
    choice = choose_effect(model, role)
    if supported_effects is not None and choice.effect not in supported_effects:
        fallback = 'On' if 'On' in supported_effects else 'Ramp' if 'Ramp' in supported_effects else None
        if fallback is None:
            raise ValueError('No compatible fallback effect in native catalog')
        choice = EffectChoice(fallback, 'Default', role, 'Native effect catalog fallback')
    return PlacementDecision(target=name, choice=choice,
                             requires_native_validation=supported_effects is None)


def native_template_choice(*, model, event: str, supported_effects: set[str],
                           template_library: Mapping, asset_roots=()) -> PlacementDecision | None:
    """Production guard: require an authored template and any Shader asset.

    Catalog membership does not establish native rendering. Preserve template
    settings/render style, targeted submodel choreography and the face router.
    """
    from pathlib import Path
    if (model is None or model.is_submodel or model.total_pixels < 1
            or not model.is_rgb_capable() or model.is_single_color()
            or event in {'vocal', 'phoneme'} or not supported_effects):
        return None
    kind = normalize_kind(model.type, model.name)
    width = model.strings if kind == 'matrix' else 1
    height = model.nodes_per_string if kind == 'matrix' else 1
    decision = select_placement(name=model.name, display_as=kind,
        pixel_count=model.total_pixels, rgb=True, event=event,
        width=width, height=height, supported_effects=supported_effects)
    template = template_library.get(decision.choice.effect.strip().lower())
    if template is None or not template.settings or not template.palette:
        return None
    if decision.choice.effect.lower() == 'shader':
        settings = dict(part.split('=', 1) for part in template.settings.split(',') if '=' in part)
        raw = settings.get('E_0FILEPICKERCTRL_IFS', '').strip()
        if not raw:
            return None
        asset = Path(raw).expanduser()
        candidates = [asset] if asset.is_absolute() else [Path(root) / asset for root in asset_roots]
        if not any(path.is_file() and path.suffix.lower() == '.fs' for path in candidates):
            return None
    return decision


def automatic_template_choice(*, model, requested: str, explicit_tpl, layer: str,
                              family: str, label: str, stem: str, tuning, history,
                              supported_effects: set[str], template_library: Mapping,
                              asset_roots=()) -> PlacementDecision | None:
    """Preserve authored events, AC routes, style overrides and learned choices."""
    if (explicit_tpl is not None or (requested or 'On').strip().lower() not in {'on', 'ramp'}
            or tuning.ac_lights_only or layer in tuning.preferred_effect_layers
            or (tuning.base_effect, tuning.motion_effect, tuning.accent_effect) != ('On', 'Ramp', 'On')
            or (history and history.family_effects.get(family))):
        return None
    event = ('vocal' if stem == 'vocals'
             else 'build' if any(word in str(label).lower() for word in ('build', 'drop'))
             else 'drum' if stem == 'drums'
             else 'bass' if stem == 'bass'
             else 'ambient' if layer == 'base' else 'note')
    return native_template_choice(model=model, event=event,
        supported_effects=supported_effects, template_library=template_library,
        asset_roots=asset_roots)
