"""Dim native house facade for residential preview context; zero light channels."""
from pathlib import Path
import xml.etree.ElementTree as ET


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
