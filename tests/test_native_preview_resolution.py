"""Regression tests: never accept xLights docked House Preview as HD video."""
import unittest
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


if __name__ == "__main__":
    unittest.main()
