"""Focused regression checks for XSQ timing and source-role independence."""
import tempfile
import unittest
from pathlib import Path
from tools.validate_source_events import validate


def fixture(elements):
    return "<xsequence><ElementEffects>" + elements + "</ElementEffects></xsequence>"


def model(name, effects):
    return '<Element name="' + name + '">' + effects + '</Element>'


def event(a, b, role, component="NOTE"):
    return f'<Effect startTime="{a}" endTime="{b}" sourceRole="{role}" sourceComponent="{component}"/>'


class SourceEventValidation(unittest.TestCase):
    def check(self, xml):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "show.xsq"
            path.write_text(xml)
            return validate(path)

    def test_independent_timings(self):
        report = self.check(fixture(model("keys", event(0, 50, "keyboard")) +
                                    model("bass", event(25, 75, "bass"))))
        self.assertEqual(report["identical_timing_roles"], [])
        self.assertEqual(report["events"], 2)

    def test_identical_timing_is_flagged_not_claimed_independent(self):
        report = self.check(fixture(model("keys", event(0, 50, "keyboard")) +
                                    model("bass", event(0, 50, "bass"))))
        self.assertEqual(report["identical_timing_roles"], [["keyboard", "bass"]])

    def test_duplicate_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.check(fixture(model("keys", event(0, 50, "keyboard") * 2)))

    def test_bad_interval_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid interval"):
            self.check(fixture(model("keys", event(50, 50, "keyboard"))))

    def test_missing_time_rejected(self):
        with self.assertRaisesRegex(ValueError, "noninteger"):
            self.check(fixture(model("keys", '<Effect sourceRole="keyboard"/>')))

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, "no timed"):
            self.check(fixture(""))

    def test_visual_geometry_excluded(self):
        report = self.check(fixture(model("stage", event(0, 50, "visual_geometry")) +
                                    model("keys", event(10, 60, "keyboard"))))
        self.assertEqual(report["events"], 1)


if __name__ == "__main__":
    unittest.main()
