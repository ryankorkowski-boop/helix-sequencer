from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from tools import preview_renderer


class _FakeFrame:
    def convert(self, _: str) -> np.ndarray:
        return np.zeros((4, 4, 3), dtype=np.uint8)


class _FakeHouseRenderer:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def render_frame(self, **_: object) -> _FakeFrame:
        return _FakeFrame()


class _FakeWriter:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append_data(self, _: np.ndarray) -> None:
        return None

    def close(self) -> None:
        self.path.write_bytes(b"silent-preview")


class PreviewRendererTests(unittest.TestCase):
    def _render_with_patches(
        self,
        *,
        root: Path,
        audio_path: Path | None,
        run_side_effect: object = None,
    ) -> tuple[Path, Path]:
        sequence_path = root / "demo.xsq"
        sequence_path.write_text("<xsequence />", encoding="utf-8")
        out_path = sequence_path.with_suffix(".mp4")
        temp_path = out_path.with_suffix(".silent.mp4")

        sequence = preview_renderer.SequenceData(duration_ms=1000, model_effects={}, timing_tracks={})
        leaf_names = ["Model 1"]
        intensity = np.ones((1, 1), dtype=np.float32)
        colors = np.full((1, 1, 3), 220, dtype=np.uint8)
        modes = np.zeros((1, 1), dtype=np.uint8)
        phases = np.zeros((1, 1), dtype=np.float32)

        def _get_writer(path: Path, **_: object) -> _FakeWriter:
            return _FakeWriter(path)

        imageio_stub = SimpleNamespace(get_writer=_get_writer)
        ffmpeg_stub = SimpleNamespace(get_ffmpeg_exe=lambda: "ffmpeg")
        if callable(run_side_effect) or isinstance(run_side_effect, BaseException):
            run_patch = patch.object(preview_renderer.subprocess, "run", side_effect=run_side_effect)
        elif run_side_effect is None:
            run_patch = patch.object(
                preview_renderer.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(args=["ffmpeg"], returncode=0),
            )
        else:
            run_patch = patch.object(preview_renderer.subprocess, "run", return_value=run_side_effect)

        with (
            patch.object(preview_renderer, "np", np),
            patch.object(preview_renderer, "parse_sequence", return_value=sequence),
            patch.object(
                preview_renderer,
                "build_leaf_intensity_matrix",
                return_value=(leaf_names, intensity, colors, modes, phases),
            ),
            patch.object(preview_renderer, "HouseRenderer", _FakeHouseRenderer),
            patch.object(preview_renderer, "imageio", imageio_stub),
            patch.object(preview_renderer, "imageio_ffmpeg", ffmpeg_stub),
            run_patch,
        ):
            result = preview_renderer.render_sequence_to_mp4(
                sequence_path=sequence_path,
                layout=SimpleNamespace(),
                audio_path=audio_path,
                fps=24,
                width=320,
                height=180,
            )
        self.assertEqual(result, out_path)
        return out_path, temp_path

    def test_no_audio_promotes_silent_preview_to_expected_mp4(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_path, temp_path = self._render_with_patches(root=Path(temp_dir), audio_path=None)
            self.assertTrue(out_path.exists())
            self.assertFalse(temp_path.exists())
            self.assertEqual(out_path.read_bytes(), b"silent-preview")

    def test_audio_mux_failure_falls_back_to_expected_mp4(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audio_path = root / "song.wav"
            audio_path.write_bytes(b"fake-audio")

            def _raise_failure(*_: object, **__: object) -> None:
                raise subprocess.CalledProcessError(returncode=1, cmd=["ffmpeg"])

            out_path, temp_path = self._render_with_patches(
                root=root,
                audio_path=audio_path,
                run_side_effect=_raise_failure,
            )
            self.assertTrue(out_path.exists())
            self.assertFalse(temp_path.exists())
            self.assertEqual(out_path.read_bytes(), b"silent-preview")

    def test_audio_mux_missing_output_falls_back_to_expected_mp4(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audio_path = root / "song.wav"
            audio_path.write_bytes(b"fake-audio")

            run_result = subprocess.CompletedProcess(args=["ffmpeg"], returncode=0)
            out_path, temp_path = self._render_with_patches(
                root=root,
                audio_path=audio_path,
                run_side_effect=run_result,
            )
            self.assertTrue(out_path.exists())
            self.assertFalse(temp_path.exists())
            self.assertEqual(out_path.read_bytes(), b"silent-preview")

    def test_audio_mux_success_keeps_muxed_mp4_and_deletes_silent_temp(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audio_path = root / "song.wav"
            audio_path.write_bytes(b"fake-audio")

            def _write_muxed_output(cmd: list[str], **_: object) -> subprocess.CompletedProcess:
                Path(cmd[-1]).write_bytes(b"muxed-preview")
                return subprocess.CompletedProcess(args=cmd, returncode=0)

            out_path, temp_path = self._render_with_patches(
                root=root,
                audio_path=audio_path,
                run_side_effect=_write_muxed_output,
            )
            self.assertTrue(out_path.exists())
            self.assertFalse(temp_path.exists())
            self.assertEqual(out_path.read_bytes(), b"muxed-preview")


if __name__ == "__main__":
    unittest.main()
