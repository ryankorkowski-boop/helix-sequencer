"""Small authored meaning/negation fixtures; no claim of lyric calibration."""
import json
from pathlib import Path
from core.semantic_nli import LocalEntailment,HYPOTHESES

CASES=[
    ('literal_winter','Snow is falling and frost covers the windows.','winter',True),
    ('negated_winter','There is no snow or ice. The weather is warm and sunny.','winter',False),
    ('reconciliation','After years apart, we forgave each other and reunited.','resolution',True),
    ('not_lonely','I am not lonely or isolated; my friends are beside me.','separation',False),
    ('figurative_fire','The guitarist was on fire tonight: his solo was brilliant. No flames or physical heat were present.','warmth',False),
    ('metaphorical_connection','With you beside me, the missing pieces of my life finally fit together.','connection',True),
]
def main():
    model=LocalEntailment()
    scores=model.score([c[1] for c in CASES],[HYPOTHESES[c[2]] for c in CASES])
    result=[]
    for case,score in zip(CASES,scores):
        accepted=(score['entailment']>=.8 and score['contradiction']<=.1
                  and score['entailment']-score['neutral']>=.25)
        result.append(dict(name=case[0],text=case[1],concept=case[2],expected=case[3],
                           accepted=accepted,passed=accepted==case[3],scores=score))
    payload=dict(schema='helix.semantic_language_fixtures.v1',model=model.identity,
                 cases=result,passed=all(r['passed'] for r in result),
                 limitation='Six authored English examples, not independent song/metaphor/irony calibration.')
    Path('semantic_language_fixtures.json').write_text(json.dumps(payload,indent=2)+'\\n')
    print(json.dumps(payload),flush=True)
    if not payload['passed']:raise SystemExit('Semantic language fixture gate failed')
if __name__=='__main__':main()
