from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from music.midi_import import import_midi


def _vlq(value: int) -> bytes:
    parts = [value & 0x7F]
    value >>= 7
    while value:
        parts.insert(0, 0x80 | (value & 0x7F))
        value >>= 7
    return bytes(parts)


class MidiImportTests(unittest.TestCase):
    def test_import_midi_reads_note_events(self) -> None:
        track = b"".join(
            [
                _vlq(0),
                b"\xff\x51\x03\x07\xa1\x20",
                _vlq(0),
                bytes([0x90, 60, 100]),
                _vlq(480),
                bytes([0x80, 60, 0]),
                _vlq(0),
                b"\xff\x2f\x00",
            ]
        )
        data = b"".join(
            [
                b"MThd",
                (6).to_bytes(4, "big"),
                (0).to_bytes(2, "big"),
                (1).to_bytes(2, "big"),
                (480).to_bytes(2, "big"),
                b"MTrk",
                len(track).to_bytes(4, "big"),
                track,
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one_note.mid"
            path.write_bytes(data)
            result = import_midi(path)
        self.assertEqual(result.ticks_per_quarter, 480)
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].pitch, 60)
        self.assertAlmostEqual(result.events[0].end - result.events[0].start, 0.5, places=3)
        self.assertAlmostEqual(result.events[0].velocity, 100 / 127.0, places=4)


if __name__ == "__main__":
    unittest.main()
