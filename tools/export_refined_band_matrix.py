"""Portable native xLights Video-on-matrix exports of verified Helix renderings.

This is explicitly a virtual-matrix show, not a claim that stationary physical
prop channels can reproduce continuously articulated meshes. Native Video owns
pixel output; the exact Helix MP4 owns its animation and lighting intention.
"""
from __future__ import annotations
import argparse,json,math,shutil,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from tools.render_refined_helix_band import OUT

MODEL='HX_BAND_REVIEW_MATRIX'


def write_xml(root,path):
    ET.indent(root,space='  ');ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)


def export(movie:Path,output=None,width=384,height=216):
    output=Path(output) if output else OUT/'xlights'/movie.stem;media=output/'media';media.mkdir(parents=True,exist_ok=True)
    target=media/'performance.mp4';shutil.copyfile(movie,target)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-vn','-c:a','pcm_s16le',str(media/'soundtrack.wav')],check=True)
    duration=float(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=duration','-of','csv=p=0',str(movie)]))
    milliseconds=math.ceil(duration*20)*50
    root=ET.Element('xrgb');models=ET.SubElement(root,'models')
    attrs=dict(name=MODEL,DisplayAs='Horiz Matrix',StringType='RGB Nodes',StartChannel='1',Controller='',LayoutGroup='Default',
               StartSide='B',Dir='L',PixelSize='1',Antialias='1',Transparency='0',versionNumber='7',
               parm1=str(height),parm2=str(width),parm3='1',WorldPosX='0',WorldPosY='0',WorldPosZ='0',ScaleX='1',ScaleY='1',ScaleZ='1')
    model=ET.SubElement(models,'model',attrs)
    ET.SubElement(model,'ControllerConnection',{'Protocol':'','Port':'0'})
    for tag in ('modelGroups','view_objects','effects','views','palettes','layoutGroups','perspectives','colors','Viewpoints'):ET.SubElement(root,tag)
    settings=ET.SubElement(root,'settings')
    for name,value in {'backgroundBrightness':'0','storedLayoutGroup':'All Models','LayoutMode3D':'0','Display2DCenter0':'1',
                       'previewWidth':str(width),'previewHeight':str(height)}.items():ET.SubElement(settings,name,{'value':value})
    write_xml(root,output/'xlights_rgbeffects.xml');write_xml(ET.Element('Networks',{'computer':'','GlobalFPPProxy':''}),output/'xlights_networks.xml')
    sequence=ET.Element('xsequence',{'BaseChannel':'1','FixedPointTiming':'1','ModelBlending':'true'})
    head=ET.SubElement(sequence,'head')
    for name,value in dict(version='2026.18',author='Helix',song=movie.stem,sequenceTiming='50 ms',sequenceType='Media',
        sequenceDuration=f'{milliseconds/1000:.3f}',mediaFile='media/soundtrack.wav',
        comment='Helix virtual-matrix review. Native Video displays exact source-event renderer output; separate physical-prop articulation remains unsupported.').items():ET.SubElement(head,name).text=value
    ET.SubElement(sequence,'nextid').text='2'
    palettes=ET.SubElement(sequence,'ColorPalettes');ET.SubElement(palettes,'ColorPalette').text='C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1'
    db=ET.SubElement(sequence,'EffectDB');ET.SubElement(db,'Effect').text='E_FILEPICKERCTRL_Video_Filename=media/performance.mp4,E_CHECKBOX_Video_AspectRatio=1,E_CHOICE_Video_DurationTreatment=Normal,E_TEXTCTRL_Video_Starttime=0,E_CHECKBOX_SynchroniseWithAudio=0,E_SLIDER_Video_Speed=100'
    display=ET.SubElement(sequence,'DisplayElements');ET.SubElement(display,'Element',{'type':'model','name':MODEL,'visible':'1','collapsed':'0'})
    elements=ET.SubElement(sequence,'ElementEffects');element=ET.SubElement(elements,'Element',{'type':'model','name':MODEL})
    layer=ET.SubElement(element,'EffectLayer');ET.SubElement(layer,'Effect',{'name':'Video','ref':'0','palette':'0','startTime':'0','endTime':str(milliseconds),'id':'1'})
    path=output/(movie.stem+'.xsq');write_xml(sequence,path)
    metadata=dict(type='native_xlights_virtual_matrix',physical_performer_prop_export=False,movie=str(movie.name),matrix_pixels=[width,height],channels=width*height*3,
                  timing_ms=50,source_movie_duration=duration,sequence_duration=milliseconds/1000,required_files=['xlights_rgbeffects.xml','xlights_networks.xml',path.name,'media/performance.mp4','media/soundtrack.wav'])
    (output/'EXPORT_SCOPE.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('movie',type=Path);p.add_argument('--output',type=Path);p.add_argument('--width',type=int,default=384);p.add_argument('--height',type=int,default=216)
    a=p.parse_args();print(export(a.movie,a.output,a.width,a.height))
