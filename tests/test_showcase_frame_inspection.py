import subprocess
import numpy as np
from tools.validate_showcase_mp4 import inspect_decoded_frames


def test_detects_a_dark_frame_between_visible_frames(tmp_path):
    movie=tmp_path/'frames.mp4'
    frames=np.full((3,32,32,3),255,'u1');frames[1]=0
    subprocess.run(['ffmpeg','-v','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','32x32','-r','1','-i','-','-c:v','libx264','-crf','0',str(movie)],
        input=frames.tobytes(),check=True)
    result=inspect_decoded_frames(movie)
    assert result['frames_fully_decoded']==3
    assert result['wholly_dark_frame_indices']==[1]
    assert result['changed_adjacent_frames']==2
