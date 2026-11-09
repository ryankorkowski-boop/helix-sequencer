"""Real owner-audio, 12 DIFFERENT xLights layouts, with source-bound native FSEQ review.

This is an unapproved advertisement candidate; it NEVER claims a native xLights
MP4 export, verified harmony identity, or fully approved canonical band motion.
Never use synthetic music, fallback effects, or an old six-layout MP4.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import redirect_stdout
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from PIL import Image, ImageDraw

from core.audio_run_cache import AudioRunCache
from core import effect_engine as engine
from models.approval_layouts import build_layout, NAMES
from tools.build_review_sampler import activity_start
from tools.build_helpers.ultimate_showcase import write_layout
from tools.build_helpers.ultimate_showcase_preview import _font
from tools.run_showcase_audio_batch import model_routes
from tools.showcase_audio_native import prepare_template, native_music_xsq
from tools.showcase_audio_preview import NativeSongView
from tools.fseq_pixel_preview import FseqReader

DURATION = 36
CLIP = 12
SOURCES = (
    ("Wub Wub Wonderland", "138aiXex83gbRKi5a88U6rtB54HTSH3iN",
     "76641340a2a59c5797b333cd36b1e108f503017d190510fbe8da9931ea3f9abc", "mp3", 110.0, "Vocal song passage: chorus not independently verified"),
    ("Frosted Axes", "1pkP14ep7R2bDEHgW67F3SeCrI7nJXLuJ",
     "6cd567832e6534e1fee26000abfb8a3eef066985752716a6899fb3a2973736ad", "mp3", None, "Instrumental guitar passage: solo classification pending"),
    ("Dry Drum Test", "1Ukn_htJnnrQHfF183wx_pjvaPrvqtRVQ",
     "4cd9ee35b65d359aa44ac4c9e01a256bbcaf3297458340fc512084bae1463913", "wav", None, "Drum-focused real audio"),
)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def run(command, **kw):
    return subprocess.run(command, check=True, **kw)

def music(root: Path):
    import gdown
    src = root / "sources"
    src.mkdir(parents=True, exist_ok=True)
    pieces, manifest = [], []
    for title, fileid, sha, ext, requested_start, tag in SOURCES:
        path = src / (title + "." + ext)
        if not path.exists() or digest(path) != sha:
            path.unlink(missing_ok=True)
            if not gdown.download(id=fileid, output=str(path), quiet=False):
                raise RuntimeError("Cannot retrieve real owner audio: " + title)
        if digest(path) != sha:
            raise ValueError("Source changed: " + title)
        run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
            stdout=subprocess.DEVNULL)
        wave, sr = sf.read(path, dtype="float32", always_2d=True)
        if not np.isfinite(wave).all() or wave.shape[1] not in (1,2):
            raise ValueError("Invalid owner audio: " + title)
        start = (activity_start(wave, sr, CLIP) if requested_start is None
                 else requested_start)
        if start < 0 or start + CLIP > len(wave) / sr:
            raise ValueError("Source selection outside track: " + title)
        cut = wave[round(start*sr):round((start+CLIP)*sr)]
        common = math.gcd(sr, 44100)
        cut = resample_poly(cut, 44100//common, sr//common, axis=0)
        if cut.shape[1] == 1:
            cut = np.repeat(cut, 2, axis=1)
        cut = cut[:CLIP * 44100]
        if len(cut) != CLIP * 44100:
            raise ValueError("Excerpt resampling produced wrong length")
        fade = int(.03*44100)
        cut[:fade] *= np.linspace(0,1,fade)[:,None]
        cut[-fade:] *= np.linspace(1,0,fade)[:,None]
        pieces.append(cut)
        manifest.append(dict(title=title,drive_file_id=fileid,sha256=sha,
                             source_start_seconds=round(float(start),3),
                             excerpt_seconds=CLIP,caption=tag,
                             selection_method="Explicit prior owner-audio window" if requested_start is not None else
                             "Peak activity window; NOT independently verified solo"))
    combined = np.concatenate(pieces,axis=0)
    gain = min(1., .98/max(float(np.max(np.abs(combined))),1e-8))
    audio = root / "HELIX_Real_Audio_Three_Passages.wav"
    sf.write(audio, combined*gain, 44100, subtype="PCM_16")
    if sf.info(audio).duration != DURATION:
        raise ValueError("Sampler must last exactly 36s")
    payload=dict(source="Owner Google Drive lyric and instrumental folders",
                 media_sha256=digest(audio), clips=manifest, duration_seconds=DURATION,
                 source_recordings_are_real=True,source_segments_are_unmodified_in_pitch=True,
                 owner_approval="PENDING",chorus_ground_truth_verified=False,
                 instrumental_solo_ground_truth_verified=False)
    (root/"sampler_provenance.json").write_text(json.dumps(payload,indent=2)+"\n")
    return audio,payload

def tuning(show, garden):
    return engine.RuntimeTuning(layout_file=show/"xlights_rgbeffects.xml",
        template_guidance=False,workspace_history_enabled=False,
        learning_memory_enabled=False,matrix_intelligence=False,polish_enabled=False,
        variant_count=1,birdsong_enabled=False,birdsong_auto=False,
        audio_reactive_profile="showcase",audio_reactive_intensity=1.5,
        spatial_awareness=.85,chase_style="radial_out",
        model_overrides=model_routes(garden),max_layers_per_prop=3)

def prepare_for_engine(g, show):
    # An empty AC-only layout cannot seed the "On" template because the
    # established template generator skips AC fixtures. Create the seed with
    # cloned display kinds, then restore the ACTUAL AC XML before sequencing.
    if all(m.kind == "ac" for m in g.models):
        seed = copy.copy(g)
        seed.models = [copy.copy(m) for m in g.models]
        for m in seed.models:
            m.kind = "pixel"
        template = prepare_template(seed, show)
        write_layout(g,show,include_demo=False,export_all_custom=True)
        return template
    return prepare_template(g,show)

def export_one(root, audio, number, xlights, cache):
    g=build_layout(number,include_xylophonist=False,full_keyboard=True)
    budget = {1:16,2:64,3:256}
    if number in budget and sum(m.channels for m in g.models) != budget[number]:
        raise ValueError("Incorrect physical AC circuit count")
    cast=[m.details.get("review_role") for m in g.models if m.details.get("review_role")]
    if number in (7,8,12) and set(cast)!={"drummer","bass","guitar","piano","lead","harmony"}:
        raise ValueError("Wrong band cast: "+str(cast))
    out=root/"shows"/f"{number:02}_{NAMES[number-1]}"
    out.mkdir(parents=True,exist_ok=False)
    template=prepare_for_engine(g,out)
    local=out/audio.name
    shutil.copyfile(audio,local)
    if digest(local)!=digest(audio):
        raise ValueError("Sampler changed when staged")
    raw=out/"engine_raw.xsq"
    with (out/"helix_engine.log").open("w") as log,redirect_stdout(log):
        engine.run_variant(engine.VARIANTS["v27.3"],template,local,raw,
                           engine.base.UserProfile(),tuning=tuning(out,g),analysis_cache=cache)
    # The converter's RGB-only gate is intended to exclude control fixtures.
    # Real separately wired AC lighting is not a control fixture; permit its
    # named models in a COPY of the converter's selection state without ever
    # changing the AC model StringType, circuit count or native layout XML.
    inclusion=copy.copy(g)
    inclusion.models=[copy.copy(m) for m in g.models]
    for m in inclusion.models:
        if m.kind=="ac":
            m.kind="pixel"
    xsq=out/"Performance.xsq"
    info=native_music_xsq(raw,xsq,inclusion,local,DURATION)
    if info["native_effects"] <= 0:
        raise ValueError("No actual Helix effects: "+NAMES[number-1])
    native_cmd=[str(xlights),"--headless","-q","-s",str(out.resolve()),
                "-od",str(out.resolve()),str(xsq.resolve())]
    if shutil.which("xvfb-run"):
        native_cmd=["xvfb-run","-a",*native_cmd]
    with (out/"xlights_native.log").open("w") as log:
        run(native_cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1500,
            env={**os.environ,"XL_NO_GPU_COMPUTE":"1","LIBGL_ALWAYS_SOFTWARE":"1"})
    fseq=xsq.with_suffix(".fseq")
    reader=FseqReader(fseq)
    if reader.info.step_ms!=50 or reader.info.frames!=DURATION*20:
        raise ValueError(f"Native FSEQ timing wrong: {number}")
    proof=dict(number=number,title=NAMES[number-1],layout=out.name,
               xsq=str(xsq.relative_to(root)),fseq=str(fseq.relative_to(root)),
               layout_xml=str((out/"xlights_rgbeffects.xml").relative_to(root)),
               xsq_sha256=digest(xsq),fseq_sha256=digest(fseq),
               layout_sha256=digest(out/"xlights_rgbeffects.xml"),
               audio_sha256=digest(local),channel_count=sum(m.channels for m in g.models),
               models=len(g.models),cast=cast,
               native_effect_count=info["native_effects"],
               frame_count=reader.info.frames,frame_ms=reader.info.step_ms,
               native_xlights_fseq=True,native_xlights_mp4_export=False)
    (out/"native_proof.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("NATIVE_SUCCEEDED",number,NAMES[number-1],proof["native_effect_count"],flush=True)
    return proof

def visual_model(g,number):
    """Presentation-only AC circuit-to-bulb RGB visualization of actual FSEQ."""
    original=[m for m in g.models]
    visual=copy.copy(g)
    visual.models=[copy.copy(m) for m in original]
    sources=[];gains=[];start=1
    for old,new in zip(original,visual.models,strict=True):
        n=len(old.points)
        if old.kind=="ac":
            circuit=np.asarray(old.details["point_circuits"],int)
            if len(circuit)!=n or circuit.min()<1 or circuit.max()>old.channels:
                raise ValueError("Invalid AC point-to-circuit map")
            idx=np.repeat(old.start-1+circuit-1,3)
            string=old.attrs.get("StringType","Single Color White")
            rgb=np.array((255,0,0) if "Red" in string else
                         (0,255,0) if "Green" in string else
                         (0,0,255) if "Blue" in string else (245,240,220),np.float32)/255
            weight=np.tile(rgb,n)
        else:
            idx=old.start-1+np.arange(n*3)
            weight=np.ones(n*3,dtype=np.float32)
        sources.extend(idx.tolist());gains.extend(weight.tolist())
        new.kind="pixel"
        new.start=start
        start+=n*3
    if number==7:
        # Camera-only reframing, never a change to the underlying native nodes.
        bounds=np.concatenate([m.points for m in visual.models])
        center=(bounds.min(axis=0)+bounds.max(axis=0))/2
        for m in visual.models:
            m.points=(m.points-center)*2.1+np.array([0,35,0])
    return visual,np.asarray(sources,dtype=np.int64),np.asarray(gains,dtype=np.float32)

def frames_to_full(reader, payload, total_channels):
    values=np.zeros(total_channels,np.uint8)
    raw=np.frombuffer(payload,np.uint8)
    if reader.info.ranges:
        pos=0
        for start,count in reader.info.ranges:
            values[start:start+count]=raw[pos:pos+count]
            pos+=count
        if pos!=len(raw):
            raise ValueError("Unexpected sparse channel payload")
    else:
        values[:len(raw)]=raw
    return values

def compose(root, audio, proofs):
    n=12
    if len(proofs)!=n:
        raise ValueError("Must have all twelve distinct native layouts")
    views=[];iters=[];readers=[];maps=[]
    for p in proofs:
        g=build_layout(p["number"],include_xylophonist=False,full_keyboard=True)
        if sum(m.channels for m in g.models)!=p["channel_count"]:
            raise ValueError("Geometry drift between native export and review")
        projection,offsets,gains=visual_model(g,p["number"])
        views.append(NativeSongView(projection,audio.stem,480,270,halo_scale=2,
                                    yaw=7,pitch=18))
        reader=FseqReader(root/p["fseq"])
        readers.append(reader);iters.append(reader.iter_frames())
        maps.append((offsets,gains,p["channel_count"]))
    movie=root/"HELIX_12_DISTINCT_NATIVE_LAYOUTS_REAL_AUDIO.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo",
         "-pixel_format","rgb24","-video_size","1920x1080","-framerate","20",
         "-i","-","-i",str(audio),"-map","0:v:0","-map","1:a:0","-t",str(DURATION),
         "-c:v","libx264","-preset","veryfast","-crf","21","-threads","2",
         "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",
         str(movie)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for k in range(DURATION*20):
            picture=Image.new("RGB",(1920,1080),"#07101c")
            draw=ImageDraw.Draw(picture)
            section= ("VOCAL SONG" if k<240 else
                      "GUITAR INSTRUMENTAL" if k<480 else "DRUM TEST")
            draw.text((22,12),"HELIX / 12 DISTINCT NATIVE XLIGHTS LAYOUTS / "+section,
                      fill="#f0f6ff",font=_font(25))
            for j,(v,it,r,mapping,p) in enumerate(zip(views,iters,readers,maps,proofs,strict=True)):
                raw=next(it)
                offsets,gains,total=mapping
                full=frames_to_full(r,raw,total)
                color=np.clip(full[offsets]*gains,0,255).astype(np.uint8)
                panel=v.frame(color)
                x=(j%4)*480;y=63+(j//4)*322
                picture.paste(panel,(x,y))
                draw.rectangle((x,y+270,x+480,y+301),fill="#081827")
                draw.text((x+12,y+275),f"{j+1:02} / {p['title'].replace('_',' ')}",
                          fill="#e3efff",font=_font(17))
            draw.text((22,1035),
                      "Source-bound Helix sequences / native xLights FSEQ / projected review camera / approval PENDING",
                      fill="#aac7db",font=_font(17))
            proc.stdin.write(picture.tobytes())
            if k%120==0:
                print("COMPOSITE_FRAMES",k,"/",DURATION*20,flush=True)
    except BaseException:
        proc.terminate()
        raise
    finally:
        proc.stdin.close()
    if proc.wait()!=0:
        raise RuntimeError("FFmpeg composition failed")
    run(["ffmpeg","-v","error","-xerror","-i",str(movie),"-f","null","-"],
        stdout=subprocess.DEVNULL)
    meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams",
                                             "-show_format","-of","json",str(movie)]))
    v=next(s for s in meta["streams"] if s["codec_type"]=="video")
    a=next(s for s in meta["streams"] if s["codec_type"]=="audio")
    if v["width"]!=1920 or v["height"]!=1080 or v["codec_name"]!="h264" or a["codec_name"]!="aac":
        raise ValueError("Failed MP4 technical validation")
    return dict(file=movie.name,sha256=digest(movie),width=1920,height=1080,
                fps=20,duration=float(meta["format"]["duration"]),full_decode=True,
                source_audio_sha256=digest(audio),
                native_xlights_fseq=True,native_xlights_video_export=False,
                performer_accuracy_and_stemless_harmony_unverified=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--xlights",type=Path,required=True)
    parser.add_argument("--preflight-only",action="store_true")
    a=parser.parse_args()
    if a.preflight_only:
        inventory=[]
        for number in range(1,13):
            g=build_layout(number,include_xylophonist=False,full_keyboard=True)
            roles=[m.details.get("review_role") for m in g.models if m.details.get("review_role")]
            row=dict(number=number,name=NAMES[number-1],
                     models=len(g.models),channels=sum(m.channels for m in g.models),
                     roles=roles)
            if number in (1,2,3) and row["channels"]!=[16,64,256][number-1]:
                raise ValueError("AC bank constraint violated")
            if number in (7,8,12) and set(roles)!={"drummer","bass","guitar","piano","lead","harmony"}:
                raise ValueError("Canonical cast constraint violated")
            inventory.append(row)
        print(json.dumps(inventory,indent=2),flush=True)
        return
    root=a.output.resolve()
    root.mkdir(parents=True,exist_ok=True)
    audio,provenance=music(root)
    cache=AudioRunCache(digest(audio))
    proofs=[]
    try:
        for number in range(1,13):
            proofs.append(export_one(root,audio,number,a.xlights.resolve(),cache))
            (root/"partial_manifest.json").write_text(json.dumps(proofs,indent=2)+"\n")
        video=compose(root,audio,proofs)
        manifest=dict(schema="helix.twelve-distinct-native-ad.v1",
                      owner_approval="PENDING",release_acceptance=False,
                      canonical_band_motion_owner_approved=False,
                      audio=provenance,layouts=proofs,video=video)
        (root/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print("OWNER_REVIEW_MP4_CREATED",root/video["file"],flush=True)
    finally:
        (root/"partial_manifest.json").write_text(json.dumps(proofs,indent=2)+"\n")

if __name__=="__main__":
    main()
