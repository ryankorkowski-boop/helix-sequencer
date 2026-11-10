from dataclasses import dataclass

@dataclass
class EffectEvent:
    start_ms:int
    end_ms:int
    target:str
    effect:str='ON'


def build_demo_plan():
    events=[]
    for beat in range(8):
        events.append(EffectEvent(beat*500, beat*500+250, f'CH_{beat+1:03d}'))
    return events
