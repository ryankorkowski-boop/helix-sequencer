import json
import unittest
from pathlib import Path
from tools.select_starred_music import candidates, select, DEFAULT_CATALOG


class StarredSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(DEFAULT_CATALOG.read_text(encoding="utf-8"))

    def test_catalog_has_verified_drive_ids(self):
        self.assertEqual(len(candidates(self.catalog)), 30)

    def test_rotation_is_deterministic(self):
        a = select(self.catalog, rotation=0)
        b = select(self.catalog, rotation=30)
        self.assertEqual(a["id"], b["id"])

    def test_skip_used_sources(self):
        first = select(self.catalog)
        self.assertNotEqual(first["id"], select(self.catalog, used_ids={first["id"]})["id"])

    def test_explicit_source_overrides_rotation(self):
        first = select(self.catalog)
        self.assertEqual(select(self.catalog, requested_id=first["id"], rotation=9), first)

    def test_unknown_source_fails_closed(self):
        with self.assertRaises(ValueError):
            select(self.catalog, requested_id="unknown")

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            candidates({"files": [self.catalog["files"][0]] * 2})


if __name__ == "__main__":
    unittest.main()
