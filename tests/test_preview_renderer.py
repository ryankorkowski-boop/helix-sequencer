from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import preview_renderer


class PreviewRendererTests(unittest.TestCase):
    def test_finalize_preview_video_promotes_silent_when_audio_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            temp_path = root / "clip.silent.mp4"
            out_path = root / "clip.mp4"
            temp_path.write_bytes(b"silent-video")

            preview_renderer._finalize_preview_video(
                temp_path=temp_path,
                out_path=out_path,
                audio_path=None,
            )

            self.assertTrue(out_path.exists())
            self.assertEqual(out_path.read_bytes(), b"silent-video")
            self.assertFalse(temp_path.exists())

    def test_finalize_preview_video_falls_back_when_mux_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            temp_path = root / "clip.silent.mp4"
            out_path = root / "clip.mp4"
            audio_path = root / "song.wav"
            temp_path.write_bytes(b"silent-video")
            audio_path.write_bytes(b"audio")

            with mock.patch("tools.preview_renderer.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
                with mock.patch("tools.preview_renderer.subprocess.run", side_effect=RuntimeError("mux failed")):
                    preview_renderer._finalize_preview_video(
                        temp_path=temp_path,
                        out_path=out_path,
                        audio_path=audio_path,
                    )

            self.assertTrue(out_path.exists())
            self.assertEqual(out_path.read_bytes(), b"silent-video")
            self.assertFalse(temp_path.exists())

    def test_finalize_preview_video_cleans_temp_after_successful_mux(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            temp_path = root / "clip.silent.mp4"
            out_path = root / "clip.mp4"
            audio_path = root / "song.wav"
            temp_path.write_bytes(b"silent-video")
            audio_path.write_bytes(b"audio")

            def _run_side_effect(cmd, **_kwargs):  # type: ignore[no-untyped-def]
                Path(cmd[-1]).write_bytes(b"muxed-video")
                return None

            with mock.patch("tools.preview_renderer.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
                with mock.patch("tools.preview_renderer.subprocess.run", side_effect=_run_side_effect):
                    preview_renderer._finalize_preview_video(
                        temp_path=temp_path,
                        out_path=out_path,
                        audio_path=audio_path,
                    )

            self.assertTrue(out_path.exists())
            self.assertEqual(out_path.read_bytes(), b"muxed-video")
            self.assertFalse(temp_path.exists())


if __name__ == "__main__":
    unittest.main()
