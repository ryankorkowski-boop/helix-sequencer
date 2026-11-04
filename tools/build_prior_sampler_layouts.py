"""Sequence the exact recovered sampler through current Helix on six new shows."""
from __future__ import annotations
from core.engine_runner import run_variant
import argparse
from contextlib import redirect_stdout
import json
from pathlib import Path
import shutil
import soundfile as sf

from core.audio_run_cache import AudioRunCache
from core import effect_engine as engine
from models.showcase_flavors import FLAVORS,build_flavor
from tools.run_showcase_audio_batch import model_routes,digest
from tools.showcase_audio_native import prepare_template,native_music_xsq


SAMPLER_SHA='0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audio',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert digest(a.audio)==SAMPLER_SHA,'Use the recovered exact sampler WAV'
    root=a.output.resolve();root.mkdir(parents=True,exist_ok=True);audio=a.audio.resolve()
    duration=sf.info(audio).duration;cache=AudioRunCache(SAMPLER_SHA);rows=[]
    for f in FLAVORS:
        g=build_flavor(f.key);folder=root/g.slug;folder.mkdir(parents=True,exist_ok=True)
        template=prepare_template(g,folder);media=folder/audio.name;shutil.copyfile(audio,media)
        raw=folder/'sampler.prime_raw.xsq'
        tuning=engine.RuntimeTuning(layout_file=folder/'xlights_rgbeffects.xml',template_guidance=False,
            workspace_history_enabled=False,learning_memory_enabled=False,matrix_intelligence=False,
            polish_enabled=False,variant_count=1,birdsong_enabled=False,birdsong_auto=False,
            audio_reactive_profile='showcase',audio_reactive_intensity=1.6,spatial_awareness=.85,
            chase_style='radial_out',model_overrides=model_routes(g),max_layers_per_prop=3)
        with (folder/'engine.log').open('w') as log,redirect_stdout(log):
            run_variant(engine.VARIANTS['v27.3'],template,media,raw,engine.base.UserProfile(),tuning=tuning,analysis_cache=cache)
        native=folder/(g.slug+'_Sampler.xsq');export=native_music_xsq(raw,native,g,media,duration)
        row=dict(flavor=f.key,folder=g.slug,xsq=native.name,layout=g.title,audio_sha256=SAMPLER_SHA,
                 duration_seconds=duration,export=export)
        rows.append(row);(root/'manifest.json').write_text(json.dumps(dict(runs=rows,analysis_cache_hits=cache.hits),indent=2)+'\n')
        print(g.slug,export['native_effects'],flush=True)


if __name__=='__main__':main()
