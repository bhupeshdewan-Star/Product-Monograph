from __future__ import annotations

import unittest

import app


class FrontendRenderStateTest(unittest.TestCase):
    def test_generated_monograph_state_uses_renderer_key(self) -> None:
        monograph = {
            "molecule_name": "Paracetamol",
            "sections": {"indications": "Sample section content."},
        }
        generation_sources = {"summary": {"total_records": 3}}
        evidence_package = {"summary": {"total_records": 3}}

        state = app._generated_monograph_state(monograph, generation_sources, evidence_package)

        self.assertIn("generated_monograph", state)
        self.assertIs(state["generated_monograph"], monograph)
        self.assertIs(state["generated_sources"], generation_sources)
        self.assertEqual(state["evidence_package"], evidence_package)
        self.assertIsNone(state["last_generation_error"])

    def test_render_gate_accepts_simulated_generated_result(self) -> None:
        monograph = {
            "molecule_name": "Metformin",
            "sections": {
                "indications": "Sample section content.",
                "warnings": "Sample warning content.",
            },
        }

        self.assertTrue(app._has_renderable_monograph(monograph))

    def test_export_buttons_path_is_reachable(self) -> None:
        exports = {
            "json": "D:/tmp/metformin.json",
            "markdown": "D:/tmp/metformin.md",
        }

        self.assertTrue(app._has_export_downloads(exports))


if __name__ == "__main__":
    unittest.main()
