from __future__ import annotations

import json
import unittest
from pathlib import Path

from core import effect_engine
from core import engine_profiles
from core import sequence_builder
from core.run_config import RunConfig
from core.run_manager import RunManager


class SequenceBuilderTests(unittest.TestCase):
    def test_available_profiles_only_exposes_master(self) -> None:
        profiles = sequence_builder.available_profiles()
        self.assertEqual([profile.profile_id for profile in profiles], ["master"])

    def test_master_profile_tracks_active_style_version(self) -> None:
        profile = engine_profiles.resolve_profile("master")
        self.assertEqual(profile.version, effect_engine.ACTIVE_STYLE_VERSION)
        self.assertFalse(profile.legacy)

    def test_legacy_version_can_still_resolve_explicitly(self) -> None:
        profile = engine_profiles.resolve_profile("v27.3")
        self.assertEqual(profile.version, "v27.3")

    def test_artifact_search_roots_include_engine_default_family(self) -> None:
        roots = sequence_builder._artifact_search_roots(RunConfig(output_root=Path("outputs")), "v27.3")

        self.assertEqual(roots, [Path("outputs"), Path("v27")])

    def test_record_changed_artifacts_adds_known_outputs_to_manifest_file(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "outputs"
            config = RunConfig(output_root=output_root)
            ctx = RunManager(config).start(command=["python", "main.py"], require_existing=False)
            before = sequence_builder._snapshot_known_artifacts([output_root])

            xsq = output_root / "song,v27.3.xsq"
            report = output_root / "song,v27.3.report.json"
            notes = output_root / "song,v27.3.sequence_notes.txt"
            ignored = output_root / "song.tmp"
            output_root.mkdir(parents=True, exist_ok=True)
            xsq.write_text("<xsequence />", encoding="utf-8")
            report.write_text("{}", encoding="utf-8")
            notes.write_text("notes", encoding="utf-8")
            ignored.write_text("ignored", encoding="utf-8")

            sequence_builder._record_changed_artifacts(ctx, [output_root], before)

            manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
            artifacts = {(item["kind"], Path(item["path"]).name) for item in manifest["artifacts"]}
            self.assertEqual(
                artifacts,
                {
                    ("xsq", xsq.name),
                    ("report", report.name),
                    ("sequence_notes", notes.name),
                },
            )

    def test_record_changed_artifacts_ignores_unchanged_known_outputs(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "outputs"
            output_root.mkdir(parents=True, exist_ok=True)
            existing = output_root / "song,v27.3.report.json"
            existing.write_text("{}", encoding="utf-8")
            config = RunConfig(output_root=output_root)
            ctx = RunManager(config).start(command=["python", "main.py"], require_existing=False)
            before = sequence_builder._snapshot_known_artifacts([output_root])

            sequence_builder._record_changed_artifacts(ctx, [output_root], before)

            manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["artifacts"], [])


if __name__ == "__main__":
    unittest.main()
