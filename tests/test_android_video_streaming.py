import subprocess

from tools.verify_android_device_proof import decode_video_samples


def test_decoder_reads_complete_movie_but_keeps_only_selected_frames(tmp_path):
    movie=tmp_path/'fixture.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
        'color=c=red:s=64x48:r=15:d=2','-c:v','libx264','-pix_fmt','yuv420p',str(movie)],check=True)
    frames,count=decode_video_samples(movie,[0,15,29],width=64,height=48)
    assert count==30 and set(frames)=={0,15,29}
    assert sum(frame.nbytes for frame in frames.values())==3*64*48*3
    assert all(frame[:,:,0].mean()>240 and frame[:,:,1:].mean()<8 for frame in frames.values())
