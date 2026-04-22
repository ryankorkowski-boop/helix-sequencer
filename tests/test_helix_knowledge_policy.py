from __future__ import annotations

import unittest

from helix_knowledge.safety.source_policy import SourcePolicy


class SourcePolicyTests(unittest.TestCase):
    def test_denies_vendor_sequence_file(self) -> None:
        policy = SourcePolicy()
        decision = policy.evaluate(
            source_type="web_page",
            url="https://vendor.example.com/premium-show.xsq",
            title="Premium paid sequence",
        )
        self.assertFalse(decision.allowed)
        self.assertIn("denied", decision.reason)

    def test_denies_youtube_without_user_or_api(self) -> None:
        policy = SourcePolicy()
        decision = policy.evaluate(
            source_type="youtube_transcript",
            url="https://www.youtube.com/watch?v=abc",
            is_user_provided=False,
            via_official_api=False,
        )
        self.assertFalse(decision.allowed)
        self.assertIn("official API", decision.reason)


if __name__ == "__main__":
    unittest.main()
