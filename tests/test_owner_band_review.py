import numpy as np
import pytest
from tools.render_owner_band_review import active_cues, drum_hits, fixed_camera
from tools.assemble_beta_review import encode_nine_comparison


def test_half_open_source_rest_and_new_attack():
    cues=[dict(start_ms=50,end_ms=100,kind='note'),dict(start_ms=200,end_ms=250,kind='note')]
    assert not active_cues(cues,100)
    assert not active_cues(cues,199.99)
    assert active_cues(cues,200)==[cues[1]]


def test_snare_hands_do_not_depend_on_interleaved_hat_or_kick():
    source=[dict(start_ms=i*100,end_ms=i*100+50,kind=k,velocity=.7)
            for i,k in enumerate(('snare','hihat','kick','snare','cymbal','snare'))]
    hits,unresolved=drum_hits(source)
    snares=[h for h in hits if h['target'].endswith('_SNARE')]
    assert [h['side'] for h in snares]==['left','right','left']
    assert [h['time'] for h in snares]==[0,.3,.5]
    assert unresolved==[]


def test_front_camera_stays_fixed_for_whole_sampler():
    a,eye=fixed_camera(1920,1080,0)
    b,other=fixed_camera(1920,1080,119.95)
    np.testing.assert_array_equal(a,b)
    np.testing.assert_array_equal(eye,other)
    assert eye[0]==0


def test_detected_tom_identity_survives_and_unknown_toms_are_reported():
    cues=[dict(start_ms=123+i*200,end_ms=200+i*200,kind='tom',velocity=.8,confidence=.9,
               frequency_band_info={'tom_class':kind,'tom_class_confidence':.9})
          for i,kind in enumerate(('high','mid','floor',None))]
    hits,unresolved=drum_hits(cues)
    assert [h['target'].rsplit('_V3_',1)[1] for h in hits]==['TOM_HIGH','TOM_MID','TOM_FLOOR']
    assert [h['time'] for h in hits]==[.123,.323,.523]
    assert unresolved==[{'start_ms':723,'kind':'tom'}]


def test_nine_grid_rejects_repeated_footage_before_encoding(tmp_path):
    item={'sources':[{'video_sha256':'same'} for _ in range(9)]}
    with pytest.raises(ValueError,match='Nine distinct'):
        encode_nine_comparison(item,tmp_path/'grid.mp4',120,'encoder')


def test_nine_grid_keeps_each_native_panel_in_its_own_cell(tmp_path):
    import subprocess
    import wave
    from tools.assemble_beta_review import assemble
    from tools.phoneme_source import digest
    colors=['red','lime','blue','yellow','cyan','magenta','orange','white','purple']
    sources=[]
    for i,color in enumerate(colors):
        movie=tmp_path/f'layout{i}.mp4'
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'color={color}:s=160x90:r=20',
            '-t','0.2','-c:v','libx264','-threads','1',str(movie)],check=True)
        sources.append(dict(video=str(movie),video_sha256=digest(movie),gamma=1,title=f'Layout {i+1}'))
    audio=tmp_path/'source.wav'
    with wave.open(str(audio),'wb') as w:
        w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(np.zeros(3200,'<i2').tobytes())
    item=dict(filename='grid.mp4',duration=.2,kind='nine_comparison',sources=sources,
              audio=str(audio),audio_sha256=digest(audio))
    report=assemble(dict(source_commit='fixture',limitations=['test'],movies=[item]),tmp_path/'movies')[0]
    assert report['decode_verified']
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(tmp_path/'movies/grid.mp4'),
        '-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
    image=np.frombuffer(raw,'u1').reshape(1080,1920,3)
    centers=[image[(i//3)*360+180,(i%3)*640+320].astype(int) for i in range(9)]
    assert len({tuple(c) for c in centers})==9
    assert centers[0][0]>200 and centers[0][1]<30
    assert centers[1][1]>200 and centers[1][0]<30
    assert centers[2][2]>200 and centers[2][0]<30
