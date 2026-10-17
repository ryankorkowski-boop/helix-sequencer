import hashlib
import json
import struct
import xml.etree.ElementTree as ET

import pytest
import numpy as np

from tools.combine_native_stage import combine


ROLES=('DRUMMER','BASS','GUITAR','PIANO','XYLOPHONE','LEAD','HARMONY')


def write_show(folder, models, *, duration='1.000', sequence_name='Performance.xsq'):
    folder.mkdir();(folder/'media').mkdir()
    (folder/'media/audio.wav').write_bytes(b'same retained source excerpt')
    layout=ET.Element('xrgb');definitions=ET.SubElement(layout,'models')
    groups=ET.SubElement(layout,'modelGroups')
    ET.SubElement(groups,'modelGroup',name='SOURCE_ALL',models=','.join(n for n,_ in models))
    ET.SubElement(layout,'Viewpoints')
    root=ET.Element('xsequence',ModelBlending='true');head=ET.SubElement(root,'head')
    for key,value in dict(sequenceDuration=duration,sequenceTiming='50 ms',mediaFile='media/audio.wav',sequenceType='Media').items():
        ET.SubElement(head,key).text=value
    ET.SubElement(root,'nextid').text=str(len(models)+1)
    ET.SubElement(ET.SubElement(root,'EffectDB'),'Effect').text='E_TEXTCTRL_Eff_On_Start=80,E_TEXTCTRL_Eff_On_End=80'
    ET.SubElement(ET.SubElement(root,'ColorPalettes'),'ColorPalette').text='C_BUTTON_Palette1=#FF0000,C_CHECKBOX_Palette1=1'
    elements=ET.SubElement(root,'ElementEffects');display=ET.SubElement(root,'DisplayElements')
    for i,(name,start) in enumerate(models):
        model=ET.SubElement(definitions,'model',name=name,StartChannel=str(start),DisplayAs='Custom',StringType='RGB Nodes',CustomModel='1',parm1='1',parm2='1',parm3='1',Controller='',LayoutGroup='Default',WorldPosX='0',WorldPosY='0',WorldPosZ='75',ScaleX='1',ScaleY='1',ScaleZ='1')
        ET.SubElement(model,'subModel',name='BODY',layout='horizontal',type='ranges',line0='1')
        ET.SubElement(display,'Element',name=name,type='model')
        layer=ET.SubElement(ET.SubElement(elements,'Element',name=name,type='model'),'EffectLayer')
        ET.SubElement(layer,'Effect',id=str(i+1),name='On',ref='0',palette='0',startTime='0',endTime='1000')
    ET.ElementTree(layout).write(folder/'xlights_rgbeffects.xml')
    ET.ElementTree(root).write(folder/sequence_name)
    (folder/'xlights_networks.xml').write_text('<Networks/>')


def sparse_fseq(folder, *, first=96, count=3, truncate=False):
    header=bytearray(38);header[:4]=b'PSEQ';header[7]=2
    struct.pack_into('<H',header,4,38)
    struct.pack_into('<II',header,10,count,20);header[18]=50;header[22]=1
    header[32:35]=first.to_bytes(3,'little');header[35:38]=count.to_bytes(3,'little')
    payload=bytes([200]*count)*20
    (folder/'Performance.fseq').write_bytes(header+(payload[:-1] if truncate else payload))


@pytest.fixture
def inputs(tmp_path):
    scenery=tmp_path/'scene';band=tmp_path/'band'
    write_show(scenery,[('SCENE',97)])
    write_show(band,[('HX_SNOW_'+role,1+i*3) for i,role in enumerate(ROLES)])
    sparse_fseq(scenery)
    return scenery,band,tmp_path/'combined'


def inventory(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}


def test_sparse_offset_uses_expanded_addresses_and_preserves_inputs(inputs):
    scenery,band,out=inputs;before=inventory(scenery),inventory(band)
    result=combine(scenery,band,out)
    assert result['band_channel_offset']==99  # packed width is only three
    models=ET.parse(out/'xlights_rgbeffects.xml').getroot().findall('models/model')
    assert [(m.get('name'),int(m.get('StartChannel'))) for m in models]==[('SCENE',97)]+[('HX_SNOW_'+r,100+i*3) for i,r in enumerate(ROLES)]
    assert (out/'audio.wav').read_bytes()==(band/'media/audio.wav').read_bytes()
    root=ET.parse(out/'Performance.xsq').getroot()
    assert root.findtext('nextid')=='9'
    assert [e.get('id') for e in root.findall('.//Effect') if e.get('id')]==list(map(str,range(1,9)))
    assert all(e.get('startTime')=='0' and e.get('endTime')=='1000' for e in root.findall('.//Effect') if e.get('id'))
    assert root.findtext('head/sequenceTiming')=='25 ms'
    assert inventory(scenery)==before[0] and inventory(band)==before[1]
    group=ET.parse(out/'xlights_rgbeffects.xml').getroot().find('modelGroups/modelGroup')
    assert group.get('models')=='SCENE'


def test_lowercase_input_remains_supported_without_second_output_alias(inputs):
    scenery,band,out=inputs
    (scenery/'Performance.xsq').rename(scenery/'performance.xsq')
    (scenery/'Performance.fseq').rename(scenery/'performance.fseq')
    combine(scenery,band,out)
    assert (out/'Performance.xsq').is_file() and not (out/'performance.xsq').exists()


def test_compressed_native_geometry_uses_node_ids_not_xyz_as_addresses(inputs):
    scenery,band,out=inputs
    for folder in (scenery,band):
        path=folder/'xlights_rgbeffects.xml';tree=ET.parse(path)
        for model in tree.findall('models/model'):
            model.attrib.pop('CustomModel');model.set('CustomModelCompressed','1,177,265,271')
        tree.write(path)
    result=combine(scenery,band,out)
    assert result['band_channel_offset']==99
    assert len(ET.parse(out/'xlights_rgbeffects.xml').findall('models/model'))==8


def test_current_complete_snowman_stage_is_replaced_without_duplicates(tmp_path):
    scenery=tmp_path/'scene';band=tmp_path/'band';out=tmp_path/'combined'
    old=[('SCENE',1)]+[('HX_SNOW_'+r,100+i*3) for i,r in enumerate(ROLES)]
    write_show(scenery,old);write_show(band,[('HX_SNOW_'+r,1+i*3) for i,r in enumerate(ROLES)])
    result=combine(scenery,band,out)
    models=ET.parse(out/'xlights_rgbeffects.xml').findall('models/model')
    assert len(models)==8 and len({m.get('name') for m in models})==8
    assert result['band_channel_offset']==99
    assert result['removed_legacy_performers']==sorted('HX_SNOW_'+r for r in ROLES)
    assert ET.parse(out/'xlights_rgbeffects.xml').find('modelGroups/modelGroup').get('models')=='SCENE'


def test_nested_groups_do_not_retain_removed_stage_group_references(tmp_path):
    scenery=tmp_path/'scene';band=tmp_path/'band';out=tmp_path/'combined'
    write_show(scenery,[('SCENE',1)]+[('HX_SNOW_'+r,100+i*3) for i,r in enumerate(ROLES)])
    write_show(band,[('HX_SNOW_'+r,1+i*3) for i,r in enumerate(ROLES)])
    path=scenery/'xlights_rgbeffects.xml';tree=ET.parse(path);groups=tree.find('modelGroups')
    ET.SubElement(groups,'modelGroup',name='OUTER',models='SCENE,OLD_STAGE')
    ET.SubElement(groups,'modelGroup',name='OLD_STAGE',models=','.join('HX_SNOW_'+r for r in ROLES));tree.write(path)
    combine(scenery,band,out)
    groups=ET.parse(out/'xlights_rgbeffects.xml').findall('modelGroups/modelGroup')
    assert not any(g.get('name')=='OLD_STAGE' for g in groups)
    assert next(g for g in groups if g.get('name')=='OUTER').get('models')=='SCENE'


def test_conflicting_case_aliases_are_rejected_without_output(inputs):
    scenery,band,out=inputs
    (scenery/'performance.xsq').write_text('<different/>')
    with pytest.raises(ValueError,match='conflicting input aliases'):combine(scenery,band,out)
    assert not out.exists()


def test_truncated_native_source_is_rejected_without_output(inputs):
    scenery,band,out=inputs;sparse_fseq(scenery,truncate=True)
    with pytest.raises(ValueError,match='Truncated FSEQ'):combine(scenery,band,out)
    assert not out.exists()


def test_mismatched_source_duration_is_rejected_without_output(inputs):
    scenery,band,out=inputs
    tree=ET.parse(band/'Performance.xsq');tree.find('head/sequenceDuration').text='1.500';tree.write(band/'Performance.xsq')
    with pytest.raises(ValueError,match='same sequence duration'):combine(scenery,band,out)
    assert not out.exists()


def test_overlapping_band_addresses_are_rejected_without_output(inputs):
    scenery,band,out=inputs
    tree=ET.parse(band/'xlights_rgbeffects.xml');tree.find('models/model[2]').set('StartChannel','2');tree.write(band/'xlights_rgbeffects.xml')
    with pytest.raises(ValueError,match='disjoint native RGB'):combine(scenery,band,out)
    assert not out.exists()


def test_failed_final_write_leaves_no_partial_candidate(inputs,monkeypatch):
    scenery,band,out=inputs;before=inventory(scenery),inventory(band)
    original=ET.ElementTree.write
    def fail_sequence(tree,path,*args,**kwargs):
        if str(path).endswith('Performance.xsq'):raise OSError('simulated output interruption')
        return original(tree,path,*args,**kwargs)
    monkeypatch.setattr(ET.ElementTree,'write',fail_sequence)
    with pytest.raises(OSError,match='output interruption'):combine(scenery,band,out)
    assert not out.exists() and not list(out.parent.glob('.combined-*'))
    assert (inventory(scenery),inventory(band))==before


def test_existing_successful_export_is_not_overwritten(inputs):
    scenery,band,out=inputs;out.mkdir();(out/'approved.mp4').write_bytes(b'previous successful output')
    with pytest.raises(FileExistsError):combine(scenery,band,out)
    assert (out/'approved.mp4').read_bytes()==b'previous successful output'


def test_combined_cues_replace_old_cast_and_preserve_source_clock(tmp_path):
    scenery=tmp_path/'scene';band=tmp_path/'band';out=tmp_path/'combined'
    write_show(scenery,[('SCENE',1)]+[('HX_SNOW_'+r,100+i*3) for i,r in enumerate(ROLES)])
    write_show(band,[('HX_SNOW_'+r,1+i*3) for i,r in enumerate(ROLES)])
    tree=ET.parse(band/'Performance.xsq');tree.find('head/sequenceTiming').text='25 ms';tree.write(band/'Performance.xsq')
    (band/'pose_provenance.json').write_text(json.dumps({'source_pose_frame_ms':50}))
    np.savez(scenery/'expected_cues.npz',**{'SCENE::BODY':np.arange(20),'HX_SNOW_PIANO::BODY':np.full(20,20)})
    np.savez(band/'expected_cues.npz',**{'HX_SNOW_PIANO::BODY':np.full(20,85),'HX_SNOW_PIANO::SOURCE_POSE':np.tile([0,90],10)})
    (scenery/'showcase_manifest.json').write_text('{"models":"old input"}')
    before=inventory(scenery),inventory(band)
    report=combine(scenery,band,out)['expected_cues']
    assert report['complete'] and report['frame_ms']==25 and report['frames']==40
    with np.load(out/'expected_cues.npz') as cues:
        np.testing.assert_array_equal(cues['SCENE::BODY'],np.repeat(np.arange(20),2))
        np.testing.assert_array_equal(cues['HX_SNOW_PIANO::BODY'],np.full(40,85))
        np.testing.assert_array_equal(cues['HX_SNOW_PIANO::SOURCE_POSE'],np.repeat(np.tile([0,90],10),2))
    assert not (out/'showcase_manifest.json').exists()
    assert (out/'source_metadata/scenery/showcase_manifest.json').read_bytes()==(scenery/'showcase_manifest.json').read_bytes()
    assert (inventory(scenery),inventory(band))==before


def test_partial_input_cue_evidence_is_archived_without_false_complete_output(inputs):
    scenery,band,out=inputs
    np.savez(scenery/'expected_cues.npz',**{'SCENE::BODY':np.ones(20)})
    result=combine(scenery,band,out)
    assert not result['expected_cues']['complete']
    assert not (out/'expected_cues.npz').exists()
    assert (out/'source_metadata/scenery/expected_cues.npz').is_file()


@pytest.mark.parametrize('values',[np.ones(21),np.full(20,np.nan),np.full(20,101)])
def test_invalid_cue_evidence_leaves_no_partial_candidate(inputs,values):
    scenery,band,out=inputs
    np.savez(scenery/'expected_cues.npz',**{'SCENE::BODY':values})
    np.savez(band/'expected_cues.npz',**{'HX_SNOW_PIANO::BODY':np.ones(20)})
    before=inventory(scenery),inventory(band)
    with pytest.raises(ValueError,match='Invalid source cue'):combine(scenery,band,out)
    assert not out.exists() and not list(out.parent.glob('.combined-*'))
    assert (inventory(scenery),inventory(band))==before
