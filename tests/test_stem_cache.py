from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from core import stem_cache


class StemCacheTests(unittest.TestCase):
    def _make_stems(self, stem_dir: Path) -> dict[str, Path]:
        track_dir = stem_dir / "htdemucs_6s" / "song"
        track_dir.mkdir(parents=True, exist_ok=True)
        stems: dict[str, Path] = {}
        for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
            path = track_dir / f"{name}.wav"
            path.write_bytes((name + "-stem").encode("utf-8"))
            stems[name] = path
        return stems

    def test_cache_round_trip_preserves_six_stems(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            audio = root / "song.wav"
            audio.write_bytes(b"original-audio")
            stem_dir = root / "cache" / audio.stem
            stems = self._make_stems(stem_dir)

            manifest = stem_cache.write_stem_cache_manifest(
                audio,
                stem_dir,
                source="demucs",
                stems=stems,
                separator="htdemucs_6s",
            )
            loaded = stem_cache.load_cached_stems(
                audio,
                stem_dir,
                allowed_sources={"demucs"},
            )

            self.assertTrue(manifest.exists())
            self.assertIsNotNone(loaded)
            source, cached_stems = loaded or ("", {})
            self.assertEqual(source, "demucs")
            self.assertEqual(set(cached_stems), set(stems))
            self.assertEqual(cached_stems["drums"].read_bytes(), b"drums-stem")

    def test_cache_invalidates_when_audio_contents_change(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            audio = root / "song.wav"
            audio.write_bytes(b"first-version")
            stem_dir = root / "cache" / audio.stem
            stems = self._make_stems(stem_dir)
            stem_cache.write_stem_cache_manifest(
                audio,
                stem_dir,
                source="demucs",
                stems=stems,
                separator="htdemucs_6s",
            )

            audio.write_bytes(b"other-version")
            self.assertIsNone(
                stem_cache.load_cached_stems(
                    audio,
                    stem_dir,
                    allowed_sources={"demucs"},
                )
            )

    def test_cache_rejects_disallowed_separator_source(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            audio = root / "song.wav"
            audio.write_bytes(b"audio")
            stem_dir = root / "cache" / audio.stem
            stems = self._make_stems(stem_dir)
            stem_cache.write_stem_cache_manifest(
                audio,
                stem_dir,
                source="demucs",
                stems=stems,
                separator="htdemucs_6s",
            )

            self.assertIsNone(
                stem_cache.load_cached_stems(
                    audio,
                    stem_dir,
                    allowed_sources={"moises"},
                )
            )


if __name__ == "__main__":
    unittest.main()
