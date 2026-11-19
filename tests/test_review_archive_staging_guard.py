import zipfile
from tools.render_approval_collection import review_archive


def test_archive_excludes_interrupted_transfer_and_encoder_copies(tmp_path):
    folder=tmp_path/'review';folder.mkdir()
    (folder/'verified.mp4').write_bytes(b'verified final bytes')
    (folder/'.verified.mp4.transfer-copy').write_bytes(b'incomplete movie')
    staging=folder/'.staging';staging.mkdir();(staging/'movie.mp4').write_bytes(b'partial')
    (folder/'README.md').write_text('Actual review inventory')
    path=review_archive(folder)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist())==['review/README.md','review/verified.mp4']
        assert archive.read('review/verified.mp4')==b'verified final bytes'
