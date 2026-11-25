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


def test_roformer_adapter_rejects_stems_outside_manifest_bundle(tmp_path):
    adapter = load_adapter()
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source-audio")
    lead, backing = tmp_path / "lead.wav", tmp_path / "backing.wav"
    wav(lead, 180)
    wav(backing, 310)
    bundle = tmp_path / "bundle"
    with pytest.raises(ValueError, match="inside the manifest directory"):
        adapter.write_manifest(source, lead, backing, bundle / "roles.json")
    assert not (bundle / "roles.json").exists()


def test_roformer_manifest_detects_original_source_mutation(tmp_path):
    adapter = load_adapter()
    from core.vocal_separation_manifest import validate_vocal_separation_manifest
    source = tmp_path / "source.mp3"
    source.write_bytes(b"original-source")
    lead, backing = tmp_path / "lead.wav", tmp_path / "backing.wav"
    wav(lead, 180)
    wav(backing, 310)
    manifest = adapter.write_manifest(source, lead, backing, tmp_path / "roles.json")
    source.write_bytes(b"changed-source")
    with pytest.raises(ValueError, match="source audio SHA256 mismatch"):
        validate_vocal_separation_manifest(manifest, source)



def test_silent_harmony_review_does_not_qualify_two_singers(tmp_path):
    import numpy as np
    from core.vocal_separation_manifest import validate_vocal_separation_manifest
    from tools.roformer_review_fixture import build
    adapter = load_adapter()
    source, lead, backing = (tmp_path / n for n in ('source.wav', 'lead.wav', 'backing.wav'))
    wav(source, 220)
    wav(lead, 180)
    wav(backing, 0)
    manifest = tmp_path / 'roles.json'
    with pytest.raises(ValueError, match='Harmony stem is silent'):
        adapter.write_manifest(source, lead, backing, manifest)
    adapter.write_manifest(source, lead, backing, manifest, allow_silent_harmony_review=True)
    with pytest.raises(ValueError, match='Unsupported vocal separation manifest schema'):
        validate_vocal_separation_manifest(manifest, source)
    output = build(source, manifest, tmp_path / 'review')
    receipt = json.loads((output / 'diagnostic.json').read_text())
    assert receipt['verification_state'] == 'ESTIMATED_REVIEW'
    assert receipt['harmony_candidate_silent'] is True
    assert receipt['independent_backing_verified'] is False
    with np.load(output / 'acoustic_vocal_clocks.npz', allow_pickle=False) as clocks:
        for key in ('energy', 'shapes', 'presence_probability'):
            assert not np.any(clocks['estimated_backing_' + key])
    backing.write_bytes(lead.read_bytes())
    with pytest.raises(ValueError, match='Duplicate|identical'):
        adapter.write_manifest(source, lead, backing, manifest, allow_silent_harmony_review=True)
