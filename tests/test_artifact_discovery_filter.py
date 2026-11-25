from pathlib import Path

from core.sequence_builder import _known_artifact_paths, _snapshot_known_artifacts


def test_artifact_discovery_filters_names_before_stat(tmp_path, monkeypatch):
    seq = tmp_path / "fresh.xsq"
    seq.write_text("<xsequence/>")
    other = tmp_path / "unrelated.mp3"
    other.write_bytes(b"irrelevant")
    nested = tmp_path / "nested"
    nested.mkdir()
    report = nested / "show.report.json"
    report.write_text("{}")
    directory = tmp_path / "not_a_file.xsq"
    directory.mkdir()
    original = Path.is_file
    inspected = []

    def tracked(path):
        inspected.append(path)
        return original(path)

    monkeypatch.setattr(Path, "is_file", tracked)
    assert _known_artifact_paths([tmp_path]) == sorted([seq, report], key=str)
    assert other not in inspected
    assert directory in inspected


def test_artifact_snapshot_still_detects_changed_existing_file(tmp_path):
    seq = tmp_path / "sequence.xsq"
    seq.write_text("<xsequence/>")
    before = _snapshot_known_artifacts([tmp_path])
    seq.write_text("<xsequence><head/></xsequence>")
    after = _snapshot_known_artifacts([tmp_path])
    assert before.keys() == after.keys() == {seq.resolve()}
    assert before[seq.resolve()] != after[seq.resolve()]
