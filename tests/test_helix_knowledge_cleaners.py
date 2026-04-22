from __future__ import annotations

import unittest

from helix_knowledge.parsing.html_cleaner import clean_html
from helix_knowledge.parsing.transcript_cleaner import clean_transcript


class CleanerTests(unittest.TestCase):
    def test_html_cleaner_strips_script_and_keeps_text(self) -> None:
        html = """
        <html><head><title>Test</title><script>ignore()</script></head>
        <body><h1>Timing Track Setup</h1><p>Click add timing.</p></body></html>
        """
        cleaned = clean_html(html)
        self.assertIn("Timing Track Setup", cleaned)
        self.assertIn("Click add timing", cleaned)
        self.assertNotIn("ignore()", cleaned)

    def test_transcript_cleaner_removes_timecodes(self) -> None:
        raw = "00:01 Intro\n[Music]\n00:09 Click the timing track and drag the effect."
        cleaned = clean_transcript(raw)
        self.assertNotIn("00:01", cleaned)
        self.assertNotIn("[Music]", cleaned)
        self.assertIn("drag the effect", cleaned)


if __name__ == "__main__":
    unittest.main()
