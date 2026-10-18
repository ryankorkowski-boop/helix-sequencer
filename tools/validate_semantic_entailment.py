"""Actual contextual-model fixtures; no claim of independent lyric calibration."""
import json
from pathlib import Path
from core.lyric_evidence import build_timeline
from core.semantic_story import interpret
from core.semantic_nli import LocalEntailment,enrich

CASES=[
    dict(name='literal_winter',focus='Snow is falling and frost covers the windows.',concept='winter',expected=True),
    dict(name='negated_winter',focus='There is no snow or ice. The weather is warm and sunny.',concept='winter',expected=False),
    dict(name='reconciliation',focus='After years apart, we forgave each other and reunited.',concept='resolution',expected=True),
    dict(name='not_lonely',focus='I am not lonely or isolated; my friends are beside me.',concept='separation',expected=False),
    dict(name='figurative_fire',focus='The guitarist was on fire tonight: his solo was brilliant. No flames or physical heat were present.',concept='warmth',expected=False),
    dict(name='ambiguous_metaphor_abstains',focus='With you beside me, the missing pieces of my life finally fit together.',concept='connection',expected=False),
    dict(name='metaphorical_connection_in_context',focus='With you beside me, the missing pieces of my life finally fit together.',
         before='I used to feel lonely and wished for companionship.',
         after='Now I know that I belong with you and we are together.',concept='connection',expected=True),
]
def main():
    model=LocalEntailment();result=[]
    for case in CASES:
        lines=([case['before']] if case.get('before') else [])+[case['focus']]+([case['after']] if case.get('after') else [])
        timeline=build_timeline([dict(text=text,start_ms=i*3000,end_ms=i*3000+2400,
            confidence=.95,timing_level='phrase') for i,text in enumerate(lines)])
        story=enrich(interpret(timeline),model)
        focus=next(p for p in story['phrases'] if p['text']==case['focus'])
        accepted=any(c['name']==case['concept'] for c in focus['concepts'])
        result.append({**case,'accepted':accepted,'passed':accepted==case['expected'],
                       'evidence':focus['semantic_evidence'][case['concept']],
                       'concepts':focus['concepts']})
    payload=dict(schema='helix.semantic_language_fixtures.v2',model=model.identity,
                 cases=result,passed=all(r['passed'] for r in result),
                 limitation='Seven authored English examples, not independent song/metaphor/irony calibration.')
    Path('semantic_language_fixtures.json').write_text(json.dumps(payload,indent=2,allow_nan=False))
    print(json.dumps(payload),flush=True)
    if not payload['passed']:raise SystemExit('Semantic language fixture gate failed')
if __name__=='__main__':main()
