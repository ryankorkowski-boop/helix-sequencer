"""Per-model AC/pixel routing from explicit configuration, including mixed shows.

No device probing or live output occurs here. LOR is a transport, not proof of
AC: Pixie/PixCon controllers also speak LOR. Sixteen ports are not 16 circuits.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re


@dataclass(frozen=True)
class OutputCapability:
    mode: str
    reason: str
    circuit_limit: int | None = None

    def to_dict(self): return asdict(self)


def detect_output(model_attrs: dict, controller_attrs: dict | None = None) -> OutputCapability:
    m = {str(k).lower():str(v).lower() for k,v in model_attrs.items()}
    c = {str(k).lower():str(v).lower() for k,v in (controller_attrs or {}).items()}
    explicit = m.get('helixoutputmode', '')
    string = m.get('stringtype', '')
    hardware = ' '.join(c.get(k, '') for k in ('model','product','controllermodel','description','type'))
    ac = bool(re.search(r'ctb\s*16|lor\s*160[02]|lor\s*800|ac.?16',hardware))
    pixel = bool(re.search(r'pixie|pixcon|falcon|kulp|hinkspix',hardware))
    rgb = 'rgb' in string or 'rgbw' in string
    if explicit not in ('', 'ac16', 'pixel'):
        raise ValueError('HelixOutputMode must be ac16 or pixel')
    if (ac and (pixel or rgb or explicit=='pixel')) or (pixel and explicit=='ac16'):
        raise ValueError('Model and controller capabilities conflict')
    if explicit == 'ac16' or ac:
        return OutputCapability('ac16','explicit model profile' if explicit else 'identified AC controller',16)
    if explicit == 'pixel' or rgb or pixel:
        return OutputCapability('pixel','RGB model or identified pixel controller')
    return OutputCapability('unknown','Insufficient configuration; do not guess from LOR protocol or channel count')


def resolve_layout_outputs(layout, networks):
    """Resolve saved xLights XML controller associations, never a global guess."""
    controllers = {}
    for element in networks.iter():
        name = element.get('Name',element.get('name'))
        if name: controllers[name] = dict(element.attrib)
    return {m.get('name'):detect_output(m.attrib,controllers.get(m.get('Controller',''),{})).to_dict()
            for m in layout.findall('./models/model')}


def encode_output(levels, mode, *, colors=None):
    import numpy as np
    values = np.asarray(levels, dtype=np.float32)
    if not np.isfinite(values).all(): raise ValueError('Nonfinite output level')
    values = np.clip(values,0,1)
    if mode == 'ac16':
        if values.shape[-1] > 16: raise ValueError('AC model exceeds 16 independent circuits')
        return np.rint(values*255).astype('u1')
    if mode == 'pixel':
        rgb = np.asarray(colors if colors is not None else (255,255,255),dtype=np.float32)
        return np.rint(values[...,None]*rgb).clip(0,255).astype('u1')
    raise ValueError('Output mode unresolved; configure the model/controller')
