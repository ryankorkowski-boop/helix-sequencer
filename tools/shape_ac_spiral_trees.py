"""Shape the existing three-circuit line trees in a separate native layout copy."""
from pathlib import Path
import argparse
import copy
import json
import math
import re
import numpy as np
import xml.etree.ElementTree as ET

from models.ultimate_showcase import Garden
from tools.build_helpers.ultimate_showcase import model_xml


def build(source, target, *, turns=4):
    source,target=Path(source).resolve(),Path(target).resolve()
    if source==target:raise ValueError('The original256 layout must remain untouched')
    if not math.isfinite(turns) or turns<=0:raise ValueError('Positive spiral turns required')
    tree=ET.parse(source);root=tree.getroot();models=root.find('models');groups={}
    for element in models:
        match=re.fullmatch(r'Line Tree (Red|Green|White) (\d+)',element.get('name',''))
        if match:groups.setdefault(int(match[2]),{})[match[1]]=element
    if not groups or any(set(g)!={'Red','Green','White'} for g in groups.values()):
        raise ValueError('Each source spiral tree needs its actual three colored circuits')
    report=[]
    for number,group in sorted(groups.items()):
        center=np.mean([[float(m.get('WorldPos'+a,0))+(float(m.get(a+'2',0))/2 if a=='X' else 0)
                         for a in 'XZ'] for m in group.values()],axis=0)
        base=np.mean([float(m.get('WorldPosY',0))+float(m.get('Y2',0)) for m in group.values()])
        height=max(abs(float(m.get('Y2',0))) for m in group.values())
        if height<=0:raise ValueError('Source tree has no measurable height')
        for index,color in enumerate(('Red','Green','White')):
            old=group[color];count=int(old.get('parm2','50'));t=np.linspace(0,1,count)
            radius=height*.20*(1-t);angle=t*math.tau*turns+index*math.tau/3
            points=np.c_[center[0]+radius*np.cos(angle),base+height*t,center[1]+radius*np.sin(angle)]
            g=Garden();m=g.custom(old.get('name'),points,'AC_SPIRAL_TREES',
                'Fixed-color AC spiral; all bulbs share one existing circuit',
                [old.get('CustomColor',{'Red':'#FF0000','Green':'#00FF00','White':'#FFFFFF'}[color])]*count,{'ALL':[1]})
            # Repeated native node1 means one dimmable AC circuit, regardless
            # of bulb count. Each color remains a separate source address.
            entries=m.attrs['CustomModelCompressed'].split(';')
            m.attrs['CustomModelCompressed']=';'.join(','.join(['1']+e.split(',')[1:]) for e in entries)
            m.kind='ac';m.details['circuit_count']=1;m.start=int(old.get('StartChannel'))
            m.attrs.update(StringType=old.get('StringType'),StartChannel=old.get('StartChannel'),
                           PixelSize='4',CustomColor=old.get('CustomColor','#FFFFFF'))
            replacement=model_xml(m)
            for child in old:replacement.append(copy.deepcopy(child))
            position=list(models).index(old);models.remove(old);models.insert(position,replacement)
            report.append(dict(tree=number,color=color,name=m.name,start_channel=old.get('StartChannel'),
                circuits=1,bulbs=count,turns=turns,all_bulbs_share_circuit=True))
    target.parent.mkdir(parents=True,exist_ok=True);tree.write(target,encoding='utf-8',xml_declaration=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('target',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source,a.target),indent=2))
