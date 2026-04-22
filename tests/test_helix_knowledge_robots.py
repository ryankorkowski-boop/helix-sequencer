from __future__ import annotations

import unittest
from unittest.mock import patch

from helix_knowledge.safety.robots_checker import RobotsChecker


class _FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class RobotsCheckerTests(unittest.TestCase):
    def test_allows_when_robots_allows_path(self) -> None:
        checker = RobotsChecker(user_agent="HelixBot")
        robots_text = "User-agent: *\nAllow: /\n"

        with patch("helix_knowledge.safety.robots_checker.requests.get", return_value=_FakeResponse(200, robots_text)):
            decision = checker.is_allowed("https://example.com/docs/page")

        self.assertTrue(decision.allowed)
        self.assertIn("allowed", decision.reason)

    def test_denies_when_robots_disallows_path(self) -> None:
        checker = RobotsChecker(user_agent="HelixBot")
        robots_text = "User-agent: *\nDisallow: /private\n"

        with patch("helix_knowledge.safety.robots_checker.requests.get", return_value=_FakeResponse(200, robots_text)):
            decision = checker.is_allowed("https://example.com/private/thread")

        self.assertFalse(decision.allowed)
        self.assertIn("disallowed", decision.reason)


if __name__ == "__main__":
    unittest.main()
