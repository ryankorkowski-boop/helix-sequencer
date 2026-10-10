"""Second recognition pass on a difficult title, preserving the prior output."""
from pathlib import Path
import json
import torch
import stable_whisper

ROOT=Path(__file__).resolve().parents[1]


def main():
    torch.set_num_threads(2)
    model=stable_whisper.load_model('small.en',device='cpu',download_root='/workspace/runtime/whisper')
    source=ROOT/'outputs/Snowman_Ensemble/shows/05_band/media/song.mp3'
    target=ROOT/'outputs/Intricate_Band_Samplers/analysis/05/recognition_second_pass.json'
    result=model.transcribe(str(source),language='en',fp16=False,verbose=False,
        initial_prompt='Christmas song lyrics. Festivus for the rest of us. Festivus, DNA, bass guitar, winter snow.',
        condition_on_previous_text=False,temperature=0,no_speech_threshold=.6,
        suppress_silence=True,regroup=True)
    target.parent.mkdir(parents=True,exist_ok=True);result.save_as_json(str(target))
    print('SECOND_PASS_READY',len(result.segments),flush=True)
    for s in result.segments:print(round(s.start,2),round(s.end,2),s.text,flush=True)


if __name__=='__main__':main()
