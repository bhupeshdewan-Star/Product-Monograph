from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace
import unittest

from src.agents.auditor.builder import build_audit_schema
from src.agents.auditor.runner import run_audit


class AuditorBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["GLOBAL_AGENTS_SCHEMA_DIR"] = self.tmpdir.name

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        os.environ.pop("GLOBAL_AGENTS_SCHEMA_DIR", None)

    def test_build_and_run_audit_schema(self) -> None:
        checklist_html = """
        <html>
          <head><title>Landing Page Audit Checklist</title></head>
          <body>
            <main>
              <h1>Landing Page Audit Checklist</h1>
              <ul>
                <li>Ensure alt text exists for images</li>
                <li>Use a clear heading hierarchy</li>
                <li>Maintain color contrast for readable text</li>
              </ul>
            </main>
          </body>
        </html>
        """
        target_html = """
        <html>
          <head><title>Target</title></head>
          <body>
            <main>
              <h1>Target landing page</h1>
              <img src="hero.png" alt="Hero visual">
              <p>Readable text</p>
            </main>
          </body>
        </html>
        """

        schema_result = build_audit_schema(
            "https://example.com/checklist",
            fetcher=lambda _: SimpleNamespace(html=checklist_html, final_url="https://example.com/checklist"),
        )
        self.assertTrue(schema_result["success"])
        self.assertTrue(schema_result["schema"]["criteria"])

        audit_result = run_audit(
            "https://example.com/target",
            schema_result["schema_id"],
            fetcher=lambda _: SimpleNamespace(html=target_html, final_url="https://example.com/target"),
        )
        self.assertTrue(audit_result["success"])
        self.assertEqual(audit_result["schema_id"], schema_result["schema_id"])
        self.assertIn("issues", audit_result)
        self.assertIn("summary", audit_result)


if __name__ == "__main__":
    unittest.main()
