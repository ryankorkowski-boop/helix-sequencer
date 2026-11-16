"""Add auditable word-level lyric timing to a source-bound acoustic vocal clock.

Never label evenly allocated within-word phones as acoustically verified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference_lyrics(audio):
    data=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format_tags","-of","json",str(audio)]))
    tags=data.get("format",{}).get("tags",{})
    return "\n".join(str(v) for k,v in tags.items() if "lyric" in k.lower()).strip()


def norm(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?",text.lower())


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audio",type=Path,required=True)
    p.add_argument("--stem",type=Path,required=True)
    p.add_argument("--fixture",type=Path,required=True)
    p.add_argument("--expected-sha256",required=True)
    a=p.parse_args()
    if sha(a.audio)!=a.expected_sha256:
        raise SystemExit("Source audio identity mismatch")
    import torch,stable_whisper,cmudict
    from tools.align_snowman_lyrics import compile_mouths
    from models.band_sampler_logic import SHAPE_NAMES
    torch.set_num_threads(2)
    model=stable_whisper.load_model("small.en",device="cpu")
    recognized=model.transcribe(str(a.stem),language="en",fp16=False,
        temperature=0,condition_on_previous_text=False,
        no_speech_threshold=.6,suppress_silence=True,regroup=True)
    data=recognized.to_dict()
    words=[w for s in data.get("segments",[]) for w in s.get("words",[])
           if w.get("end",0)>w.get("start",0)]
    reference=reference_lyrics(a.audio)
    ref_tokens=norm(reference)
    recognized_tokens=norm(" ".join(w.get("word","") for w in words))
    import difflib
    match=difflib.SequenceMatcher(None,recognized_tokens,ref_tokens,autojunk=False)
    matching=sum(b.size for b in match.get_matching_blocks())
    coverage=matching/max(1,len(recognized_tokens))
    # Source metadata is the minimum independent lexical corroboration.
    reference_corrob=bool(ref_tokens and recognized_tokens and
        coverage>=.90 and matching/max(1,len(ref_tokens))>=.85)
    accepted=[w for w in words if w.get("probability",0)>=.60]
    # Do not treat a plausible ASR transcript alone as verified lyrics.
    lexical_accepted=accepted if reference_corrob else []
    mouths=compile_mouths(lexical_accepted,cmudict.dict())
    clock=a.fixture/"acoustic_vocal_clocks.npz"
    with np.load(clock,allow_pickle=False) as z:
        arrays={k:z[k].copy() for k in z.files}
    energy=arrays["estimated_lead_energy"]
    shape=arrays["estimated_lead_shapes"]
    lexical=np.zeros(len(shape),dtype="i1")
    word_coverage=np.zeros(len(shape),dtype="u1")
    for m in mouths:
        start=max(0,round(m["start_ms"]/10))
        end=min(len(shape),round(m["end_ms"]/10))
        if end<=start:continue
        phone=m["phoneme"]
        if phone not in SHAPE_NAMES:continue
        lexical[start:end]=SHAPE_NAMES.index(phone)
        word_coverage[start:end]=1
    # Vocal activity is always gated by the acoustic separated source.
    # With no independently corroborated reference, retain the existing
    # conservative acoustic mouth estimates and do not invent lexical phones.
    if reference_corrob:
        arrays["estimated_lead_shapes"]=np.where(
            (word_coverage>0)&(energy>.02),lexical,0).astype("i1")
        arrays["estimated_lead_energy"]=np.where(
            word_coverage>0,energy,0).astype("f4")
        arrays["estimated_lead_presence_probability"]=np.where(
            arrays["estimated_lead_energy"]>0,.95,0).astype("f4")
    arrays["word_alignment_coverage"]=word_coverage
    np.savez_compressed(clock,**arrays)
    receipt_path=a.fixture/"diagnostic.json"
    receipt=json.loads(receipt_path.read_text())
    receipt["clock_sha256"]=sha(clock)
    receipt["word_alignment"]={
        "recognized_word_count":len(words),
        "confidence_accepted_word_count":len(accepted),
        "reference_source":"MP3 embedded lyrics" if reference else None,
        "reference_corroborated":reference_corrob,
        "recognized_reference_token_coverage":coverage,
        "corroborated_word_count":len(lexical_accepted),
        "estimated_phoneme_segments":len(mouths),
        "word_timing_method":"stable_whisper_small_en_on_Demucs_vocal_stem",
        "phone_timing_method":"dictionary_pronunciation_even_allocation_inside_word",
        "word_alignment_status":"REFERENCE_CORROBORATED_ESTIMATE" if reference_corrob else "UNVERIFIED_ASR_ONLY",
        "phoneme_boundaries_acoustically_verified":False,
        "human_listening_verified":False,
        "lyrics_reference_verified_by_owner":False}
    receipt["exact_phoneme_boundaries_verified"]=False
    receipt_path.write_text(json.dumps(receipt,indent=2)+"\n")
    (a.fixture/"word_alignment.json").write_text(json.dumps({
        "audio_sha256":sha(a.audio),"vocal_stem_sha256":sha(a.stem),
        "recognized_words":words,"reference_lyrics_present":bool(reference),
        "reference_lyrics":reference,
        "corroborated_words":lexical_accepted,
        "estimated_mouth_segments":mouths,
        "verification":receipt["word_alignment"]},indent=2)+"\n")
    print("WORD_ALIGNMENT",json.dumps(receipt["word_alignment"]))


if __name__=="__main__":
    main()
