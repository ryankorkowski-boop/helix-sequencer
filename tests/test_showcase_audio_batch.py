"""Regressions for full-song native export, source reuse and channel review."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from core.audio_run_cache import AudioRunCache
from models.showcase_flavors import FLAVORS, build_flavor
from tools.build_helpers.ultimate_showcase_preview import render_frame
from tools.run_showcase_audio_batch import model_routes
from tools.showcase_audio_native import native_music_xsq, prepare_template,native_effect
from tools.showcase_audio_preview import NativeSongView
from tools.package_showcase_audio_batch import verify_soundtracks,package_imports


def test_cache_reuses_analysis_without_leaking_layout_mutations(tmp_path):
    source=tmp_path/'same-name.mp3';source.write_bytes(b'original recording')
    cache=AudioRunCache(hashlib.sha256(source.read_bytes()).hexdigest())
    cache.validate_source(source);cache.validate_configuration((False,''))
    calls=[]
    def analyze():
        calls.append(1)
        return {'energy':np.array([.1,.5,.8]),'section_profiles':[]}
    first=cache.get('multiband',analyze,copy_result=True)
    first['section_profiles'].append('left-side route')
    first['energy'][0]=99
    second=cache.get('multiband',analyze,copy_result=True)
    assert len(calls)==1 and second['section_profiles']==[]
    assert second['energy'][0]==.1 and cache.hits=={'multiband':1}
    source.write_bytes(b'different song, same filename')
    with pytest.raises(ValueError,match='different source'):
        cache.validate_source(source)
    with pytest.raises(ValueError,match='different analysis configuration'):
        cache.validate_configuration((True,'other-provider'))


def test_native_aliases_restore_attack_decay_and_fail_closed_on_unknown_effects():
    name,settings=native_effect('Ramp','')
    assert name=='On' and 'Eff_On_Start=100' in settings and 'Eff_On_End=0' in settings
    explicit='E_TEXTCTRL_Eff_On_Start=25,E_TEXTCTRL_Eff_On_End=80'
    assert native_effect('Ramp',explicit)==('On',explicit)
    assert native_effect('Single Strand','')==('SingleStrand','')
    with pytest.raises(ValueError,match='Unsupported native xLights effect'):
        native_effect('silently dark invented effect','')


@pytest.fixture
def native_inputs(tmp_path):
    g=build_flavor('fire_and_ice');template=prepare_template(g,tmp_path)
    return g,tmp_path,template


def test_music_template_does_not_retain_demo_choreography(native_inputs):
    _,_,template=native_inputs;root=ET.parse(template).getroot()
    effects=root.findall('.//Effect')
    # EffectDB defaults are library entries; the sole scheduled seed is 1ms.
    scheduled=root.findall('ElementEffects/Element/EffectLayer/Effect')+root.findall('ElementEffects/Element/SubModelEffectLayer/Effect')
    assert len(scheduled)==1
    assert scheduled[0].get('startTime')=='0' and scheduled[0].get('endTime')=='1'
    assert scheduled[0].get('name')=='On'
    assert effects


def test_native_export_preserves_late_hits_submodels_and_physical_nodes(native_inputs):
    g,folder,template=native_inputs
    physical_before=[ET.tostring(n) for n in ET.parse(folder/'xlights_rgbeffects.xml').getroot().findall('models/model')]
    raw=ET.parse(template);root=raw.getroot();rows=root.find('ElementEffects');rows.clear()
    dna=next(m for m in g.models if m.details.get('double_helix'))
    control=next(m for m in g.models if m.kind!='pixel')
    timing=ET.SubElement(rows,'Element',{'name':'audible beats','type':'timing'})
    ET.SubElement(ET.SubElement(timing,'EffectLayer'),'Effect',{'startTime':'30000','endTime':'30100','label':'anchor'})
    for name in (dna.name+'/STRAND_B',control.name,'HX_WHOLE_SHOW'):
        row=ET.SubElement(rows,'Element',{'name':name,'type':'model'})
        ET.SubElement(ET.SubElement(row,'EffectLayer'),'Effect',{'name':'On','startTime':'30025','endTime':'30375',
            'settings':'E_TEXTCTRL_Eff_On_Start=82,E_TEXTCTRL_Eff_On_End=12','palette':'legacy inline palette'})
    source=folder/'raw.xsq';raw.write(source);media=folder/'real song.mp3';media.write_bytes(b'fixture')
    output=folder/'full.xsq';report=native_music_xsq(source,output,g,media,48.12)
    native=ET.parse(output).getroot()
    assert native.findtext('head/sequenceType')=='Media'
    assert native.findtext('head/sequenceDuration')=='48.150'
    assert native.findtext('head/mediaFile')=='real song.mp3'
    assert report['source_events_retimed'] is False and report['native_effects']==2
    assert report['skipped']['control_or_unresolved_targets']==1
    elements={n.get('name'):n for n in native.findall('ElementEffects/Element')}
    assert dna.name+'/STRAND_B' not in elements and control.name not in elements
    assert elements['audible beats'].find('EffectLayer/Effect').get('startTime')=='30000'
    layer=elements[dna.name].find('SubModelEffectLayer')
    assert layer.get('name')=='STRAND_B' and layer.get('layer')=='0'
    event=layer.find('Effect')
    assert (event.get('startTime'),event.get('endTime'))==('30025','30375')
    assert dna.colors[dna.submodels['STRAND_B'][0]-1] in native.findall('ColorPalettes/ColorPalette')[int(event.get('palette'))].text
    assert 'Eff_On_Start=82' in native.findall('EffectDB/Effect')[int(event.get('ref'))].text
    layout=ET.parse(folder/'xlights_rgbeffects.xml').getroot()
    assert [ET.tostring(n) for n in layout.findall('models/model')]==physical_before
    whole=next(n for n in layout.findall('modelGroups/modelGroup') if n.get('name')=='HX_WHOLE_SHOW')
    assert control.name not in whole.get('models').split(',')


def test_unrouted_rgb_pair_shares_real_choreography_but_keeps_own_colour(native_inputs):
    g,folder,template=native_inputs;raw=ET.parse(template);rows=raw.getroot().find('ElementEffects');rows.clear()
    west=next(m for m in g.models if 'CANDY_GARDEN_-1' in m.name)
    east=next(m for m in g.models if m.name==west.name.replace('_-1','_1'))
    row=ET.SubElement(rows,'Element',{'name':east.name,'type':'model'})
    ET.SubElement(ET.SubElement(row,'EffectLayer'),'Effect',{'name':'Twinkle','startTime':'31225','endTime':'31775','settings':'E_SLIDER_Twinkle_Count=20'})
    source=folder/'raw.xsq';raw.write(source);output=folder/'native.xsq'
    report=native_music_xsq(source,output,g,folder/'song.mp3',48.12)
    assert report['mirrored_rgb_motifs']==[{'source':east.name,'target':west.name,'effects':1}]
    native=ET.parse(output).getroot();palettes=native.findall('ColorPalettes/ColorPalette')
    for model in (west,east):
        element=next(e for e in native.findall('ElementEffects/Element') if e.get('name')==model.name)
        event=element.find('EffectLayer/Effect')
        assert (event.get('startTime'),event.get('endTime'))==('31225','31775')
        assert model.colors[0] in palettes[int(event.get('palette'))].text
    # An independently sequenced west target must never be replaced.
    row=ET.SubElement(rows,'Element',{'name':west.name,'type':'model'})
    ET.SubElement(ET.SubElement(row,'EffectLayer'),'Effect',{'name':'On','startTime':'40200','endTime':'40500','settings':''})
    raw.write(source);report=native_music_xsq(source,output,g,folder/'song.mp3',48.12)
    assert not report['mirrored_rgb_motifs']


@pytest.mark.parametrize('key',[f.key for f in FLAVORS])
def test_explicit_routes_cover_both_sides_and_only_rgb(key):
    g=build_flavor(key);routes=model_routes(g)
    all_routes=set(n for values in routes.values() for n in values)
    assert all_routes=={m.name for m in g.models if m.kind=='pixel'}
    trees=[m for m in g.models if m.details.get('spiral_tree')]
    assert all(m.name in routes['mega'] for m in trees)
    assert any(m.points[:,0].mean()<0 for m in trees)
    assert any(m.points[:,0].mean()>0 for m in trees)


@pytest.mark.parametrize('key',[f.key for f in FLAVORS])
def test_cached_projection_matches_native_reference_outside_song_footer(key):
    g=build_flavor(key);channels=max(m.start-1+m.channels for m in g.models)
    values=np.random.default_rng(3).integers(0,256,channels,dtype=np.uint8)
    expected=np.asarray(render_frame(g,640,360,yaw=7,pitch=18,native=values))
    actual=np.asarray(NativeSongView(g,'song',640,360).frame(values))
    np.testing.assert_array_equal(actual[:330],expected[:330])


def test_native_view_never_invents_lighting_from_song_time():
    g=build_flavor('crystal_lagoon');channels=max(m.start-1+m.channels for m in g.models)
    view=NativeSongView(g,'song',640,360,halo_scale=2)
    zero=np.zeros(channels,dtype=np.uint8)
    np.testing.assert_array_equal(np.asarray(view.frame(zero)),np.asarray(view.base))
    control=next(m for m in g.models if m.kind!='pixel');zero[control.start-1]=255
    np.testing.assert_array_equal(np.asarray(view.frame(zero)),np.asarray(view.base))


@pytest.mark.skipif(shutil.which('ffmpeg') is None,reason='ffmpeg required for actual soundtrack check')
def test_soundtrack_audit_accepts_original_and_rejects_different_music(tmp_path):
    folder=tmp_path/'show';folder.mkdir();source=folder/'song.mp3';movie=folder/'show.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=330:duration=1','-c:a','libmp3lame',str(source)],check=True)
    def encode(audio):
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=black:s=64x64:r=20:d=1',
            '-i',str(audio),'-c:v','libx264','-threads','1','-c:a','aac','-t','1',str(movie)],check=True)
    row={'folder':'show','xsq':'show.xsq','audio':'song.mp3','audio_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'track':'test','title':'Test song','flavor':'neon_circuit'}
    encode(source);report=verify_soundtracks(tmp_path,{'runs':[row]})
    assert report['all_sources_match'] and report['comparisons'][0]['correlation']>.97
    other=folder/'other.mp3'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=610:duration=1','-c:a','libmp3lame',str(other)],check=True)
    encode(other)
    with pytest.raises(ValueError,match='Soundtrack mismatch'):
        verify_soundtracks(tmp_path,{'runs':[row]})


def test_import_package_keeps_native_assets_media_and_portable_paths(native_inputs):
    import zipfile
    g,folder,template=native_inputs
    media=folder/'song.mp3';media.write_bytes(b'exact uploaded audio')
    native_music_xsq(template,folder/'song.xsq',g,media,48.12)
    (folder/'verification.json').write_text('{}')
    row={'track':'Frostbitten_Fingerboard','title':'Frostbitten Fingerboard','folder':'.','layout':g.title,'xsq':'song.xsq','audio':media.name}
    manifest={'runs':[row],'sources':[{'track':row['track'],'sha256':hashlib.sha256(media.read_bytes()).hexdigest()}]}
    packages=package_imports(folder,manifest)
    with zipfile.ZipFile(folder/packages[row['track']]['file']) as archive:
        assert archive.testzip() is None
        assert archive.read(folder.name+'/song.mp3')==media.read_bytes()
        root=ET.fromstring(archive.read(folder.name+'/song.xsq'))
        assert root.findtext('head/mediaFile')=='song.mp3'
        assert folder.name+'/assets/helix_crest.png' in archive.namelist()
        assert json.loads(archive.read('song_manifest.json'))['layouts'][0]['xsq']=='song.xsq'
