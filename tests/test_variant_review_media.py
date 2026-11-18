import subprocess

import pytest

from tools.variant_review_media import compose


def test_eight_panel_comparison_and_serial_review_decode(tmp_path):
    ffmpeg = pytest.importorskip("imageio_ffmpeg").get_ffmpeg_exe()
    paths = []
    for index in range(8):
        path = tmp_path / f"variant-{index+1}.mp4"
        subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-y",
                        "-f", "lavfi", "-i", f"color=c=0x{index*30:02x}4060:s=160x90:r=15:d=0.4",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:d=0.4",
                        "-c:v", "libx264", "-threads", "1", "-c:a", "aac", "-shortest", str(path)],
                       check=True)
        paths.append(path)
    for comparison, expected_samples in ((True, 17_640), (False, 141_120)):
        output = tmp_path / f"review-{comparison}.mp4"
        compose(paths, output, comparison=comparison)
        # Fully decode audio and video. Map a single mixed-independent stream:
        # simultaneous panels use variant 1's clock and serial review preserves
        # the duration of all eight successive clips.
        subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-"],
                       check=True)
        pcm = subprocess.check_output([ffmpeg, "-v", "error", "-i", str(output),
                                       "-map", "0:a:0", "-f", "s16le", "-"])
        assert abs(len(pcm) // 2 - expected_samples) <= 8192
