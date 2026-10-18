from copy import deepcopy
from types import SimpleNamespace as NS
import numpy as np
import pytest
from core.lyric_evidence import build_timeline
from core.semantic_story import interpret, direct
from core.semantic_nli import HYPOTHESES, enrich, maybe_enrich


def story(text='At last you fill the empty space beside me'):
    return interpret(build_timeline([dict(text=text,start_ms=100,end_ms=2400,
        confidence=.95,timing_level='phrase')]))


class Scorer:
    identity={'model':'labeled_test_double','revision':'fixture','remote_inference':False}
    def __init__(self, enabled=('connection',), focus=True):
        self.enabled,self.focus=enabled,focus
    def score(self,premises,hypotheses):
        result=[]
        width=len(HYPOTHESES)
        for index,hypothesis in enumerate(hypotheses):
            key=next(k for k,v in HYPOTHESES.items() if v==hypothesis)
            accepted=key in self.enabled and (self.focus or index%(width*2)>=width)
            result.append(dict(entailment=.94,contradiction=.02,neutral=.04) if accepted else
                          dict(entailment=.03,contradiction=.07,neutral=.90))
        return result


def test_uncalibrated_contextual_hypothesis_is_quarantined_without_literal_evidence():
    source=story()
    assert not source['phrases'][0]['concepts']
    result=enrich(source,Scorer())
    assert not result['phrases'][0]['concepts']
    assert result['phrases'][0]['semantic_candidates'][0]['name']=='connection'
    assert not direct(result)['intents']
    assert result['semantic_backend']['production_direction_modified'] is False


def test_neighbour_alone_cannot_trigger_current_passage_effect():
    result=enrich(story(),Scorer(focus=False))
    assert not result['phrases'][0]['concepts']
    assert not direct(result)['intents']


def test_source_text_and_timing_preserved_and_input_not_mutated():
    source=story();before=deepcopy(source)
    result=enrich(source,Scorer())
    assert source==before
    a,b=source['phrases'][0],result['phrases'][0]
    assert [(a[k],b[k]) for k in ('text','start_ms','end_ms')]==[(a[k],a[k]) for k in ('text','start_ms','end_ms')]
    assert result['semantic_backend']['source_words_modified'] is False


def test_possible_irony_abstains_on_literal_imagery():
    result=enrich(story(),Scorer(enabled=('connection','irony')))
    assert any(c['name']=='irony' for c in result['phrases'][0]['semantic_candidates'])
    assert not direct(result)['intents']


def test_invalid_model_probabilities_rejected():
    class Bad(Scorer):
        def score(self,premises,hypotheses):
            return [dict(entailment=float('nan'),contradiction=0,neutral=0)]*len(premises)
    with pytest.raises(ValueError,match='Malformed'):
        enrich(story(),Bad())


def test_missing_model_preserves_working_rules(monkeypatch):
    import core.semantic_nli as module
    monkeypatch.setenv('HELIX_SEMANTIC_NLI','1')
    def missing():raise ImportError('optional dependency absent')
    monkeypatch.setattr(module,'LocalEntailment',missing)
    source=story('snow falls gently')
    result=maybe_enrich(source)
    assert result['phrases']==source['phrases']
    assert result['semantic_backend']['status']=='rules_fallback'


def test_instrumental_never_loads_language_model(monkeypatch):
    import core.semantic_nli as module
    monkeypatch.setenv('HELIX_SEMANTIC_NLI','1')
    monkeypatch.setattr(module,'LocalEntailment',lambda:pytest.fail('No model needed for instrumental music'))
    assert maybe_enrich({'phrases':[]})['semantic_backend']['status']=='no_reliable_lyrics'


def test_unknown_labels_or_incomplete_model_output_fail_closed():
    class Bad(Scorer):
        def score(self,premises,hypotheses):return []
    with pytest.raises(ValueError):
        enrich(story(),Bad())


def test_pitch_normalization_has_linear_scan_budget_and_preserves_known_events(monkeypatch):
    import core.audio_intelligence as audio
    mags=np.array([[1,.8,.9,.7,.85],[.1,.1,.1,.1,.1],[0,0,0,0,0]],dtype=float)
    hz=np.array([[261.625565,261.625565,329.627557,329.627557,261.625565],[0,0,0,0,0],[0,0,0,0,0]])
    calls=[]
    class ArrayOps:
        def __getattr__(self,name):return getattr(np,name)
        def max(self,values,*args,**kwargs):
            if values is mags:calls.append(values.shape)
            return np.max(values,*args,**kwargs)
    library=NS(effects=NS(hpss=lambda y:(y,y)),stft=lambda *a,**k:mags,
        piptrack=lambda **k:(hz,mags),
        frames_to_time=lambda *a,**k:np.array([0,.05,.10,.25,.30]),
        hz_to_midi=lambda x:69+12*np.log2(x/440))
    monkeypatch.setattr(audio,'np',ArrayOps());monkeypatch.setattr(audio,'librosa',library)
    notes,raw=audio._extract_note_candidates(np.zeros(100),16000,source_stem='fixture',
        config=NS(pitch_confidence_min=.18,smoothing_window_ms=180))
    assert calls==[(3,5)]
    assert sorted((n.timestamp_ms,n.duration_ms,n.midi_note) for n in notes)==[(0,130,60),(100,230,64),(300,80,60)]
    assert [r['midi_note'] for r in raw]==[60,60,64,64,60]


def test_actual_observed_spurious_model_hypotheses_cannot_change_production_direction():
    source=story('Snow is falling and frost covers the windows.')
    original=direct(source)
    result=enrich(source,Scorer(enabled=('winter','fear','travel','negative_emotion')))
    assert {'fear','travel'} <= {c['name'] for c in result['phrases'][0]['semantic_candidates']}
    assert direct(result)==original
    assert result['phrases'][0]['emotion']==source['phrases'][0]['emotion']
    assert result['motifs']==source['motifs']
    assert all(not e['accepted'] for e in result['phrases'][0]['semantic_evidence'].values())
