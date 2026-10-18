from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace as NS
import xml.etree.ElementTree as ET

import pytest

from core.lyric_evidence import build_timeline, load_corrections, whisper_events
from core.semantic_story import interpret, direct, fuse
from core.semantic_xsq import append_direction
from core.vocal_timeline import build_lyric_timeline
from core.vocal_emotion import face_expression_for


def phrase(text, start=0, end=2000, confidence=.95):
    return dict(text=text,start_ms=start,end_ms=end,confidence=confidence,timing_level='phrase')


def story(*texts):
    return interpret(build_timeline([phrase(t,i*3000,i*3000+2000) for i,t in enumerate(texts)]))


def test_no_words_or_phonemes_invented_from_instrumental_peaks():
    timeline=build_lyric_timeline([], [0,100,250], evidence_aware=True)
    assert timeline.words==timeline.phoneme_events==timeline.lines==[]
    assert direct(interpret(timeline))['intents']==[]


def test_source_word_boundaries_and_acoustically_supplied_phones_are_exact():
    timeline=build_timeline([dict(text='love',start_ms=121,end_ms=489,confidence=.94,
        phonemes=[dict(phoneme='L',start_ms=121,end_ms=192,confidence=.9,source='labeled_fixture'),
                  dict(phoneme='AH',start_ms=192,end_ms=489,confidence=.88,source='labeled_fixture')])])
    assert [(w.start_ms,w.end_ms) for w in timeline.words]==[(121,489)]
    assert [(p.start_ms,p.end_ms,p.source) for p in timeline.phoneme_events]==[(121,192,'labeled_fixture'),(192,489,'labeled_fixture')]


def test_phrase_timing_does_not_claim_word_or_phone_alignment():
    timeline=build_timeline([phrase('snow falls gently')])
    assert len(timeline.lines)==1
    assert timeline.lines[0].text=='snow falls gently'
    assert timeline.words==timeline.phoneme_events==[]


@pytest.mark.parametrize('invalid', [float('nan'),float('inf'),-1,None])
def test_bad_or_missing_confidence_cannot_trigger_story(invalid):
    timeline=build_timeline([phrase('snow falls gently',confidence=invalid)])
    assert not interpret(timeline)['phrases']


def test_uncertain_transcription_is_explicit_and_never_becomes_lyric_text():
    data={'segments':[dict(start=0,end=1,text='invented love',no_speech_prob=.9,
        words=[dict(word='love',start=0,end=1,probability=.98)])]}
    events=whisper_events(data)
    assert events[0]['text']=='' and not events[0]['intelligible']
    timeline=build_timeline(events)
    assert not timeline.words
    assert timeline.confidence_summary['unintelligible_spans'][0]['start_ms']==0


@pytest.mark.parametrize('segment', [
    dict(avg_logprob=-2),dict(compression_ratio=4),dict(no_speech_prob=.9)])
def test_unreliable_whisper_segments_do_not_drive_lights(segment):
    data=dict(words=[dict(word='snow',start=1,end=2,probability=.99)],**segment)
    assert whisper_events({'segments':[data]})[0]['text']==''


def test_missing_word_probability_is_unknown_not_high_confidence():
    assert not whisper_events({'segments':[dict(words=[dict(word='love',start=0,end=1)])]})[0]['intelligible']


def test_estimated_dictionary_phones_stay_inside_short_source_word():
    timeline=build_timeline([dict(text='beautiful',start_ms=11,end_ms=29,confidence=.95)])
    assert all(11<=p.start_ms<=p.end_ms<=29 for p in timeline.phoneme_events)
    assert all('estimated_within_word' in p.source and p.confidence<=.45 for p in timeline.phoneme_events)


def test_out_of_word_alignment_rejected():
    with pytest.raises(ValueError, match='contained'):
        build_timeline([dict(text='snow',start_ms=100,end_ms=400,confidence=1,
            phonemes=[dict(phoneme='AH',start_ms=0,end_ms=900,confidence=1)])])


def test_user_correction_requires_source_hash_and_explicit_timing(tmp_path):
    audio=tmp_path/'audio.wav';audio.write_bytes(b'source fixture')
    correction=tmp_path/'lyrics.json'
    payload=dict(audio_sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),events=[phrase('snow falls')])
    correction.write_text(json.dumps(payload))
    result=load_corrections(correction,audio)
    assert result[0]['source']=='user_timed_correction'
    assert build_timeline(result).words==[]
    audio.write_bytes(b'different recording')
    with pytest.raises(ValueError,match='different audio'):
        load_corrections(correction,audio)


def test_negation_changes_meaning_and_suppresses_literal_unsupported_cue():
    negative=story('I am alone')['phrases'][0]
    positive=story('I am not alone')['phrases'][0]
    assert positive['emotion']['valence'] > negative['emotion']['valence']
    assert 'separation' not in {c['name'] for c in positive['concepts']}


def test_figurative_fire_does_not_produce_literal_fire_story():
    s=story('a fire burns in my heart')
    assert not s['phrases'][0]['concepts']
    assert 'figurative_warmth' in s['phrases'][0]['uncertainty']
    assert direct(s)['intents']==[]


def test_repeated_image_transforms_with_emotional_context():
    s=story('snow brings pain','snow brings joy','snow brings joy')
    motifs=[p['motifs'][0] for p in s['phrases']]
    assert len({m['id'] for m in motifs})==1
    assert [m['phase'] for m in motifs]==['introduce','transform','return']
    assert s['phrases'][1]['narrative']=='resolution'
    intents=direct(s)['intents']
    assert intents[0]['palette_family']!=intents[1]['palette_family']


def test_mixed_lyric_and_acoustic_mood_retained_as_conflict():
    t=build_timeline([phrase('alone in the cold')])
    s=interpret(t,acoustic_sections=[dict(start_ms=0,end_ms=3000,energy=.9,confidence=.8)])
    assert s['phrases'][0]['emotion']['valence']<0
    assert s['phrases'][0]['emotion']['arousal']==.9
    assert 'lyrical_acoustic_conflict' in s['phrases'][0]['uncertainty']


def test_absent_acoustics_does_not_claim_emotion_certainty():
    emotion=story('snow falls softly')['phrases'][0]['emotion']
    assert emotion['confidence']['arousal']==emotion['confidence']['intensity']==0
    assert emotion['provenance']['arousal']=='unknown'


def test_fused_events_preserve_instrument_timing_without_beat_snap():
    analysis=NS(beat_events=[dict(time_ms=500,confidence=.9)],
        note_events=[dict(timestamp_ms=523,duration_ms=81,confidence=.8,source_stem='guitar')],
        stem_events={'drum_event_streams':{'kick':[dict(time_ms=517,confidence=.8)]}},
        section_events=[],lyric_timeline={})
    fused=fuse(analysis,story('snow falls'))
    note=next(e for e in fused['events'] if e['kind']=='instrument_note')
    drum=next(e for e in fused['events'] if e['kind']=='drum_kick')
    assert (note['start_ms'],note['end_ms'],drum['start_ms'])==(523,604,517)
    assert note['source']=='guitar'


class ScenicModel:
    is_submodel=False
    def is_pixel_model(self): return True
    def is_rgb_capable(self): return True


def sequence():
    root=ET.fromstring('<xsequence><EffectDB><Effect>E_TEXTCTRL_Eff_On_Start=100</Effect></EffectDB><ColorPalettes><ColorPalette>C_BUTTON_Palette1=#ff0000,C_CHECKBOX_Palette1=1</ColorPalette></ColorPalettes><ElementEffects><Element type="model" name="GUITAR"><EffectLayer><Effect name="On" startTime="523" endTime="604" ref="0" palette="0" id="1"/></EffectLayer></Element><Element type="model" name="SKY"><EffectLayer/></Element></ElementEffects></xsequence>')
    return root


def test_native_overlay_preserves_all_original_instrument_subtrees():
    root=sequence();original=ET.tostring(root.find('.//Element[@name="GUITAR"]'))
    report=append_direction(root,direct(story('snow falls gently')),['SKY'],
        parsed_layout=NS(models={'SKY':ScenicModel()}),duration_ms=2000)
    assert report['effects']==1
    assert ET.tostring(root.find('.//Element[@name="GUITAR"]'))==original
    effect=root.findall('.//Element[@name="SKY"]//Effect')[0]
    assert int(effect.get('ref'))<len(root.find('EffectDB'))
    assert int(effect.get('palette'))<len(root.find('ColorPalettes'))


@pytest.mark.parametrize('name',['GUITAR','BASS','SNOWMAN_SINGER','DRUMMER','UNKNOWN'])
def test_semantics_cannot_write_to_performers_or_unknown_targets(name):
    with pytest.raises(ValueError,match='scenic RGB'):
        append_direction(sequence(),direct(story('snow falls')), [name],
            parsed_layout=NS(models={'GUITAR':ScenicModel(),'BASS':ScenicModel()}),duration_ms=2000)


def test_no_lyrics_leaves_sequence_identical():
    root=sequence();before=ET.tostring(root)
    report=append_direction(root,direct(story()),['SKY'],parsed_layout=NS(models={'SKY':ScenicModel()}),duration_ms=2000)
    assert ET.tostring(root)==before and report['effects']==0


def test_low_confidence_delivery_restrains_singer_expression():
    low=face_expression_for('lead_singer',dict(intensity=1,confidence=.1),.5)
    high=face_expression_for('lead_singer',dict(intensity=1,confidence=.9),.5)
    assert low['motion_amplitude']<high['motion_amplitude']<=.65
    assert high['mouth_intensity_scale']<=1.18
