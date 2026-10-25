"""Native surface export of FinalBandScene, with the preserved source drummer.

The drummer is the original planar source-art node model used by FinalBandScene's
compositor. Other characters sample the retained solid meshes and material light
at bounded spacing; the legacy sparse exporter remains available. Neither is described as
continuous mesh animation or as owner-approved native visual output.
"""
from models.final_band_native import add_final_native_band

ROLES = ('drummer', 'bass', 'guitar', 'piano', 'lead', 'harmony')
VISEMES = {'AI': 'AH', 'E': 'EE', 'FV': 'FV', 'L': 'L', 'MBP': 'MBP',
           'O': 'OH', 'U': 'OH', 'WQ': 'OH', 'etc': 'EE', 'rest': 'REST'}


def add_band(garden, prefix='HX_SNOW', position=(0, 0, 0)):
    before = len(garden.models)
    add_final_native_band(garden, prefix, position, include_stage=False, mouth_scale=.42, surface_spacing=.08)
    models = garden.models[before:]
    if len(models) != 6 or {m.details['final_band_role'] for m in models} != set(ROLES):
        raise ValueError('Canonical native export requires exactly six performers')
    for model in models:
        model.attrs.pop('StartChannel', None)
        role = model.details['final_band_role']
        model.details.update(review_role=role, geometry_source='models.final_band_scene.FinalBandScene',
                             owner_approved_native_visuals=False)
        model.attrs.update(PixelSize='6', Antialias='1', BlackTransparency='100',
                           HelixOutputMode='pixel')
        if role == 'drummer':
            # xLights draws CustomBkgImage in the exported House Preview,
            # including the source editor's gray rectangle. Keep the exact
            # authored reference portable without compositing it over pixels.
            model.attrs['HelixReferenceImage'] = model.attrs.pop('CustomBkgImage')
            # Preserve every source range and add semantic aliases, never
            # replace source contact/shoulder/pedal pixels with a new drummer.
            model.submodels['BASE_DIM'] = list(model.submodels['BODY_KEEPALIVE'])
            from PIL import Image
            import numpy as np
            from models.approved_concepts import ROOT
            pixels = np.asarray(Image.open(ROOT/'fixtures/band_geometry/source/drummer_idle.png').convert('RGB').resize((96,72),Image.Resampling.BOX)).reshape(-1,3)
            model.colors = ['#'+''.join(f'{int(c):02X}' for c in pixel) for pixel in pixels]
            # Use the retained masked idle ranges; source margins/axes are excluded.
            model.submodels['BASE_DIM'] = list(model.submodels['BODY_KEEPALIVE'])
            for target in ('KICK', 'SNARE_LEFT', 'SNARE_RIGHT', 'TOM_HIGH', 'TOM_MID',
                           'TOM_FLOOR', 'HI_HAT', 'CYMBAL_LEFT', 'CYMBAL_RIGHT'):
                key = 'HX_SNOWMAN_DRUMMER_V3_' + target
                if key not in model.submodels:
                    key = 'HX_SNOWMAN_DRUMMER_V3_SNARE' if target.startswith('SNARE_') else key
                if key not in model.submodels:
                    raise ValueError('Missing source drummer component: ' + key)
                model.submodels[target] = list(model.submodels[key])
            model.details['native_limitation'] = 'Preserved planar source-art drummer; not a newly sculpted drummer'
        if role in ('lead', 'harmony'):
            original = dict(model.submodels)
            for name in list(model.submodels):
                if name.startswith('MOUTH_'):
                    del model.submodels[name]
            for viseme, shape in VISEMES.items():
                model.submodels['MOUTH_' + viseme] = list(original['MOUTH_' + shape])
            model.children.append(('faceInfo', dict(Name='Helix independent phonemes', Type='NodeRange',
                **{'Mouth-' + v: ','.join(map(str, model.submodels['MOUTH_' + v])) for v in VISEMES},
                **{'Eyes-Open': '', 'Eyes-Closed': '', 'FaceOutline': ''})))
            model.attrs['HelixPhonemeOwnership'] = 'exclusive'
            model.details['mouth_scale_relative_to_solid_scene'] = .42
    start = 1
    for model in garden.models:
        model.start = start
        start += model.channels
    return models


def visual_identity():
    return dict(renderer='xlights_house_preview', geometry_source='models.final_band_scene.FinalBandScene',
                canonical_solid_3d_band=False, canonical_surface_geometry=True,
                owner_vocal_animation_review='rejected_timing_reopened_20261023',
                owner_canonical_visual_review='rejected_identity_reopened_20261023',
                limitations=['Native surface samples and stationary light poses are not continuous solid meshes',
                             'Canonical source drummer is planar artwork, as in the solid scene compositor'],
                performer_count=6, optional_xylophonist=False)
