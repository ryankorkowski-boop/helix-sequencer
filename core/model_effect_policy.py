"""Conservative model-aware xLights effect selection policy.

Candidates are used by the guarded production adapter. Native template settings,
assets and rendered output need separate validation.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelCapability:
    name: str
    kind: str
    pixels: int
    rgb: bool = True
    width: int = 1
    height: int = 1

@dataclass(frozen=True)
class EffectChoice:
    effect: str
    render_style: str
    role: str
    rationale: str

_EFFECTS = {
    'tree': {'melody': 'Spirals', 'build': 'Morph', 'hit': 'Shockwave', 'ambient': 'Twinkle'},
    'arch': {'melody': 'Single Strand', 'build': 'Morph', 'hit': 'Bars', 'ambient': 'Wave'},
    'line': {'melody': 'Single Strand', 'build': 'Marquee', 'hit': 'On', 'ambient': 'Twinkle'},
    'outline': {'melody': 'Marquee', 'build': 'Color Wash', 'hit': 'On', 'ambient': 'Twinkle'},
    'spinner': {'melody': 'Pinwheel', 'build': 'Fan', 'hit': 'Shockwave', 'ambient': 'Twinkle'},
    'matrix': {'melody': 'Morph', 'build': 'Shader', 'hit': 'Shockwave', 'ambient': 'Plasma'},
    'icicle': {'melody': 'Meteors', 'build': 'Meteors', 'hit': 'On', 'ambient': 'Twinkle'},
    'star': {'melody': 'Twinkle', 'build': 'Shockwave', 'hit': 'On', 'ambient': 'Twinkle'},
    'flood': {'melody': 'Color Wash', 'build': 'Color Wash', 'hit': 'On', 'ambient': 'On'},
    'face': {'vocal': 'Faces', 'melody': 'On', 'build': 'On', 'hit': 'On', 'ambient': 'On'},
}

def choose_effect(model: ModelCapability, role: str) -> EffectChoice:
    """Select a compatible candidate; never claim native validation."""
    if model.pixels < 1:
        raise ValueError('Model must contain at least one pixel/channel')
    if role not in {'melody', 'build', 'hit', 'ambient', 'vocal'}:
        raise ValueError(f'Unsupported role: {role}')
    if not model.rgb or model.pixels == 1:
        return EffectChoice('On' if role == 'hit' else 'Ramp', 'Default', role,
                            'AC or single-pixel model: avoid spatial RGB effects')
    kind = model.kind.lower()
    effects = _EFFECTS.get(kind, _EFFECTS['line'])
    effect = effects.get(role, 'On')
    if effect in {'Shader', 'Plasma', 'Morph'} and (model.width < 8 or model.height < 8):
        effect = 'On' if role == 'hit' else 'Twinkle'
    if effect in {'Meteors', 'Spirals', 'Pinwheel', 'Fan', 'Shockwave'} and model.pixels < 12:
        effect = 'On' if role == 'hit' else 'Twinkle'
    render = 'Single Line' if kind in {'arch', 'line', 'icicle'} else 'Default'
    return EffectChoice(effect, render, role, f'{kind} geometry and {role} musical role')
