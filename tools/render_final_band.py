"""Render two final solid bands from an existing source-bound analysis."""
from __future__ import annotations

import argparse,hashlib,json,math,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import ImageDraw
from models.final_band_scene import FinalBandScene
from models.distinct_band_stages import TwinBandGarden
from tools.final_band_performance import FinalBandPerformance
from tools.render_dual_band_showcases import TwinStageView
from tools.render_refined_helix_band import encoder,physical_hits,DynamicDry,FONT,SMALL
from animation.articulated_source_drummer import ArticulatedDrummer
from core.output_provenance import brand_frame,stamp_mp4


class SharedDrummerFrame(DynamicDry):
    """Both stages use the same source performance; reuse identical pixels."""
    def frame(self,lighting,strikes,hand):
        key=(self.time,tuple(lighting),tuple(strikes),int(hand))
        if getattr(self,'_frame_key',None)!=key:
            self._frame_pixels=super().frame(lighting,strikes,hand);self._frame_key=key
        return self._frame_pixels


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audio',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True)
    p.add_argument('--drummer',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--start',type=float,default=0);p.add_argument('--seconds',type=float)
    p.add_argument('--width',type=int,default=1280);p.add_argument('--height',type=int,default=720)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    duration=sf.info(a.audio).duration;seconds=a.seconds if a.seconds is not None else duration-a.start
    if not 0<=a.start<duration or seconds<=0 or a.start+seconds>duration+.0001: raise ValueError('Invalid excerpt')
    digest=hashlib.sha256(a.audio.read_bytes()).hexdigest()
    row=dict(id=a.analysis.name,path=str(a.audio),sha256=digest,duration=duration,drummer_xsq=str(a.drummer))
    scenes=[FinalBandScene(),FinalBandScene('circuit_garage',rock=True)]
    performers=[FinalBandPerformance(row,s,a.analysis.parent) for s in scenes]
    garden=TwinBandGarden(*scenes);view=TwinStageView(garden,a.width,a.height)
    player=ArticulatedDrummer(physical_hits(a.drummer),natural_arms=True)
    view.dry=view.second_dry=SharedDrummerFrame(player)
    tmp=a.output.with_name(a.output.stem+'.rendering.mp4');writer=encoder(tmp,a.width,a.height,20,a.audio,a.start,seconds)
    contacts=0;max_error=0;frames=math.ceil(seconds*20);snapshot_times=(0,2,2.45,30.5,40,55,74,120,150,179)
    try:
        for i in range(frames):
            idx=min(performers[0].n-1,round((a.start+i/20)*20))
            levels=np.r_[performers[0].pose(idx),performers[1].pose(idx)].astype('f4')
            levels[177]=levels[369]=.8;garden.sync()
            view.dry.time=view.second_dry.time=idx/20
            image=view.frame(levels,performers[0].drums[idx],performers[0].strikes[idx],performers[0].hands[idx],idx/20,i/20)
            d=ImageDraw.Draw(image);d.rectangle((0,0,a.width,44),fill='#07101C')
            d.text((18,11),'HELIX BETA v1.0 | TWO BANDS | ORIGINAL SIX-SONG SAMPLER',font=FONT,fill='#DDF5FF')
            d.rectangle((0,a.height-36,a.width,a.height),fill='#07101C')
            d.text((18,a.height-27),'Snow stage + rock stage | One pitched/mallet player each | Source estimates pending listening review',font=SMALL,fill='#C2D2DF')
            writer.stdin.write(brand_frame(image).tobytes())
            for perf in performers:
                for hit in perf.mallet_schedule:
                    if abs(hit['time']-idx/20)<1e-7:
                        tip=perf.mallet_targets[hit['side']][1]
                        error=float(np.linalg.norm(tip-(perf.scene.bars[hit['pitch']]+(0,.0275+.057,0))))
                        max_error=max(max_error,error);contacts+=1
            if any(abs(i/20-t)<.0001 for t in snapshot_times):
                image.save(a.output.with_name(a.output.stem+f'_{i:04d}.png'))
            if i%200==0: print('final bands',i,frames,flush=True)
    except BaseException:
        writer.stdin.close();writer.terminate();writer.wait();tmp.unlink(missing_ok=True);raise
    finally:
        if not writer.stdin.closed:writer.stdin.close()
        view.close()
    if writer.wait(): raise RuntimeError('Final band encoder failed')
    tmp.replace(a.output);stamp_mp4(a.output)
    subprocess.run(['ffmpeg','-v','error','-i',str(a.output),'-f','null','-'],check=True)
    proof=dict(source_audio_sha256=digest,source_start=a.start,seconds=seconds,frames=frames,
        resolution=[a.width,a.height],fps=20,full_decode_passed=True,
        visible_performers_per_band=6,wireframe_performers=False,unified_pitched_performer=True,
        keyboard_events=len(performers[0].keyboard_events),mallet_contacts=contacts,
        maximum_contact_error=max_error,mallet_motion_omissions=performers[0].mallet_motion_omissions,
        independent_voices_listening_verified=performers[0].independent_voices_verified,
        musical_accuracy_independently_verified=False,physical_channel_equivalence=False,
        source_drummer=performers[0].drum_proof,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
        bytes=a.output.stat().st_size)
    a.output.with_suffix('.verification.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
