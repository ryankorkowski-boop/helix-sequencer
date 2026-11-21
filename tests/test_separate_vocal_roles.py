"""Fast Phoneme Test Hook checks for the optional RoFormer adapter."""
import importlib.util
import json
import math
from pathlib import Path
import struct
import wave

import pytest


def load_adapter():
    path = Path(__file__).resolve().parents[1] / "tools" / "separate_vocal_roles.py"
    spec = importlib.util.spec_from_file_location("separate_vocal_roles", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wav(path, hz):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(8000)
        samples = [int(12000 * math.sin(2 * math.pi * hz * i / 8000)) for i in range(8000)]
        out.writeframes(struct.pack("<" + "h" * len(samples), *samples))


def test_roformer_adapter_writes_source_bound_manifest(tmp_path):
    adapter = load_adapter()
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source-audio")
    lead, backing = tmp_path / "lead.wav", tmp_path / "backing.wav"
    wav(lead, 180)
    wav(backing, 310)
    manifest = adapter.write_manifest(source, lead, backing, tmp_path / "roles.json")
    data = json.loads(manifest.read_text())
    assert data["model"] == adapter.MODEL
    assert data["identity_evidence"] == "unverified_roles_not_individual_singer_identity"
    assert data["lead"]["path"] == "lead.wav"
    assert data["backing"]["path"] == "backing.wav"


def test_roformer_adapter_rejects_duplicate_voice(tmp_path):
    adapter = load_adapter()
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source-audio")
    lead, backing = tmp_path / "lead.wav", tmp_path / "backing.wav"
    wav(lead, 180)
    backing.write_bytes(lead.read_bytes())
    with pytest.raises(ValueError, match="identical|Duplicate|near-identical"):
        adapter.write_manifest(source, lead, backing, tmp_path / "roles.json")
