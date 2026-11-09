import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools import native_renderer_bundle as bundles
from tools.patch_xlights_native_export import PATCHES


class NativeRendererBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "build"
        self.source.mkdir()
        self.patch = self.base / "patch.py"
        self.patch.write_text("exact pinned patch\n")
        files = {
            "bin/xLights": "fake compiled payload for archive tests\n",
            "wxWidgets-xlights_2026.17c/lib/libwx_gtk3u-3.3.so.4.0.0": "wx test payload",
        }
        files.update({path: "\n".join(after for _, after in sites) for path, sites in PATCHES.items()})
        for relative, content in files.items():
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        (self.source / "bin/xLights").chmod(0o755)
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        subprocess.run(["git", "-C", str(self.source), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.source), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.test", "commit", "-qm", "fixture"], check=True)
        revision = subprocess.check_output(
            ["git", "-C", str(self.source), "rev-parse", "HEAD"], text=True).strip()
        mock = patch.object(bundles, "UPSTREAM_COMMIT", revision)
        mock.start()
        self.addCleanup(mock.stop)
        self.bundle = self.base / "bundle"
        self.destination = self.base / "restored"

    def pack(self):
        return bundles.pack(self.source, self.bundle, self.patch)

    def test_roundtrip_preserves_executable_wx_git_and_existing_cache(self):
        manifest = self.pack()
        self.destination.mkdir()
        (self.destination / "old-object").write_text("old")
        self.assertEqual(bundles.restore(self.bundle, self.destination, self.patch), manifest)
        self.assertFalse((self.destination / "old-object").exists())
        bundles.validate_tree(self.destination)
        self.assertEqual(bundles.digest(self.destination / "bin/xLights"), manifest["binary_sha256"])

    def test_other_patch_is_rejected_before_replacing_existing_cache(self):
        self.pack()
        self.patch.write_text("different patch")
        self.destination.mkdir()
        (self.destination / "keep").write_text("useful cache")
        with self.assertRaisesRegex(ValueError, "identity"):
            bundles.restore(self.bundle, self.destination, self.patch)
        self.assertEqual((self.destination / "keep").read_text(), "useful cache")

    def test_damaged_archive_is_rejected(self):
        self.pack()
        with (self.bundle / "renderer.tar.gz").open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaisesRegex(ValueError, "archive checksum"):
            bundles.restore(self.bundle, self.destination, self.patch)
        self.assertFalse(self.destination.exists())

    def test_wrong_binary_checksum_rejected_after_safe_extraction(self):
        manifest = self.pack()
        manifest["binary_sha256"] = "0" * 64
        (self.bundle / "renderer.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "renderer checksum"):
            bundles.restore(self.bundle, self.destination, self.patch)
        self.assertFalse(self.destination.exists())

    def test_wrong_platform_or_upstream_rejected(self):
        original = self.pack()
        for key in ("platform", "upstream_commit", "schema"):
            with self.subTest(key=key):
                manifest = dict(original, **{key: "other"})
                (self.bundle / "renderer.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "identity"):
                    bundles.restore(self.bundle, self.destination, self.patch)

    def test_pack_refuses_missing_wx_unpatched_source_and_incomplete_binary(self):
        for relative in ("wxWidgets-xlights_2026.17c/lib/libwx_gtk3u-3.3.so.4.0.0",
                         "src-ui-wx/xLightsMain.cpp", "bin/xLights"):
            target = self.source / relative
            data = target.read_bytes()
            target.unlink()
            with self.subTest(relative=relative), self.assertRaises((ValueError, FileNotFoundError)):
                self.pack()
            target.write_bytes(data)
            if relative == "bin/xLights":
                target.chmod(0o755)

    def test_archive_traversal_and_external_symlinks_are_rejected(self):
        manifest = self.pack()
        archive = self.bundle / "renderer.tar.gz"
        for name, link in (("xlights-src/../../escape", None),
                           ("xlights-src/link", "/tmp/escape")):
            with self.subTest(name=name):
                with tarfile.open(archive, "w:gz") as output:
                    member = tarfile.TarInfo(name)
                    if link:
                        member.type, member.linkname = tarfile.SYMTYPE, link
                        output.addfile(member)
                    else:
                        member.size = 4
                        output.addfile(member, io.BytesIO(b"oops"))
                manifest["archive_sha256"] = bundles.digest(archive)
                (self.bundle / "renderer.json").write_text(json.dumps(manifest))
                with self.assertRaises((ValueError, tarfile.FilterError)):
                    bundles.restore(self.bundle, self.destination, self.patch)
                self.assertFalse(self.destination.exists())

    def test_bundle_name_changes_with_patch_and_cannot_pack_inside_tree(self):
        name = bundles.artifact_name(self.patch)
        self.assertTrue(name.endswith(hashlib.sha256(self.patch.read_bytes()).hexdigest()))
        self.patch.write_text("next patch")
        self.assertNotEqual(name, bundles.artifact_name(self.patch))
        with self.assertRaisesRegex(ValueError, "outside"):
            bundles.pack(self.source, self.source / "bundle", self.patch)


if __name__ == "__main__":
    unittest.main()
