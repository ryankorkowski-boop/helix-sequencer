"""Build independent native concept shows and encode their actual FSEQ pixels."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from models.approved_concepts import ROOT, CONCEPTS, build_concept, catalog
from tools.build_helpers.ultimate_showcase import write_layout, model_xml, _write_xml
from tools.build_helpers.ultimate_showcase_preview import read_fseq, _font


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sequence(g, output):
    """24s neutral native study, distinct per-sector depth chases and On fades."""
    p=output/(g.slug+'_Showcase.xsq')
    root=ET.parse(p).getroot()
    for tag in ('ColorPalettes','EffectDB','DisplayElements','ElementEffects'):root.find(tag).clear()
    palettes={};settings={};identifier=1
    def effect(layer,color,start,end,b0,b1):
        nonlocal identifier
        if color not in palettes:
            palettes[color]=len(palettes)
            ET.SubElement(root.find('ColorPalettes'),'ColorPalette').text=f'C_BUTTON_Palette1={color},C_CHECKBOX_Palette1=1'
        key=(b0,b1)
        if key not in settings:
            settings[key]=len(settings)
            ET.SubElement(root.find('EffectDB'),'Effect').text=f'E_TEXTCTRL_Eff_On_Start={b0},E_TEXTCTRL_Eff_On_End={b1}'
        ET.SubElement(layer,'Effect',{'name':'On','ref':str(settings[key]),'palette':str(palettes[color]),
                                     'startTime':str(start),'endTime':str(end),'id':str(identifier)})
        identifier+=1
    for i,m in enumerate(g.models):
        ET.SubElement(root.find('DisplayElements'),'Element',{'type':'model','name':m.name,'visible':'1','collapsed':'1'})
        e=ET.SubElement(root.find('ElementEffects'),'Element',{'type':'model','name':m.name})
        base=ET.SubElement(e,'EffectLayer')
        if m.details.get('canonical_drummer'):
            body=ET.SubElement(e,'SubModelEffectLayer',{'name':'BODY_KEEPALIVE','layer':'0'})
            effect(body,'#BECAD3',0,24000,30,30)
            # Exact instrument/actuator helpers, decorative demonstration only.
            targets=('KICK','SNARE','HI_HAT','TOM_HIGH','TOM_MID','TOM_FLOOR','CYMBAL_LEFT','CYMBAL_RIGHT')
            for k,target in enumerate(targets):
                prefix=m.name+'_'+target
                for suffix,color in [('_SURFACE',g.palette[k%3]),('_ARM_STICK_NEUTRAL','#686868'),('_ARM_STICK_WOOD','#855124')]:
                    part=prefix+suffix
                    if part not in m.submodels:continue
                    layer=ET.SubElement(e,'SubModelEffectLayer',{'name':part,'layer':'0'})
                    for start in range(k*800,24000,6400):effect(layer,color,start,min(start+600,24000),90,20)
                if target=='HI_HAT':
                    layer=ET.SubElement(e,'SubModelEffectLayer',{'name':prefix+'_FOOT','layer':'0'})
                    for start in range(k*800,24000,6400):effect(layer,'#DAAD6D',start,min(start+600,24000),32,12)
            continue
        # Disjoint sectors retain model-specific colors; helix strands keep palettes.
        for k in range(8):
            part=f'SECTOR_{k:02}'
            if part not in m.submodels:continue
            layer=ET.SubElement(e,'SubModelEffectLayer',{'name':part,'layer':'0'})
            ids=m.submodels[part];color=m.colors[ids[len(ids)//2]-1]
            effect(layer,color,0,4000,0,60)
            for cycle in range(4):
                start=4000+cycle*4000
                delay=((k+i%8)%8)*350
                effect(layer,color,start,start+delay,20,20) if delay else None
                effect(layer,color,start+delay,start+delay+650,25,100)
                effect(layer,color,start+delay+650,min(start+4000,20000),100,20)
            effect(layer,color,20000,22000,30,95)
            effect(layer,color,22000,24000,95,15)
    root.find('nextid').text=str(identifier)
    root.find('head/comment').text='24-second silent artwork-guided concept lighting study. Stage drummer cues are an instrument demonstration, not song transcription.'
    _write_xml(root,p)
    return p


def export(concept,output):
    g=build_concept(concept)
    manifest=write_layout(g,output)
    # This batch intentionally covers its own structure, not Aurora's 27 families.
    manifest.update({'schema':'helix.approved_concept.v1','name':g.title,'concept_id':concept['id'],
                     'native_families':['Custom'],'native_coverage_complete':False,
                     'source_art':concept['image'],'source_art_side':concept['side'],
                     'build_status':'native planning layout','source_brief':concept,
                     'sequence_type':'24-second silent Animation study','physical_output_networks':0,
                     'limits':[concept['constraint'],'Artwork-guided finite geometry, not a scanned/surveyed reconstruction.',
                               'No complete music sequence or musical drummer acceptance claimed.']})
    for m in g.models:_write_xml(model_xml(m,'custommodel'),output/'models'/(m.name+'.xmodel'))
    if concept['round']=='stage':
        for name in ('drummer_idle.png','drummerbg.png'):
            shutil.copy2(ROOT/'fixtures/band_geometry/source'/name,output/'assets'/name)
    # Human-readable source reference is a copy, never an edit of the original.
    shutil.copy2(CONCEPTS.parent/concept['image'],output/'assets'/'concept_reference.png')
    (output/'media').mkdir(exist_ok=True)
    (output/'media/README.txt').write_text('Silent lighting study; no soundtrack is required. Copy original song media here when authoring a matching music XSQ.\n')
    layout=ET.parse(output/'xlights_rgbeffects.xml')
    points=np.vstack([m.points for m in g.models]);span=np.ptp(points,axis=0)
    distance=-max(240,float(max(span))*1.9)
    for camera in layout.findall('./Viewpoints/*'):
        camera.set('distance',f'{distance:.2f}')
        camera.set('pany',str(-float((points[:,1].max()+points[:,1].min())/2)))
    _write_xml(layout.getroot(),output/'xlights_rgbeffects.xml')
    xsq=sequence(g,output)
    (output/'showcase_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'README.txt').write_text(f'{g.title} — NATIVE CONCEPT SHOW\n\n'
        f'{len(g.models)} independent Custom pixel models; {manifest["rgb_pixels"]} pixels; {manifest["channel_count"]} channels.\n'
        f'Use this folder as an independent xLights show. Open {xsq.name}, Render All, then play.\n'
        'Pinned validation version: xLights 2026.18. The study is 24 seconds, silent, and is not a full-song music sequence.\n'
        'All source artwork, original shows and source drummer files are preserved. No physical output networks.\n'
        'models/ contains every reusable native model; model_inventory.csv lists absolute channel ranges.\n'
        'Editable SECTOR_00–07, structure-specific submodels and zone groups are available for sequencing.\n'
        f'Artwork reference: assets/concept_reference.png ({concept["side"]} panel).\n'
        f'Limit: {concept["constraint"]}\n'
        'The emitted contours are a planning interpretation. Scenic water, people, beams, vehicle bodywork and stonework are not pixel meshes.\n'
        'Stage drummer demonstration does not establish source-song transcription or drummer acceptance.\n')
    return g,xsq,manifest


class ConceptView:
    """Auto-fit exact XML points, with fixed depth projection and native colors."""
    def __init__(self,g,width=960,height=540):
        self.width,self.height=width,height
        p=np.vstack([m.points for m in g.models]);yaw,pitch=np.radians([22,19])
        x=p[:,0]*np.cos(yaw)-p[:,2]*np.sin(yaw)
        z=p[:,0]*np.sin(yaw)+p[:,2]*np.cos(yaw)
        y=p[:,1]*np.cos(pitch)+z*np.sin(pitch)
        scale=min(width*.88/np.ptp(x),height*.72/np.ptp(y))
        sx=np.rint(width/2+(x-(x.min()+x.max())/2)*scale).astype(int)
        sy=np.rint(height*.54-(y-(y.min()+y.max())/2)*scale).astype(int)
        locations=sy*width+sx
        self.order=np.argsort(locations,kind='stable');ordered=locations[self.order]
        self.starts=np.r_[0,np.flatnonzero(np.diff(ordered))+1];self.locations=ordered[self.starts]
        self.indices=(np.arange(len(p))[:,None]*3+np.arange(3))[self.order]
        self.base=Image.new('RGB',(width,height),'#070e1c');d=ImageDraw.Draw(self.base)
        d.text((28,18),g.title,font=_font(26),fill='#EAF5FF')
        d.text((30,52),'NATIVE XLIGHTS  /  24-SECOND CONCEPT LIGHTING STUDY',font=_font(11),fill='#9CBACB')
        footer=f'{len(g.models)} models • {len(p):,} pixels • exact exported geometry • silent preview'
        d.text((30,height-27),footer,font=_font(11),fill='#9CBACB')
        self.g=g

    def frame(self,values):
        merged=np.maximum.reduceat(values[self.indices],self.starts)
        screen=np.zeros((self.height*self.width,3),dtype=np.uint8);screen[self.locations]=merged
        screen=screen.reshape(self.height,self.width,3)
        lights=screen.copy();small=(screen*.55).astype(np.uint8)
        np.maximum(lights[:,1:],small[:,:-1],out=lights[:,1:]);np.maximum(lights[:,:-1],small[:,1:],out=lights[:,:-1])
        np.maximum(lights[1:],small[:-1],out=lights[1:]);np.maximum(lights[:-1],small[1:],out=lights[:-1])
        im=Image.fromarray(lights)
        glow=im.resize((self.width//2,self.height//2),Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(2)).resize(im.size,Image.Resampling.BILINEAR)
        return ImageChops.add(self.base,ImageChops.add(im,glow))


def render_one(args):
    concept,delivery,xlights=args
    output=Path(delivery)/(concept['id']+'_'+concept['name'].replace(' ','_'))
    g,xsq,manifest=export(concept,output)
    with (output/'native_render.log').open('w') as log:
        subprocess.run([xlights,'--headless','-q','-s',str(output),'-od',str(output),str(xsq)],
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
    frames,step=read_fseq(xsq.with_suffix('.fseq'))
    assert frames.shape==(480,manifest['channel_count']) and step==50,(frames.shape,manifest['channel_count'])
    coverage=[]
    for m in g.models:
        values=frames[:,m.start-1:m.start-1+m.channels]
        assert values.max()>0,f'Unlit model {m.name}'
        coverage.append({'model':m.name,'lit':True,'start_channel':m.start,'nodes':len(m.points)})
    view=ConceptView(g);movie=output/(g.slug+'.mp4')
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r','20','-i','-',
             '-c:v','libx264','-preset','veryfast','-crf','21','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i,values in enumerate(frames):
            frame=view.frame(values)
            if i in (100,250,420):frame.save(output/f'preview_{i//20:02}.png')
            proc.stdin.write(frame.tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('MP4 encoding failed')
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    stream=info['streams'][0]
    assert len(info['streams'])==1 and stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert int(stream['nb_frames'])==480 and abs(float(info['format']['duration'])-24)<.001
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True,timeout=90)
    result={'id':concept['id'],'name':g.title,'show_folder':str(output),'xsq':str(xsq),'mp4':str(movie),
            'models':len(g.models),'pixels':manifest['rgb_pixels'],'channels':manifest['channel_count'],
            'native_frames':480,'frame_ms':50,'native_models_lit':coverage,'physical_output_networks':0,
            'video':{'codec':'h264','pixel_format':'yuv420p','duration_s':24,'frames':480,'full_decode':'pass','audio':False},
            'sha256':{'layout':sha(output/'xlights_rgbeffects.xml'),'xsq':sha(xsq),'fseq':sha(xsq.with_suffix('.fseq')),'mp4':sha(movie)},
            'musical_drummer_acceptance':False,'lighting_source':'Actual native xLights FSEQ; exact geometry projection, not GUI recording.'}
    if concept['round']=='stage':
        source=ET.parse(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel').getroot()
        drummer=next(m for m in g.models if m.details.get('canonical_drummer'))
        from tools.render_drummer_v3_preview import _expand_ranges
        assert all(set(drummer.submodels[s.get('name')])==_expand_ranges(s.get('line0')) for s in source.findall('subModels/subModel'))
        result['canonical_drummer']={'all_40_source_submodels_preserved':True,'pixels':6912,'body_keepalive':bool(drummer.submodels['BODY_KEEPALIVE']),
                                     'source_model_sha256':sha(ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel')}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def save_native_sources(delivery, destination):
    """Compact self-contained source shows; XML embeds every model's geometry."""
    for row in delivery['concepts']:
        source=Path(row['show_folder']);target=destination/source.name
        target.mkdir(parents=True,exist_ok=True)
        files=['xlights_rgbeffects.xml','xlights_networks.xml',Path(row['xsq']).name,
               'showcase_manifest.json','model_inventory.csv']
        for name in files:shutil.copy2(source/name,target/name)
        layout=ET.parse(target/'xlights_rgbeffects.xml')
        for model in layout.findall('./models/model'):
            for key in ('CustomBkgImage','HelixVisualSource'):
                value=model.get(key)
                if value:
                    asset=target/value;asset.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(source/value,asset)
        (target/'README.txt').write_text(
            f'{row["name"]} — SELF-CONTAINED NATIVE SOURCE SHOW\n\n'
            f'Select this folder as an xLights show and open {Path(row["xsq"]).name}.\n'
            'All pixel models/submodels/groups and channel allocations are embedded in xlights_rgbeffects.xml.\n'
            '24-second silent lighting study; not a full-song sequence. No controllers configured.\n'
            'Required runtime assets are copied locally. Separate model exports, reference art and previews can be regenerated.\n'
            'See docs/APPROVED_CONCEPT_NATIVE_SHOWS.md and MASTER_TODO.md in the repository.\n')


def preserved_hashes():
    selected=json.loads((ROOT/'showcase/favorites/selected_layouts.json').read_text())
    hashes={f['path']:f['sha256'] for favorite in selected['favorites'] for f in favorite['files']}
    assert all(sha(ROOT/p)==v for p,v in hashes.items()),'Saved favorite differs from pinned original'
    paths=[CONCEPTS,*CONCEPTS.parent.glob('images/*.png'),*(ROOT/'showcase/favorites').rglob('*'),
           *(ROOT/'fixtures/band_geometry/source').glob('drummer*.png'),
           ROOT/'fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel',
           *(ROOT/'evidence/showcase_audio').rglob('*.mp3')]
    hashes.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    for recording in json.loads((ROOT/'evidence/showcase_audio/sources.json').read_text()):
        original=ROOT/'evidence/showcase_audio/source'/recording['file']
        assert sha(original)==recording['sha256'],'Source recording differs from pinned original'
    return hashes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--xlights',type=Path,required=True)
    p.add_argument('--ids',nargs='*');p.add_argument('--workers',type=int,default=2)
    p.add_argument('--native-source-root',type=Path,help='Optional separate generated native source directory')
    args=p.parse_args();args.output=args.output.resolve()
    chosen=[c for c in catalog() if not args.ids or c['id'] in args.ids]
    if not chosen:raise ValueError('No matching concepts')
    source_hashes=preserved_hashes()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs=pool.map(render_one,[(c,str(args.output),str(args.xlights.resolve())) for c in chosen])
        results=[]
        for row in jobs:
            results.append(row);print(json.dumps({k:row[k] for k in ('id','name','models','pixels','mp4')}),flush=True)
    assert all(sha(ROOT/p)==v for p,v in source_hashes.items()),'Preserved source changed'
    result={'schema':'helix.approved_concepts_delivery.v1','concepts':results,'preserved_source_hashes':source_hashes,
            'unresolved':['Whale artwork/name is absent from the saved 22-concept catalog and workspace.'],
            'sample_type':'24-second silent native lighting studies; not full-song music sequences.'}
    (args.output/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    if args.native_source_root:save_native_sources(result,args.native_source_root)
    print(f'Complete: {len(results)} native shows and direct MP4s',flush=True)


if __name__=='__main__':main()
