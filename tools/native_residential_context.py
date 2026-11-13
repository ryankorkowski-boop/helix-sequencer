"""Dim native house facade for residential preview context; zero light channels."""
from pathlib import Path
import xml.etree.ElementTree as ET


def _showcase_houses(garden):
    by_name = {model.name: model for model in garden.models}
    for name, eave in by_name.items():
        if eave.zone != 'HOUSE' or not name.endswith('_EAVE'):
            continue
        prefix = name.removesuffix('_EAVE')
        roof = by_name.get(prefix + '_ROOF')
        if roof is None:
            continue
        left, right = eave.points[:, 0].min(), eave.points[:, 0].max()
        height = float(eave.points[:, 1].mean())
        peak = max(roof.points, key=lambda point: point[1])
        # The fixture front uses the greater Z. Keep all facade vertices
        # behind even the recessed roof peak, independent of house setback.
        rear = min(float(roof.points[:, 2].min()), float(eave.points[:, 2].min())) - 1
        yield prefix, [
            (left, 0, rear), (right, 0, rear), (right, height, rear), (left, height, rear),
            (min(roof.points[:, 0]), height, rear), (max(roof.points[:, 0]), height, rear),
            (peak[0], peak[1], rear),
        ]


def add_showcase_context(folder, garden):
    folder = Path(folder)
    houses = list(_showcase_houses(garden))
    if not houses:
        return
    assets = folder / 'assets'
    assets.mkdir(exist_ok=True)
    (assets / 'showcase_facade.mtl').write_text(
        'newmtl facade\nKa 0.065 0.075 0.09\nKd 0.065 0.075 0.09\nKs 0 0 0\nd 1\nillum 1\n',
        encoding='utf-8',
    )
    path = folder / 'xlights_rgbeffects.xml'
    tree = ET.parse(path)
    root = tree.getroot()
    objects = root.find('view_objects')
    if objects is None:
        objects = ET.SubElement(root, 'view_objects')
    for index, (prefix, vertices) in enumerate(houses):
        name = f'{prefix} ambient facade'
        asset = f'assets/showcase_facade_{index}.obj'
        vertex_rows = ''.join(f'v {x:.5f} {y:.5f} {z:.5f}\n' for x, y, z in vertices)
        (folder / asset).write_text(
            'mtllib showcase_facade.mtl\nusemtl facade\n' + vertex_rows
            + 'vn 0 0 1\nf 1//1 2//1 3//1\nf 1//1 3//1 4//1\nf 5//1 6//1 7//1\n',
            encoding='utf-8',
        )
        existing = next((item for item in objects if item.get('name') == name), None)
        if existing is None:
            ET.SubElement(objects, 'view_object', name=name, DisplayAs='Mesh',
                          ObjFile=asset, MeshOnly='0', Brightness='100', Active='1',
                          WorldPosX='0', WorldPosY='0', WorldPosZ='0',
                          ScaleX='1', ScaleY='1', ScaleZ='1',
                          RotateX='0', RotateY='0', RotateZ='0', LayoutGroup='Default')
    tree.write(path, encoding='utf-8', xml_declaration=True)


def add_context(folder):
    folder=Path(folder);assets=folder/'assets';assets.mkdir(exist_ok=True)
    (assets/'residential_context.mtl').write_text('newmtl facade\nKa 0.22 0.23 0.25\nKd 0.22 0.23 0.25\nKs 0 0 0\nd 1\nillum 1\n')
    (assets/'residential_context.obj').write_text('mtllib residential_context.mtl\nusemtl facade\n'
        'v -30 0 -14\nv 30 0 -14\nv 30 22 -14\nv -30 22 -14\n'
        'v -33 22 -14\nv 33 22 -14\nv 0 40 -17\n'
        'vn 0 0 1\nf 1//1 2//1 3//1\nf 1//1 3//1 4//1\nf 5//1 6//1 7//1\n')
    path=folder/'xlights_rgbeffects.xml';tree=ET.parse(path);root=tree.getroot()
    objects=root.find('view_objects')
    if objects is None:objects=ET.SubElement(root,'view_objects')
    if not any(n.get('name')=='Residential ambient context' for n in objects):
        ET.SubElement(objects,'view_object',name='Residential ambient context',DisplayAs='Mesh',
            ObjFile='assets/residential_context.obj',MeshOnly='0',Brightness='100',Active='1',
            WorldPosX='0',WorldPosY='0',WorldPosZ='0',ScaleX='1',ScaleY='1',ScaleZ='1',
            RotateX='0',RotateY='0',RotateZ='0',LayoutGroup='Default')
    tree.write(path,encoding='utf-8',xml_declaration=True)
