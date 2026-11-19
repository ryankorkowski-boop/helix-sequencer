import json
from pathlib import Path
import pytest
from tools.phoneme_source import EXPECTED_SHA256, FIXTURE, digest, ingest


def test_retained_original_runs_without_urls(tmp_path):
    report = ingest(tmp_path)
    assert report['status'] == 'verified'
    assert digest(Path(report['audio'])) == EXPECTED_SHA256
    assert Path(report['audio']).read_bytes() == FIXTURE.read_bytes()


def test_bad_explicit_source_does_not_fall_back_to_fixture(tmp_path):
    bad = tmp_path / 'wrong.mp3'
    bad.write_bytes(b'wrong')
    with pytest.raises(ValueError, match='mismatch'):
        ingest(tmp_path / 'out', source=bad)
    report = json.loads((tmp_path / 'out/source_ingestion.json').read_text())
    assert report['status'] == 'failed'
    assert not (tmp_path / 'out/Phoneme_Test_Hook.mp3').exists()


@pytest.mark.parametrize('url', ['http://host/audio', 'file:///song', 'https://secret:token@host/audio'])
def test_non_https_or_embedded_credentials_reject_before_transfer(tmp_path, url):
    with pytest.raises(ValueError, match='HTTPS'):
        ingest(tmp_path, url=url, token='test-secret')
    assert 'test-secret' not in (tmp_path / 'source_ingestion.json').read_text()


def test_missing_override_produces_actionable_receipt(tmp_path):
    with pytest.raises(ValueError, match='restore fixtures/audio'):
        ingest(tmp_path / 'out', source=tmp_path / 'missing.mp3')
    assert json.loads((tmp_path / 'out/source_ingestion.json').read_text())['status'] == 'failed'
