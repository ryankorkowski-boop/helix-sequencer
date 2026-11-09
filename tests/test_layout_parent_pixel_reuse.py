"""Dense authored submodels must not repeatedly expand the same parent map."""
import xml.etree.ElementTree as ET
from unittest.mock import patch
from core import model_parser as parser


def test_parse_reuses_each_parent_map_without_changing_submodel_geometry(tmp_path):
    root=ET.Element('xrgb');models=ET.SubElement(root,'models')
    for number in range(2):
        model=ET.SubElement(models,'model',name=f'CUSTOM_{number}',DisplayAs='Custom',
            parm1='10',parm2='8',WorldPosX=str(number*20),PointData='0,0,0,8,6,2')
        for index in range(40):
            ET.SubElement(model,'subModel',name=f'MATERIAL_{index}',line0=f'{index+1},{index+2},{index+3}')
    path=tmp_path/'layout.xml';ET.ElementTree(root).write(path)
    original=parser.Model.virtual_pixel_map;calls=[]
    def count(model):
        calls.append(model.name);return original(model)
    with patch.object(parser.Model,'virtual_pixel_map',count):
        actual=parser._parse_layout_uncached(path)
    assert calls==['CUSTOM_0','CUSTOM_1']
    for model_el in models:
        parent=parser._model_from_xml(model_el)
        for sub_el in model_el:
            # Compare every output field against the preceding uncached path.
            expected=parser._build_submodel(parent,sub_el)
            assert actual.models[expected.name]==expected


def test_reuse_does_not_cache_parent_edits_between_calls():
    parent=parser._model_from_xml(ET.fromstring('<model name="P" DisplayAs="Custom" parm1="2" parm2="2" PointData="0,0,0,6,0,0"/>'))
    sub=ET.fromstring('<subModel name="A" line0="1-4"/>')
    before=parser._build_submodel(parent,sub)
    parent.geometry_points=[(10.,0.,0.),(16.,0.,0.)]
    after=parser._build_submodel(parent,sub)
    assert after.geometry_points!=before.geometry_points
    assert after.geometry_points[0]==(10.,0.,0.)
