"""Optional local entailment model for contextual lyric interpretation.

No generated lyrics, executable output or remote inference. Every hypothesis is
scored against both its source passage and neighbouring narrative context.
Model probabilities are uncalibrated evidence, not objective emotional truth.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import math
import os

from core.lyric_evidence import probability
from core.semantic_story import MOTION

MODEL = 'cross-encoder/nli-deberta-v3-small'
REVISION = 'fa2804872c3b4bd748f38c0185cc85775361e735'
HYPOTHESES = {
    'winter': 'This passage describes snow, ice, frost, or wintry weather.',
    'warmth': 'This passage describes physical warmth, flames, or a warm shelter.',
    'sky': 'This passage evokes stars or the sky.',
    'travel': 'This passage describes a journey, travelling, or moving toward a destination.',
    'connection': 'This passage expresses love, closeness, belonging, or companionship.',
    'separation': 'This passage expresses loneliness, isolation, loss, or separation.',
    'fear': 'This passage expresses fear, danger, dread, or suspense.',
    'hope': 'This passage expresses hope, discovery, possibility, or a better future.',
    'celebration': 'This passage expresses celebration, joy, success, or triumph.',
    'conflict': 'This passage describes conflict, struggle, opposition, or fighting.',
    'resolution': 'This passage expresses reconciliation, forgiveness, relief, or coming together after difficulty.',
    'positive_emotion': 'The speaker expresses happiness, affection, contentment, or optimism.',
    'negative_emotion': 'The speaker expresses sadness, pain, despair, or grief.',
    'irony': 'The speaker is being ironic or sarcastic rather than literal.',
}


class LocalEntailment:
    def __init__(self, model_name=MODEL, revision=REVISION):
        os.environ['ORT_DISABLE_TELEMETRY'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        torch.set_num_threads(2)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, revision=revision, use_safetensors=True, trust_remote_code=False).eval()
        labels = {str(v).lower():int(k) for k,v in self.model.config.id2label.items()}
        if set(labels) != {'contradiction','entailment','neutral'}:
            raise ValueError('Entailment model must declare its three label indices')
        self.labels = labels
        self.identity = dict(model=model_name, revision=revision, engine='local_pytorch_nli',
                             probability_calibration='not_calibrated_for_song_lyrics',
                             remote_inference=False)

    def score(self, premises, hypotheses):
        result = []
        for offset in range(0,len(premises),8):
            batch = self.tokenizer(premises[offset:offset+8], hypotheses[offset:offset+8],
                padding=True, truncation=True, max_length=384, return_tensors='pt')
            with self.torch.inference_mode():
                values = self.model(**batch).logits.softmax(dim=-1).cpu().tolist()
            result.extend({label:float(row[index]) for label,index in self.labels.items()} for row in values)
        return result


def _valid_score(row):
    if not isinstance(row,dict) or set(row) != {'entailment','contradiction','neutral'}:
        return False
    try:
        values=[float(row[k]) for k in ('entailment','contradiction','neutral')]
        return all(math.isfinite(v) and 0<=v<=1 for v in values) and abs(sum(values)-1)<.02
    except (TypeError,ValueError):
        return False


def enrich(story, scorer):
    out=deepcopy(story)
    phrases=out.get('phrases',[])
    if not phrases:
        out['semantic_backend']=dict(status='no_reliable_lyrics', model_not_loaded=True)
        return out
    keys=list(HYPOTHESES)
    premises,hypotheses=[],[]
    for index,phrase in enumerate(phrases):
        # Explicitly identify the focus. Neighbours supply pronoun/narrative
        # context but cannot independently justify a cue in this passage.
        neighbour=' '.join(p['text'] for p in phrases[max(0,index-1):index+2])
        for text in (phrase['text'], neighbour):
            for key in keys:
                premises.append(text);hypotheses.append(HYPOTHESES[key])
    scores=scorer.score(premises,hypotheses)
    if len(scores)!=len(premises) or not all(_valid_score(s) for s in scores):
        raise ValueError('Malformed entailment probabilities; semantic fallback required')
    motifs={};previous=None;counts=Counter()
    for index,phrase in enumerate(phrases):
        base=index*len(keys)*2
        focus=dict(zip(keys,scores[base:base+len(keys)]))
        context=dict(zip(keys,scores[base+len(keys):base+2*len(keys)]))
        evidence={}
        for key in keys:
            f,c=focus[key],context[key]
            accepted=(f['entailment']>=.55 and c['entailment']>=.80
                      and c['contradiction']<=.10 and c['entailment']-c['neutral']>=.25)
            evidence[key]=dict(focus=f,context=c,accepted=accepted,hypothesis=HYPOTHESES[key])
        ironic=evidence['irony']['accepted']
        concepts=[]
        for key in keys[:11]:
            if evidence[key]['accepted'] and not ironic:
                concepts.append(dict(name=key,confidence=min(phrase['confidence'],.8*context[key]['entailment']),
                                     evidence=[phrase['text']],evidence_kind='contextual_entailment_hypothesis'))
        emotion=phrase['emotion']
        positive=context['positive_emotion']['entailment'] if focus['positive_emotion']['entailment']>=.5 else 0
        negative=context['negative_emotion']['entailment'] if focus['negative_emotion']['entailment']>=.5 else 0
        affect=max(positive,negative)
        if affect>=.70:
            emotion['valence']=round((positive-negative)/max(1,positive+negative),4)
            emotion['confidence']['valence']=round(min(phrase['confidence'],affect*.75),4)
            emotion['provenance']['valence']='contextual_nli_hypothesis'
        if positive>.6 and negative>.6:
            phrase['uncertainty'].append('conflicting_contextual_emotions')
            emotion['confidence']['valence']*=.5
        if ironic:
            phrase['uncertainty'].append('possible_irony_unresolved')
            emotion['confidence']['valence']*=.5
        if not concepts and affect>=.85 and not ironic:
            concepts.append(dict(name='emotional_transition',confidence=min(phrase['confidence'],affect*.8),
                                 evidence=[phrase['text']],evidence_kind='contextual_emotion_hypothesis'))
        valence=emotion['valence']
        recurrences=[]
        for concept in concepts:
            name=concept['name'];counts[name]+=1
            import hashlib
            motif=motifs.setdefault(name,dict(id='motif_'+hashlib.sha256(name.encode()).hexdigest()[:10],occurrences=[]))
            occurrences=motif['occurrences']
            phase='introduce' if not occurrences else 'transform' if abs(valence-occurrences[-1]['valence'])>=.35 else 'return'
            occurrences.append(dict(start_ms=phrase['start_ms'],end_ms=phrase['end_ms'],
                                   valence=valence,phase=phase,phrase_key=phrase['text'].lower()))
            recurrences.append(dict(id=motif['id'],concept=name,occurrence=len(occurrences),phase=phase))
        phrase['concepts']=concepts
        phrase['motifs']=recurrences
        phrase['narrative']=('opening' if previous is None else 'resolution' if previous<-.15 and valence>.15
                             else 'reversal' if previous>.15 and valence<-.15 else 'development')
        if emotion['confidence']['valence']>.3:previous=valence
        phrase['provenance']='contextual_nli_with_focus_and_neighbour_evidence'
        phrase['semantic_evidence']=evidence
        phrase['interpretation_status']='model_hypothesis_requires_review'
    out['motifs']=motifs
    out['global_themes']=dict(counts)
    out['semantic_backend']={**scorer.identity,'status':'inferred','passage_count':len(phrases),
        'focus_entailment_min':.55,'context_entailment_min':.80,
        'context_contradiction_max':.10,'source_words_modified':False}
    out['limitations']=['Contextual NLI is not calibrated on singing, metaphor, humour or irony.',
        'Every meaning/emotion remains a hypothesis; no unknown lyric text is generated.',
        'Neighbouring context is bounded; whole-song motifs and emotional progression retain state.']
    return out


def maybe_enrich(story):
    if not os.environ.get('HELIX_SEMANTIC_NLI'):
        return story
    if not story.get('phrases'):
        return {**story,'semantic_backend':{'status':'no_reliable_lyrics','model_not_loaded':True}}
    try:
        return enrich(story,LocalEntailment())
    except Exception as exc:
        out=deepcopy(story)
        out['semantic_backend']=dict(status='rules_fallback',reason=type(exc).__name__+': '+str(exc)[:240])
        return out
