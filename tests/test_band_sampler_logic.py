import numpy as np

from models.band_sampler_logic import bass_neck_height, cast_duet, held_bass_heights, SHAPE_NAMES
from tools.analyze_band_samplers import acoustic_vowels, mallet_cues


def test_bass_absolute_pitch_never_reverses_at_string_changes():
    heights=np.array([bass_neck_height(n) for n in range(28,65)])
    assert np.all(np.diff(heights)<0)
    assert bass_neck_height(28)==3.08 and abs(bass_neck_height(64)-1.78)<1e-6
    # Crossing the old open-string boundary must still move down for higher pitch.
    assert bass_neck_height(33)>bass_neck_height(39)>bass_neck_height(43)
    notes=np.array([[28],[-1],[40],[64],[-1]])
    actual=held_bass_heights(notes,np.ones(5))
    assert actual[1]==actual[0] and actual[4]==actual[3]


def test_duet_shares_refrains_and_alternates_other_phrases_without_silent_singing():
    mouths=np.full(100,SHAPE_NAMES.index('AH'),dtype=np.int8);mouths[70:80]=0
    lines=[dict(start_ms=i*1000,end_ms=(i+1)*1000,text=t) for i,t in enumerate(
        ['first verse','second verse','third verse','Who knew?','Who knew?'])]
    lanes,casting=cast_duet(mouths,lines)
    assert lanes[1,0] and not lanes[1,1]
    assert lanes[45,1] and not lanes[45,0]
    assert lanes[65,0] and lanes[65,1]
    assert not lanes[75].any()
    assert casting[3]['reason']=='shared refrain'


def test_wordless_vowel_gap_recovery_and_quiet_recognized_ooh():
    sr=16000;t=np.arange(sr*3)/sr
    tone=sum(np.sin(2*np.pi*hz*t)/j for j,hz in enumerate((180,360,540,720,900),1))*.04
    a=np.zeros_like(tone);a[:sr]=tone[:sr];a[sr+4000:sr*2]=tone[sr+4000:sr*2]
    v={'mouths':[dict(start_ms=0,end_ms=900,phoneme='AH')],
       'words':[dict(word='ooh',start=2.2,end=2.6,probability=.008)]}
    # A silent recognized hallucination cannot make a singer open their mouth.
    shapes,proof,_=acoustic_vowels(a,v,60)
    assert any(e['shape']=='AH' and e['start_ms']>=1000 for e in proof['acoustic_gap_visemes'])
    assert shapes[44:52].max()==0
    a[sr*2+3200:sr*2+9600]=tone[sr*2+3200:sr*2+9600]*.4
    shapes,proof,_=acoustic_vowels(a,v,60)
    assert np.any(shapes[44:52]==SHAPE_NAMES.index('OH'))
    assert proof['sustained_vowel_token_fixes'][0]['original_confidence']==.008


def test_mallet_detector_accepts_ringing_pitch_and_rejects_broadband_and_vocal_leakage():
    sr=16000;n=80;time=np.arange(sr*4)/sr
    tone=np.zeros(sr*4)
    for start in (1,2.5):
        t=np.arange(int(sr*.6))/sr
        bell=.15*np.sin(2*np.pi*880*t)*np.exp(-t*9)
        tone[int(start*sr):int(start*sr)+len(t)]+=bell
    energy,_,notes,proof=mallet_cues(tone,np.zeros_like(tone),n)
    assert proof and energy.max()>.1
    assert np.any(notes==81)
    _,_,_,leak=mallet_cues(tone,tone,n)
    assert not leak
    rng=np.random.default_rng(22);noise=np.zeros_like(tone)
    noise[sr:sr+2000]=rng.normal(0,.1,2000)
    _,_,_,broadband=mallet_cues(noise,np.zeros_like(tone),n)
    assert not broadband


def test_embedded_alignment_rejects_a_long_failed_intro_but_keeps_corroborated_refrain(tmp_path,monkeypatch):
    import json
    import tools.analyze_band_samplers as analyzer
    folder=tmp_path/'analysis'/'01';folder.mkdir(parents=True)
    def w(text,start,end,confidence):return dict(word=text,start=start,end=end,probability=confidence)
    bad={'text':'Lights are bending time is slow','start':0.,'end':45.,
         'words':[w('Lights',0,20,.001),w('slow',20,45,.001)]}
    chorus={'text':'Who knew? Cindy Lou knew.','start':50.,'end':53.,
            'words':[w('Who',50,50.3,.01),w('knew',50.3,50.6,.01),w('Cindy',51,51.3,.20),
                     w('Lou',51.3,51.8,.2),w('knew',51.8,53,.05)]}
    (folder/'embedded_lyrics_aligned.json').write_text(json.dumps({'segments':[bad,chorus]}))
    old={'words':[w("I'm",2,3,.9),w('going',3,4,.9),w('Cindy',51,51.3,.9),w('Lou',51.3,51.8,.9)],
         'lines':[dict(start_ms=2000,end_ms=4000,text="I'm going")],'mouths':[]}
    monkeypatch.setattr(analyzer,'OLD',tmp_path)
    result=analyzer.refine_lyrics({'id':'01'},old)
    assert [s['text'] for s in result['lines']]==['Who knew? Cindy Lou knew.']
    proof=result['lyric_refinement']
    assert len(proof['rejected_reference_segments'])==1 and len(proof['accepted_reference_segments'])==1
    assert result['mouths'] and all(e['start_ms']>=50000 for e in result['mouths'])
