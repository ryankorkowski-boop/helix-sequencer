"""Regression tests: never accept xLights docked House Preview as HD video."""
import unittest
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import native_preview as preview
from tools.native_preview import _stream


class NativePreviewResolutionTests(unittest.TestCase):
    def test_video_stream_selection(self):
        probe = {"streams": [
            {"codec_type": "audio", "codec_name": "aac"},
            {"codec_type": "video", "width": 248, "height": 442},
        ]}
        self.assertEqual(_stream(probe, "video")["width"], 248)

    def test_missing_video_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing video stream"):
            _stream({"streams": [{"codec_type": "audio"}]}, "video")

    def test_default_request_matches_default_hd_acceptance(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(preview._export_size(), (1920, 1080))

    def test_explicit_dimensions_are_used(self):
        with patch.dict(os.environ, {"HELIX_NATIVE_PREVIEW_WIDTH": "1280",
                                     "HELIX_NATIVE_PREVIEW_HEIGHT": "720"}):
            self.assertEqual(preview._export_size(), (1280, 720))

    def test_invalid_dimensions_are_rejected(self):
        for value in ("0", "319", "1921", "4098", "nan", ""):
            with self.subTest(value=value), patch.dict(
                    os.environ, {"HELIX_NATIVE_PREVIEW_WIDTH": value}):
                with self.assertRaises(ValueError):
                    preview._export_size()

    def _run_preview(self, directory, size):
        """Exercise production orchestration; fixture bytes are never media evidence."""
        run = Path(directory)
        (run / "run_manifest.json").write_text(json.dumps({
            "warnings": [], "quality": {"preserve": True}}))
        xsq, audio = run / "Performance.xsq", run / "original.wav"
        xsq.write_text('<xsequence><head><sequenceDuration>1</sequenceDuration>'
                       '</head></xsequence>')
        audio.write_bytes(b"unit source only")
        (run / "xlights_rgbeffects.xml").write_text("<xrgb/>")
        before = (xsq.read_bytes(), audio.read_bytes())

        def export(binary, show, staged, port):
            video = staged.parent / "native-silent.mp4"
            video.write_bytes(b"unit export only")
            return {"native_video": str(video), "xlights_version": "2026.18"}

        def mux(video, source_audio, output, **kwargs):
            self.assertEqual(source_audio, audio)
            output.write_bytes(b"unit mux only")
            return {"streams": [{"codec_type": "video", "width": size[0],
                                 "height": size[1]}, {"codec_type": "audio"}]}

        def render(command, **kwargs):
            Path(command[-1]).with_suffix(".fseq").write_bytes(b"unit FSEQ only")
            return SimpleNamespace(returncode=0)

        with patch.dict(os.environ, {}, clear=True), \
                patch.object(preview.shutil, "which", return_value="/bin/true"), \
                patch.object(preview.subprocess, "run", side_effect=render), \
                patch.object(preview, "inspect_fseq", return_value={"duration_ms": 1000}), \
                patch.object(preview, "_native_export", side_effect=export), \
                patch.object(preview, "probe_media", return_value={"streams": [
                    {"codec_type": "video", "width": size[0], "height": size[1]}]}), \
                patch.object(preview, "mux_original_audio", side_effect=mux) as mux_call:
            result = preview.preview_run(run, xsq=xsq, audio=audio)
        saved = json.loads((run / "run_manifest.json").read_text())
        self.assertEqual(saved["quality"], {"preserve": True})
        self.assertEqual(saved["native_preview"], result)
        self.assertEqual((xsq.read_bytes(), audio.read_bytes()), before)
        return result, mux_call

    def test_docked_preview_fails_before_audio_mux(self):
        with tempfile.TemporaryDirectory() as directory:
            report, mux = self._run_preview(directory, (248, 442))
            self.assertEqual(report["status"], "fallback")
            self.assertIsNone(report["mp4"])
            self.assertFalse(report["audio_stream_verified"])
            self.assertEqual(report["native_export_resolution"], [248, 442])
            self.assertEqual(report["requested_resolution"], [1920, 1080])
            self.assertIn("248x442", report["warnings"][0])
            mux.assert_not_called()

    def test_native_hd_passes_resolution_gate_then_muxes_selected_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            report, mux = self._run_preview(directory, (1920, 1080))
            self.assertEqual(report["status"], "success")
            self.assertTrue(report["audio_stream_verified"])
            self.assertTrue(Path(report["mp4"]).is_file())
            self.assertEqual(report["warnings"], [])
            mux.assert_called_once()


if __name__ == "__main__":
    unittest.main()

