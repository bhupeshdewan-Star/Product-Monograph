from __future__ import annotations

from types import SimpleNamespace
import unittest

from src.agents.a11y.checker import check_accessibility


class A11yCheckerTest(unittest.TestCase):
    def test_accessibility_check_returns_json(self) -> None:
        html = """
        <html>
          <head><title>Demo</title></head>
          <body>
            <main>
              <h1>Demo page</h1>
              <img src="hero.png">
              <button>Click</button>
            </main>
          </body>
        </html>
        """

        result = check_accessibility(
            "inline://demo",
            fetcher=lambda _: SimpleNamespace(html=html, final_url="inline://demo"),
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["audit_type"], "accessibility")
        self.assertIn("issues", result)
        self.assertIn("summary", result)
        self.assertIn("score", result)


if __name__ == "__main__":
    unittest.main()
