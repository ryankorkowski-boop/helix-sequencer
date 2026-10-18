"""Recovered unchanged from tools.align_snowman_lyrics; no ML dependencies."""
import re
from core.lyric_phoneme_mapper import map_lyric_to_phonemes

PHONE_MAP={**dict.fromkeys(('AA','AE','AH','AW','AY','ER'),'AH'),
           **dict.fromkeys(('EH','EY','IH','IY'),'EE'),
           **dict.fromkeys(('AO','OW','OY','UH','UW','W'),'OH'),
           **dict.fromkeys(('M','B','P'),'MBP'),**dict.fromkeys(('F','V'),'FV'),'L':'L'}
SYLLABLE_PHONES={'ba':['MBP','AH'],'da':['EE','AH'],'ta':['EE','AH'],
                 'ka':['EE','AH'],'ma':['MBP','AH'],'na':['EE','AH'],'la':['L','AH'],
                 'fo':['FV','OH'],'so':['EE','OH'],'zu':['EE','OH']}


def pronunciation(word, dictionary):
    token=re.sub(r"[^a-z']",'',word.lower())
    candidates=dictionary.get(token)
    if token in SYLLABLE_PHONES:
        shapes=SYLLABLE_PHONES[token];method='nonlexical_sung_syllable_rule'
    elif candidates:
        shapes=[PHONE_MAP.get(re.sub(r'\d','',p),'EE') for p in candidates[0]]
        method='cmu_pronunciation_dictionary'
    else:
        shapes=[s for s in map_lyric_to_phonemes(token) if s!='REST'] or ['AH']
        method='existing_grapheme_fallback'
    compact=[]
    for shape in shapes:
        if not compact or compact[-1]!=shape:compact.append(shape)
    return compact,method

