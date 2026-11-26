from pathlib import Path
import struct
import tempfile
import unittest

from core.beat_grid import BeatGrid, generate_beat_grid, snap_placement_range
from tools.verify_native_xlights_gate import inspect_fseq


class LiveBeatGridTests(unittest.TestCase):
    def test_shifts_duration_preserving_inside_section(self):
        grid = BeatGrid(bpm=120, subdivision=4, mode="strict")
        points = generate_beat_grid(grid, 2000)
        self.assertEqual(snap_placement_range(460, 540, points, grid, lower_ms=400, upper_ms=800), (500, 580))
        self.assertEqual(snap_placement_range(460, 540, points, grid, lower_ms=400, upper_ms=550), (460, 540))
        self.assertEqual(snap_placement_range(510, 600, points, grid, lower_ms=505, upper_ms=800), (510, 600))
        self.assertEqual(snap_placement_range(460, 540, points, grid, lower_ms=400, upper_ms=800, anchored=True), (460, 540))

    def test_musical_limit(self):
        grid = BeatGrid(bpm=120, subdivision=4, max_shift_ms=20)
        points = generate_beat_grid(grid, 2000)
        self.assertEqual(snap_placement_range(460, 540, points, grid, lower_ms=0, upper_ms=2000), (460, 540))

    def test_native_frame_header_requires_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.fseq"
            header = struct.pack("<4sHBBHIIBB", b"PSEQ", 20, 0, 1, 20, 12, 4, 50, 0)
            path.write_bytes(header)
            with self.assertRaises(ValueError):
                inspect_fseq(path)
            path.write_bytes(header + bytes(48))
            with self.assertRaisesRegex(ValueError, "no active channels"):
                inspect_fseq(path)
            path.write_bytes(header + b"\x01" + bytes(47))
            self.assertEqual(inspect_fseq(path), {"channels": 12, "frames": 4, "step_ms": 50, "active_frames": 1})


if __name__ == "__main__":
    unittest.main()
