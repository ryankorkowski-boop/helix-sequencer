"""Resolve the owner-authorized Phoneme Test Hook before installing DSP/GUI deps."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.parse
import urllib.request

EXPECTED_SHA256 = '19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938'
FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/audio/Phoneme_Test_Hook.mp3'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ingest(output: Path, *, source: Path | None = None, url: str = '', token: str = '') -> dict:
    """Explicit path/URL overrides the retained fixture; a bad override fails closed.

    Credentials never enter receipts or error text. Authorization is sent only
    to the explicitly chosen HTTPS origin, never forwarded to redirected hosts.
    """
    if source and url:
        raise ValueError('Choose an audio path or URL, not both')
    output.mkdir(parents=True, exist_ok=True)
    receipt = output / 'source_ingestion.json'
    target = output / 'Phoneme_Test_Hook.mp3'
    report = dict(schema='helix.phoneme-source.v1', status='failed', expected_sha256=EXPECTED_SHA256)
    temporary = None
    try:
        chosen = source or FIXTURE
        if url:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Audio URL must be HTTPS without embedded credentials')

            class Redirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, request, fp, code, msg, headers, newurl):
                    if urllib.parse.urlparse(newurl).scheme != 'https':
                        raise ValueError('Audio redirect must remain HTTPS')
                    redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
                    if redirected and urllib.parse.urlparse(newurl).netloc != parsed.netloc:
                        redirected.remove_header('Authorization')
                    return redirected

            request = urllib.request.Request(url)
            if token:
                request.add_header('Authorization', 'Bearer ' + token)
            fd, name = tempfile.mkstemp(dir=output, suffix='.download')
            temporary = Path(name)
            with os.fdopen(fd, 'wb') as dest, urllib.request.build_opener(Redirect()).open(request, timeout=90) as src:
                # This exact 803kB source cannot legitimately need unbounded storage.
                data = src.read(16 * 1024 * 1024 + 1)
                if len(data) > 16 * 1024 * 1024:
                    raise ValueError('Audio download exceeds source size limit')
                dest.write(data)
            chosen = temporary
        if not chosen.is_file():
            raise ValueError('Original Phoneme Test Hook MP3 missing: restore fixtures/audio/Phoneme_Test_Hook.mp3 or supply --audio / --audio-url')
        actual = digest(chosen)
        report['actual_sha256'] = actual
        if actual != EXPECTED_SHA256:
            raise ValueError('Original Phoneme Test Hook SHA256 mismatch; refusing substitute audio')
        if chosen.resolve() != target.resolve():
            shutil.copyfile(chosen, target)
        report.update(status='verified', audio=str(target.resolve()), size_bytes=target.stat().st_size,
                      source_kind='https_override' if url else 'path_override' if source else 'retained_owner_upload')
        return report
    except Exception as exc:
        # HTTP exception strings may contain signed URLs. Keep diagnostics
        # actionable without leaking them or credentials into Actions artifacts.
        report['error'] = str(exc) if isinstance(exc, ValueError) else 'Source transfer failed: ' + type(exc).__name__
        raise ValueError(report['error']) from None
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
        receipt.write_text(json.dumps(report, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--audio', type=Path)
    parser.add_argument('--audio-url', default=os.environ.get('HELIX_PHONEME_AUDIO_URL', ''))
    args = parser.parse_args()
    print(json.dumps(ingest(args.output, source=args.audio, url=args.audio_url,
                            token=os.environ.get('HELIX_PHONEME_AUDIO_TOKEN', '')), indent=2))


if __name__ == '__main__':
    main()
