"""Place the existing concept sculptures around the panel 16 performance stage."""
from models import advanced_concepts
from models.approved_concepts import Structures, abstract
from models.showcase_flavors import _move
from models.ultimate_showcase import Garden


# Each target places the named source origin in the finale's world coordinates.
# Limit each selection to its signature silhouette; companion scenery already
# exists in the finale. Separate high, middle and ground-level sight lines.
# ID, group, source zones, origin, target, uniform scale, source lane, travel axis
PLACEMENTS = (
    (38, 'PHOENIX', (), (0, 0, 0), (0, 80, -74), .50, 'guitarist', 'y'),
    (27, 'WHALE', ('WHALE',), (0, 65, 0), (-105, 120, -52), .47, 'bassist', 'x'),
    (28, 'MANTA', ('MANTA',), (0, 70, 0), (108, 111, -52), .42, 'keyboardist', 'x'),
    (26, 'TESSERACT', (), (0, 80, 0), (-172, 59, -31), .31, 'bassist', 'z'),
    (36, 'ATLAS', (), (0, 80, 0), (172, 63, -31), .39, 'keyboardist', 'y'),
    (7, 'MOIRE', ('LATTICES', 'RINGS'), (0, 0, 0), (-169, 1, 6), .33, 'keyboardist', 'x'),
    (34, 'CRYSTAL', (), (0, 0, 0), (169, 1, 6), .32, 'guitarist', 'y'),
    (39, 'CATHEDRAL', ('NAVE',), (0, 0, 0), (0, 35, -38), .33, 'bassist', 'z'),
)


def add_concept_gallery(garden):
    for number, group, zones, origin, target, scale, role, axis in PLACEMENTS:
        source = Garden(palette=garden.palette)
        structures = Structures(source)
        if number == 7:
            abstract(structures, number)
        else:
            advanced_concepts.build(structures, number)
        for model in source.models:
            if zones and model.zone not in zones:
                continue
            _move(model, origin, target, scale)
            model.name = f'FINALE_{group}_{model.name}'
            model.zone = f'{group}_{model.zone}'
            model.details.update(showcase_group=group, musical_role=role,
                                 spatial_axis=axis, advanced_showcase_clock=True,
                                 spatial_direction=-1 if target[0] < 0 else 1,
                                 source_display_floor=.20)
            garden.models.append(model)
