"""Optional local entailment model for contextual lyric interpretation.

No generated lyrics, executable output or remote inference. Every hypothesis is
scored against both its source passage and neighbouring narrative context.
Model probabilities are uncalibrated evidence, not objective emotional truth.
"""
from __future__ import annotations
from copy import deepcopy
import math
import os

from core.lyric_evidence import probability

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
    # Actual-model validation found unsupported fear/travel hypotheses for
    # ordinary snow/reconciliation text. Keep all NLI output in review metadata.
    # No model probability alone can alter production concepts, emotion or motifs.
    for index,phrase in enumerate(phrases):
        base=index*len(keys)*2
        focus=dict(zip(keys,scores[base:base+len(keys)]))
        context=dict(zip(keys,scores[base+len(keys):base+2*len(keys)]))
        evidence={}
        candidates=[]
        for key in keys:
            f,c=focus[key],context[key]
            proposed=(f['entailment']>=.55 and c['entailment']>=.80
                      and c['contradiction']<=.10 and c['entailment']-c['neutral']>=.25)
            evidence[key]=dict(focus=f,context=c,accepted=False,proposed=proposed,
                blocked_reason='uncalibrated_model_requires_independent_review',
                hypothesis=HYPOTHESES[key])
            if proposed:
                candidates.append(dict(name=key,confidence=min(phrase['confidence'],.8*c['entailment']),
                    evidence=[phrase['text']],evidence_kind='unreviewed_contextual_hypothesis'))
        phrase['semantic_candidates']=candidates
        phrase['semantic_evidence']=evidence
        phrase['interpretation_status']='rules_preserved_model_candidates_quarantined'
    out['semantic_backend']={**scorer.identity,'status':'review_only','passage_count':len(phrases),
        'focus_entailment_min':.55,'context_entailment_min':.80,
        'context_contradiction_max':.10,'source_words_modified':False,
        'production_direction_modified':False,
        'reason':'Actual-model fixtures exposed unsupported fear/travel and missed contextual metaphor.'}
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
