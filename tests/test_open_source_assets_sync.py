from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools import open_source_assets_sync


class OpenSourceAssetsSyncTests(unittest.TestCase):
    def test_classify_repo_enforces_license_policy(self) -> None:
        permissive = {"license": {"spdx_id": "MIT"}}
        blocked = {"license": {"spdx_id": "NOASSERTION"}}
        copyleft = {"license": {"spdx_id": "GPL-3.0"}}

        allow = open_source_assets_sync.classify_repo(permissive, include_copyleft=False)
        self.assertTrue(allow.allowed_for_download)
        self.assertEqual(allow.mode, "allowed")

        deny = open_source_assets_sync.classify_repo(blocked, include_copyleft=False)
        self.assertFalse(deny.allowed_for_download)
        self.assertEqual(deny.mode, "blocked")

        ref_only = open_source_assets_sync.classify_repo(copyleft, include_copyleft=False)
        self.assertFalse(ref_only.allowed_for_download)
        self.assertEqual(ref_only.mode, "reference_only")

    def test_run_sync_downloads_allowed_repo_files(self) -> None:
        fake_repo = {
            "html_url": "https://github.com/demo/repo",
            "stargazers_count": 100,
            "updated_at": "2026-01-01T00:00:00Z",
            "license": {"spdx_id": "MIT"},
        }
        fake_files = [
            {
                "path": "demo.xmodel",
                "download_url": "https://example.com/demo.xmodel",
                "size": 42,
                "sha": "abc",
                "category": "models",
                "suffix": ".xmodel",
            }
        ]

        with TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir) / "assets"

            with patch.object(open_source_assets_sync, "SEED_REPOSITORIES", ["demo/repo"]):
                with patch("tools.open_source_assets_sync._repo_metadata", return_value=fake_repo):
                    with patch("tools.open_source_assets_sync._walk_contents", return_value=fake_files):
                        with patch("tools.open_source_assets_sync._download_file") as download_mock:
                            manifest = open_source_assets_sync.run_sync(
                                output_root=output_root,
                                include_copyleft=False,
                                max_files_per_repo=10,
                                repo_limit=1,
                                token=None,
                            )

        self.assertEqual(manifest["summary"]["repo_count"], 1)
        self.assertEqual(manifest["summary"]["allowed_repo_count"], 1)
        self.assertEqual(manifest["summary"]["downloaded_file_count"], 1)
        download_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
