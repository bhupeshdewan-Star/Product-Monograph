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


if __name__ == "__main__":
    unittest.main()
