from __future__ import annotations

from core.band_vocal_face_export import BandVocalFaceExportCompiler
from core.beat_aligner import align_to_beat_grid
from core.energy_scaler import scale_section_intensity
from core.lyric_section_scheduler import schedule_lyric_section
from models.helixville4_vocal_phonemes import PHONEME_BY_NAME


def test_lyric_section_energy_beat_alignment_exports_valid_manifest() -> None:
    scheduled = schedule_lyric_section(
        performer="singer",
        lines=["Hello", "world"],
        section_start=0.0,
        section_duration=4.0,
        intensity=0.8,
    )

    scaled = scale_section_intensity(scheduled, section_energy=0.5)
    aligned = align_to_beat_grid(scaled, beat_interval=0.5, grid_division=2)
    manifest = BandVocalFaceExportCompiler().build_manifest(aligned)

    assert manifest["schema"] == "helixville4.band_vocal_face_export.v1"
    assert manifest["effect_count"] == len(aligned)
    assert manifest["performers"] == ["singer"]
    assert manifest["models"] == ["HX_SNOWMAN_SINGER"]

    approved = set(PHONEME_BY_NAME)
    for effect in manifest["effects"]:
        assert effect["phoneme"] in approved
        assert effect["start"] == round(effect["start"], 6)
        assert effect["end"] == round(effect["end"], 6)
        assert 0.0 <= effect["intensity"] <= 1.0
        assert effect["intensity"] <= 0.4
        assert effect["effect_type"] == "Faces"
        assert effect["timing_track"] == "helixville4_vocal_phonemes"
        assert effect["submodels"]


def test_vocal_pipeline_integration_is_deterministic() -> None:
    def build() -> dict:
        scheduled = schedule_lyric_section(
            performer="female_singer",
            lines=["Bright", "lights"],
            section_start=1.0,
            section_duration=6.0,
            intensity=1.0,
        )
        scaled = scale_section_intensity(scheduled, section_energy=0.75)
        aligned = align_to_beat_grid(scaled, beat_interval=0.5, grid_division=4)
        return BandVocalFaceExportCompiler().build_manifest(aligned)

    assert build() == build()
