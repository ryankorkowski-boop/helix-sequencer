"""Exporter and montage regressions: portable bindings and mixed-frame-rate duration."""
from pathlib import Path
import json,subprocess,xml.etree.ElementTree as ET
from tools.export_refined_band_matrix import export,MODEL
import tools.package_refined_band as package


def clip(path,fps,seconds):
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'color=c=blue:s=160x90:r={fps}:d={seconds}',
        '-f','lavfi','-i',f'sine=frequency=440:duration={seconds}','-c:v','libx264','-threads','1','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(path)],check=True)


def test_mixed_frame_rate_montage_keeps_video_and_audio_duration(tmp_path,monkeypatch):
    first=tmp_path/'30fps.mp4';second=tmp_path/'20fps.mp4';clip(first,30,1.2);clip(second,20,1.2)
    monkeypatch.setattr(package,'OUT',tmp_path);result=package.concat([first,second],'montage')
    streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(result)]))['streams']
    video=next(s for s in streams if s['codec_type']=='video');audio=next(s for s in streams if s['codec_type']=='audio')
    assert abs(float(video['duration'])-2.4)<.06
    assert abs(float(video['duration'])-float(audio['duration']))<.10


def test_native_matrix_has_matching_models_portable_media_and_real_video_effect(tmp_path):
    movie=tmp_path/'clip.mp4';clip(movie,20,.3);xsq=export(movie,tmp_path/'show',160,90)
    root=ET.parse(xsq).getroot();layout=ET.parse(xsq.parent/'xlights_rgbeffects.xml').getroot()
    assert layout.find('./models/model').get('name')==MODEL
    assert root.find('./ElementEffects/Element').get('name')==MODEL
    assert root.find('./ElementEffects/Element/EffectLayer/Effect').get('name')=='Video'
    assert root.findtext('./head/sequenceDuration')=='0.300'
    assert (xsq.parent/root.findtext('./head/mediaFile')).exists()
    assert (xsq.parent/'media/performance.mp4').read_bytes()==movie.read_bytes()
    scope=json.loads((xsq.parent/'EXPORT_SCOPE.json').read_text())
    assert not scope['physical_performer_prop_export'] and scope['channels']==160*90*3
