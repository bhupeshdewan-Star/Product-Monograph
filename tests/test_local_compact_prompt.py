from __future__ import annotations

import unittest

from src.monograph.generator import ProductMonographGenerator
from src.monograph.prompts import build_executive_summary_prompt, build_section_prompt


class LocalCompactPromptTests(unittest.TestCase):
    def test_local_compact_section_prompt_uses_compact_summary_not_full_evidence_json(self) -> None:
        research_sources = {
            "total_articles": 4,
            "sources": {
                "local": [{"title": "Approved label", "identifier": "label.pdf"}],
                "pubmed": [{"title": "Trial A", "identifier": "PMID:123"}],
            },
            "evidence_context": "LOCAL SUMMARY\nPUBMED SUMMARY",
            "evidence_package": {"sources": {"local": [], "pubmed": []}},
            "retrieved_with": {
                "local_compact_prompt_mode": True,
                "local_section_generation_mode": True,
                "local_compact_evidence_chars": 6000,
            },
        }
        prompt = build_section_prompt(
            molecule_name="Paracetamol",
            section_name="introduction",
            section_spec={"title": "Introduction"},
            research_sources=research_sources,
            sop_constraints="Constraints",
        )
        self.assertIn("COMPACT EVIDENCE SUMMARY", prompt)
        self.assertIn("local model first draft", prompt.lower())
        self.assertNotIn("EVIDENCE PACKAGE:", prompt)

    def test_local_compact_executive_summary_prompt_is_shorter(self) -> None:
        research_sources = {
            "total_articles": 4,
            "evidence_context": "X" * 5000,
            "formatted_text": "X" * 5000,
            "retrieved_with": {
                "local_compact_prompt_mode": True,
                "local_compact_evidence_chars": 6000,
            },
        }
        prompt = build_executive_summary_prompt("Paracetamol", "Medical Affairs", research_sources)
        self.assertIn("compact evidence summary", prompt.lower())
        self.assertNotIn("raw JSON", prompt)

    def test_local_section_generation_order_prioritizes_core_sections(self) -> None:
        order = ProductMonographGenerator._section_generation_order(True)
        self.assertGreaterEqual(order.index("introduction"), 0)
        self.assertLess(order.index("introduction"), order.index("clinical_efficacy"))
        self.assertLess(order.index("pharmacology"), order.index("clinical_efficacy"))
        self.assertLess(order.index("pharmacokinetics"), order.index("clinical_efficacy"))
        self.assertLess(order.index("safety"), order.index("clinical_efficacy"))
        self.assertLess(order.index("dosage"), order.index("clinical_efficacy"))


if __name__ == "__main__":
    unittest.main()
