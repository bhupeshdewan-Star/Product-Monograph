from __future__ import annotations

import unittest
from unittest.mock import patch

from src.agents.a11y.rendered import run_rendered_accessibility_review


class RenderedA11yTest(unittest.TestCase):
    def test_rendered_accessibility_review_gracefully_handles_missing_playwright(self) -> None:
        with patch("src.agents.a11y.rendered.playwright_available", return_value=False):
            result = run_rendered_accessibility_review("https://example.com")

        self.assertFalse(result["success"])
        self.assertFalse(result["playwright_available"])
        self.assertIn("Playwright is not installed", result["summary"])
        self.assertIn("coverage_notes", result)

    def test_rendered_accessibility_review_rejects_invalid_inline_url(self) -> None:
        with patch("src.agents.a11y.rendered.playwright_available", return_value=True):
            result = run_rendered_accessibility_review("inline://rendered")

        self.assertFalse(result["success"])
        self.assertIn("http(s) URL or inline HTML", result["summary"])
        self.assertNotIn("Page.goto", result["summary"])


if __name__ == "__main__":
    unittest.main()
