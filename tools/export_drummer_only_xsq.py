"""Make an isolated real-song XSQ without unrelated template effects or media."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import librosa
from tools.render_drummer_v3_preview import parse_effects

PREFIX='HX_SNOWMAN_DRUMMER_V3_'

def export(source,output,audio):
    tree=ET.parse(source);root=tree.getroot();container=root.find('ElementEffects')
    if container is None:raise ValueError('No ElementEffects in integrated sequence')
    before=parse_effects(source)
    for element in list(container):
        if not element.get('name','').startswith(PREFIX):container.remove(element)
    display=root.find('DisplayElements')
    if display is None:display=ET.SubElement(root,'DisplayElements')
    display.clear()
    for element in container:
        visible=any(layer.get('visible','1')=='1' for layer in element.findall('EffectLayer'))
        ET.SubElement(display,'Element',{'type':'model','name':element.get('name'),
                      'visible':'1' if visible else '0','collapsed':'0','views':'Master View','active':'0'})
    head=root.find('head')
    if head is None:head=ET.SubElement(root,'head')
    duration=float(librosa.get_duration(path=audio))
    for tag,value in [('mediaFile',Path(audio).name),('sequenceDuration',f'{duration:.3f}'),('sequenceType','Media'),('song',Path(audio).stem)]:
        node=head.find(tag)
        if node is None:node=ET.SubElement(head,tag)
        node.text=value
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(tree,space='  ');tree.write(output,encoding='utf-8',xml_declaration=True)
    assert parse_effects(output)==before,'Isolated export changed physical performance'
    assert all(e.get('name','').startswith(PREFIX) for e in container)
    print(f'Isolated drummer XSQ: {output}; {len(before)} hits; duration {duration:.3f}s; media {Path(audio).name}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--audio',type=Path,required=True);a=p.parse_args();export(a.source,a.output,a.audio)
