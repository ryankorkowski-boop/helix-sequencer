"""Conservative contextual story interpretation layered over recovered music.

This rule system recognizes supported relationships, negation and recurring
imagery. It abstains on unfamiliar metaphors, irony and unrecognized words;
it is not a general language-understanding model. All outputs are hypotheses.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import re
from typing import Any, Iterable, Mapping

from core.lyric_evidence import number, probability, value
from core import vocal_emotion as ve
from core.choreography_intent import (ChoreographyIntent, ChoreographyTarget,
    IntentLayerRole, MotionVocabulary, PaletteFamily, DominanceStrategy)
from core.intent_graph import IntentGraph
from core.intent_layer_expander import IntentLayerExpander


CONCEPTS = {
    'winter': {'snow', 'snowflakes', 'winter', 'frost', 'blizzard', 'ice'},
    'warmth': {'fire', 'flame', 'flames', 'warmth', 'hearth', 'warm'},
    'sky': {'star', 'stars', 'sky', 'constellation', 'starlight'},
    'travel': {'journey', 'road', 'travel', 'sail', 'walking', 'running'},
    'connection': {'together', 'embrace', 'love', 'hand', 'hands', 'reunited'},
    'separation': {'alone', 'lonely', 'apart', 'abandoned', 'separated'},
    'fear': {'fear', 'afraid', 'terror', 'dread', 'haunted'},
    'hope': {'hope', 'discover', 'discovery', 'tomorrow', 'dawn'},
    'celebration': {'celebrate', 'celebration', 'joy', 'victory', 'triumph'},
    'conflict': {'fight', 'battle', 'war', 'clash', 'struggle'},
    'resolution': {'reconcile', 'forgive', 'peace', 'reunited', 'home'},
}
NEGATION = {"not", "no", "never", "without", "isn't", "don't", "can't", "cannot"}
MOTION = {'winter':'cascade', 'warmth':'pulse', 'sky':'shimmer', 'travel':'chase',
    'connection':'bloom', 'separation':'texture', 'fear':'texture', 'hope':'bloom',
    'celebration':'sweep', 'conflict':'pulse', 'resolution':'bloom'}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace('’', "'"))


def _lexical_state(words: list[str]) -> tuple[float, float, list[str]]:
    score, hits, flags = 0., 0, []
    for index, word in enumerate(words):
        if word in NEGATION:
            continue
        polarity = int(word in ve.POSITIVE_WORDS or word in ve.TRIUMPH_WORDS) - int(word in ve.NEGATIVE_WORDS)
        if not polarity:
            continue
        prefix = words[max(0,index-3):index]
        negated = any(w in NEGATION for w in prefix)
        # "no longer alone" signals release rather than loneliness.
        if negated:
            polarity *= -1; flags.append('negation_scoped')
        score += polarity; hits += 1
    return max(-1.,min(1.,score/max(2,hits))), min(.8, .3 + .12*hits) if hits else 0., flags


def interpret(timeline: Any, *, acoustic_sections: Iterable[Any] = ()) -> dict:
    sections = list(acoustic_sections)
    phrases, motifs, previous = [], {}, None
    for line in timeline.lines:
        text, words = line.text, tokens(line.text)
        confidence = probability(line.confidence)
        if confidence < .65 or len(words) < 2:
            continue
        start, end = round(line.start_time*1000), round(line.end_time*1000)
        section = next((s for s in sections if number(value(s,'start_ms')) <= start < number(value(s,'end_ms'))), None)
        energy = probability(value(section,'energy', value(section,'strength', .5)))
        acoustic_conf = probability(value(section, 'confidence', 0))
        valence, lexical_conf, flags = _lexical_state(words)
        concepts = []
        for concept, vocabulary in CONCEPTS.items():
            indices = [i for i,w in enumerate(words) if w in vocabulary]
            supported = [i for i in indices if not any(w in NEGATION for w in words[max(0,i-3):i])]
            if not supported:
                continue
            # Context disambiguation: literal visuals must not follow an idiom.
            if concept == 'warmth' and set(words) & {'heart','desire','soul','eyes'}:
                flags.append('figurative_warmth'); continue
            if concept == 'resolution' and 'home' in words and set(words) & {'leave','left','leaving'}:
                continue
            if concept == 'connection' and 'hand' in words and 'clock' in words:
                continue
            evidence = sorted({words[i] for i in supported})
            concepts.append(dict(name=concept, confidence=min(confidence, .68 + .05*(len(evidence)-1)), evidence=evidence))
        # Conflicting sentiment is preserved; no claim to detect sarcasm.
        positive = bool(set(words) & ve.POSITIVE_WORDS)
        negative = bool(set(words) & ve.NEGATIVE_WORDS)
        if positive and negative:
            flags.append('mixed_lyrical_signals'); lexical_conf *= .65
        mood_conflict = lexical_conf > .35 and valence < -.15 and energy > .7 and acoustic_conf > .4
        if mood_conflict:
            flags.append('lyrical_acoustic_conflict')
        arousal = energy if acoustic_conf else .5
        tension = probability(value(section, 'tension', 0))
        tension_conf = probability(value(section, 'tension_confidence', 0))
        if any(c['name'] in ('fear','conflict') for c in concepts):
            tension = max(tension, .65); tension_conf = max(tension_conf, confidence*.65)
        emotion = dict(valence=round(valence,4), arousal=round(arousal,4), tension=round(tension,4),
            intensity=round(energy,4), confidence=dict(valence=round(confidence*lexical_conf,4),
                arousal=acoustic_conf, tension=round(tension_conf,4), intensity=acoustic_conf),
            provenance=dict(valence='scoped_lyric_rules', arousal='section_acoustics' if acoustic_conf else 'unknown',
                            tension='supplied_harmonic_or_lyric_evidence', intensity='section_acoustics' if acoustic_conf else 'unknown'))
        phrase_key = ' '.join(words)
        recurrences = []
        for concept in concepts:
            name = concept['name']
            motif = motifs.setdefault(name, dict(id='motif_'+hashlib.sha256(name.encode()).hexdigest()[:10], occurrences=[]))
            earlier = motif['occurrences']
            phase = 'introduce' if not earlier else ('transform' if abs(valence-earlier[-1]['valence']) >= .35 else 'return')
            occurrence = dict(start_ms=start, end_ms=end, valence=valence, phrase_key=phrase_key, phase=phase)
            earlier.append(occurrence)
            recurrences.append(dict(id=motif['id'], concept=name, occurrence=len(earlier), phase=phase))
        narrative = ('opening' if previous is None else 'resolution' if previous < -.15 and valence > .15
                     else 'reversal' if previous > .15 and valence < -.15 else 'development')
        phrases.append(dict(start_ms=start,end_ms=end,text=text,confidence=confidence,concepts=concepts,
            emotion=emotion,narrative=narrative,motifs=recurrences,uncertainty=sorted(set(flags)),
            section=str(value(section,'name',value(section,'section_type','unknown'))),
            provenance='contextual_rules_v1', interpretation_status='hypothesis'))
        if lexical_conf:
            previous = valence
    return dict(schema='helix.semantic_story.v1', phrases=phrases, motifs=motifs,
        limitations=['English contextual rules; unfamiliar metaphors and irony unresolved.',
                     'Valence is subjective; absent acoustic evidence has zero confidence.'])


def direct(story: Mapping[str, Any]) -> dict:
    """Use the recovered intent vocabulary and execution layer, with restraint."""
    graph = IntentGraph()
    for phrase in story.get('phrases', []):
        if not phrase['concepts']:
            continue
        # Maximum one focal concept per phrase; familiar motifs can recur.
        cue = max(phrase['concepts'], key=lambda c:(c['confidence'],c['name']))
        if cue['confidence'] < .65:
            continue
        emotion = phrase['emotion']; valence = emotion['valence']
        intensity = .22 + .3*emotion['intensity']*emotion['confidence']['intensity']
        family = PaletteFamily.CINEMATIC_BLUE_GOLD if valence < 0 else PaletteFamily.WARM_WHITE_GOLD
        motif = next(m for m in phrase['motifs'] if m['concept']==cue['name'])
        density = .18 if cue['name'] in ('separation','fear') else .35
        if motif['phase']=='transform':
            density = min(.5,density+.1)
        graph.add_intent(ChoreographyIntent(start=phrase['start_ms']/1000,
            duration=(phrase['end_ms']-phrase['start_ms'])/1000, section=phrase['section'],
            event_type='semantic_'+cue['name'],style='semantic_story',emotional_energy=emotion['arousal'],
            intensity=intensity,focal_region='scenery',target_families=(ChoreographyTarget.BACKGROUND,),
            dominance_strategy=DominanceStrategy.BACKGROUND_ONLY,
            motion_vocabulary=(MotionVocabulary(MOTION[cue['name']]),),palette_family=family,
            density_budget=density,layer_roles=(IntentLayerRole.MOTION,),source='semantic_story',
            metadata=dict(confidence=cue['confidence'],motif=motif,emotion=emotion,
                          narrative=phrase['narrative'],evidence=cue['evidence'],uncertainty=phrase['uncertainty'])))
    events = IntentLayerExpander().expand_many(graph)
    return dict(schema='helix.semantic_direction.v1',intents=[asdict(i) for i in graph],
        execution=[asdict(e) for e in events], timing_policy='source_times_preserved',
        conflict_policy='instrument accents retain their existing lanes; semantic cues use explicit scenic targets')


def fuse(analysis: Any, story: Mapping[str, Any]) -> dict:
    """One ordered event stream; retains source timestamps and provenance."""
    events = []
    def add(kind, start, end, confidence, source, payload):
        a,b=round(number(start)),round(number(end))
        if a < 0 or b < a:
            raise ValueError('Invalid fused event interval')
        events.append(dict(kind=kind,start_ms=a,end_ms=b,confidence=probability(confidence),source=source,payload=payload))
    for index,beat in enumerate(value(analysis,'beat_events',[]) or []):
        ms=value(beat,'time_ms',0)
        add('beat',ms,ms,value(beat,'confidence',0),'audio_intelligence',
            dict(beat_index=index,bar_index=index//4,bar_position=index%4,meter_assumption='4/4; downbeat phase unverified'))
    for note in value(analysis,'note_events',[]) or []:
        a=value(note,'timestamp_ms',0)
        add('instrument_note',a,a+number(value(note,'duration_ms',0)),value(note,'confidence',0),
            value(note,'source_stem','unknown'),note.to_dict() if hasattr(note,'to_dict') else dict(note))
    stem=value(analysis,'stem_events',{}) or {}
    for instrument, lane in (stem.get('drum_event_streams',{}) or {}).items():
        for hit in lane:
            a=value(hit,'timestamp_ms',value(hit,'time_ms',0))
            add('drum_'+instrument,a,a,value(hit,'confidence',0),value(hit,'source','drum_analysis'),hit.to_dict() if hasattr(hit,'to_dict') else dict(hit))
    for section in value(analysis,'section_events',[]) or []:
        add('section',value(section,'start_ms',0),value(section,'end_ms',0),value(section,'confidence',0),'section_analysis',
            section.to_dict() if hasattr(section,'to_dict') else dict(section))
    for role in stem.get('verified_vocal_role_events', []) or []:
        if value(role, 'independent_source_verified', False):
            add('vocal_role',value(role,'start_ms',0),value(role,'end_ms',0),
                value(role,'confidence',0),value(role,'source','independent_voice_input'),dict(role))
    timeline=value(analysis,'lyric_timeline',{}) or {}
    for word in timeline.get('words',[]):
        a,b=number(word['start_time'])*1000,number(word['end_time'])*1000
        add('lyric_word',a,b,word['confidence'],word.get('source','lyrics'),word)
        for phone in word.get('phonemes',[]):
            add('phoneme',number(phone['start_time'])*1000,number(phone['end_time'])*1000,
                phone['confidence'],phone.get('source','unknown'),phone)
    for phrase in story.get('phrases',[]):
        add('semantic_phrase',phrase['start_ms'],phrase['end_ms'],phrase['confidence'],phrase['provenance'],phrase)
    return dict(schema='helix.synchronized_events.v1',events=sorted(events,key=lambda e:(e['start_ms'],e['kind'])),
                vocal_role_policy='use music.vocal_roles independent-source evidence; mixed bus does not establish harmony')
