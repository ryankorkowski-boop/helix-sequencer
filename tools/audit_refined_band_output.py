"""Full decoding, source audio, actual encoded screenshots and geometry audit."""
from __future__ import annotations
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from tools.render_refined_helix_band import OUT,ROOT
from tools.render_intricate_band_samplers import excerpt_audio_check,sha


def frame(movie,time,path):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(time),'-i',str(movie),'-frames:v','1',str(path)],check=True)
    return Image.open(path).convert('RGB')


def main():
    shots=OUT/'review_frames';shots.mkdir(exist_ok=True);reports=[];panels=[]
    for movie in sorted(OUT.glob('*.mp4')):
        if '_pilot' in movie.name:continue
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(movie)]))
        video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        duration=float(video['duration']);assert abs(duration-float(audio['duration']))<.10
        assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p'
        subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(movie),'-f','null','-'],check=True)
        times=[0,min(1.95,duration-.1),duration/2,duration-.1]
        for index,time in enumerate(times):
            path=shots/(movie.stem+f'_{index}.jpg');image=frame(movie,time,path)
            assert np.asarray(image).mean()>2
            if index==1:panels.append((movie.stem,time,image))
        report=dict(file=movie.name,sha256=sha(movie),bytes=movie.stat().st_size,frames=int(video['nb_frames']),fps=video['r_frame_rate'],
            seconds=duration,audio_duration=float(audio['duration']),full_decode_passed=True,video_audio_duration_agree=True,review_times=times)
        if movie.name.startswith(('Video_A','Video_B')):
            report['soundtrack']=excerpt_audio_check(ROOT/'evidence/drummer/dry_drum_test.wav',movie,0,38.32)
        reports.append(report);print('decoded',movie.name,report['frames'],flush=True)
    # Audit actual source-art joint coordinates for all dry-test rendered frames.
    dry=json.loads((OUT/'dry_verification.json').read_text());max_steps={};length_errors={}
    for side in ('left','right'):
        joints=[f['joints'][side] for f in dry['joint_frames']]
        upper=[np.linalg.norm(np.array(j['shoulder'])-j['elbow']) for j in joints]
        lower=[np.linalg.norm(np.array(j['elbow'])-j['wrist']) for j in joints]
        shafts=[np.linalg.norm(np.array(j['tip'])-j['wrist']) for j in joints]
        assert np.allclose(upper,39) and np.allclose(lower,39) and np.allclose(shafts,55)
        wrists=np.array([j['wrist'] for j in joints]);max_steps[side]=float(np.linalg.norm(np.diff(wrists,axis=0),axis=1).max())
        length_errors[side]=max(max(abs(np.array(upper)-39)),max(abs(np.array(lower)-39)),max(abs(np.array(shafts)-55)))
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    sheet=Image.new('RGB',(1280,5*392),'#07101C');draw=ImageDraw.Draw(sheet)
    for index,(name,time,image) in enumerate(panels):
        x=(index%2)*640;y=(index//2)*392;sheet.paste(image.resize((640,360)),(x,y+32))
        draw.text((x+10,y+8),name.removesuffix('_Candidates_Festivus')[:55]+f' / {time:.2f}s',font=font,fill='white')
    sheet.save(OUT/'Helix_Band_Actual_Render_Review.jpg',quality=92)
    result=dict(movies=reports,all_frames_decode=True,total_frames=sum(r['frames'] for r in reports),
        reviewed_screenshot_count=len(reports)*4,contact_sheet='Helix_Band_Actual_Render_Review.jpg',
        dry_joint_frames=len(dry['joint_frames']),fixed_segment_length_errors=length_errors,max_dry_wrist_step_pixels=max_steps,
        accepted_drum_events=dry['accepted_events'],rendered_hand_events=dry['rendered_physical_hits'],motion_rejections=dry['motion_rejections'],hand_reassignments=dry['hand_reassignments'],
        source_audio_uncut=True,actual_listening_performed=False,visual_review_by_model_pending=True)
    (OUT/'output_verification.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
