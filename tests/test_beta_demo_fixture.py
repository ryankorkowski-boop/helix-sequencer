from __future__ import annotations

import importlib.util
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "beta_demo"


def _load_audio_generator():
    module_path = FIXTURE_DIR / "generate_synthetic_audio.py"
    spec = importlib.util.spec_from_file_location(
        "beta_demo_audio_generator",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_beta_demo_fixture_files_exist() -> None:
    expected_files = {
        "README.md",
        "generate_synthetic_audio.py",
        "minimal_layout.xml",
        "minimal_template.xsq",
    }

    for file_name in expected_files:
        assert (FIXTURE_DIR / file_name).is_file(), file_name


def test_beta_demo_xml_fixtures_are_parseable() -> None:
    for file_name in ("minimal_layout.xml", "minimal_template.xsq"):
        tree = ET.parse(FIXTURE_DIR / file_name)
        assert tree.getroot().tag


def test_synthetic_audio_generator_writes_valid_wav(tmp_path: Path) -> None:
    generator = _load_audio_generator()
    output_path = tmp_path / "synthetic_tone.wav"

    generated_path = generator.generate_wav(output_path)

    assert generated_path == output_path
    assert output_path.is_file()
    assert output_path.stat().st_size > 44

    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == generator.DEFAULT_SAMPLE_RATE
        assert wav_file.getnframes() > 0


def test_beta_demo_readme_mentions_clean_room_scope() -> None:
    readme = (FIXTURE_DIR / "README.md").read_text(encoding="utf-8").lower()

    required_terms = [
        "clean-room",
        "synthetic",
        "scope",
        "asset policy",
    ]

    for term in required_terms:
        assert term in readme
