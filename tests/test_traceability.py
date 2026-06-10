from __future__ import annotations

from unittest.mock import Mock, patch

import unittest

from src.agents.providers.base import ProviderConfig
from src.agents.providers.openai_provider import OpenAIProvider
from src.monograph.sop_engine import sop_engine
from src.monograph.generation_config import resolve_generation_config
from src.services.evidence_retrieval.traceability import (
    annotate_section_with_traceability,
    apply_section_traceability,
    build_traceability_appendix,
)


class TraceabilityTest(unittest.TestCase):
    def test_local_mode_sets_completion_tokens(self) -> None:
        cfg = resolve_generation_config(
            mode="local",
            provider_choice="openai",
            model="gemma4:e4b-it-qat",
            base_url="http://localhost:11434/v1",
        )

        self.assertEqual(cfg.max_completion_tokens, 256)
        provider_cfg = cfg.to_provider_config()
        self.assertIsNotNone(provider_cfg)
        self.assertEqual(provider_cfg.max_completion_tokens, 256)

    def test_openai_local_payload_includes_completion_tokens(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with patch("src.agents.providers.base.requests.post", return_value=response) as mock_post:
            provider = OpenAIProvider(base_url="http://localhost:11434/v1")
            provider.generate(
                prompt="prompt",
                system_prompt="system",
                model="gemma4:e4b-it-qat",
                api_key=None,
                temperature=0.2,
                max_completion_tokens=256,
            )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["max_tokens"], 256)
        self.assertEqual(payload["max_completion_tokens"], 256)

    def test_validation_fails_when_scientific_claim_lacks_source(self) -> None:
        content = (
            "This contraindication narrative explains renal impairment, interaction risk, and patient review. "
            "The draft should be reviewed carefully because the clinical decision depends on source-verified safety limits. "
            "Older adults with unstable kidney function need careful monitoring and cautious escalation."
        )
        is_valid, validation = sop_engine.validate_section("contraindications", content)

        self.assertFalse(is_valid)
        self.assertTrue(any("source identifiers" in issue.lower() for issue in validation["issues"]))

    def test_validation_passes_with_source_markers(self) -> None:
        content = (
            "This contraindication narrative explains renal impairment, interaction risk, and patient review [PMID:12345]. "
            "The draft should be reviewed carefully because the clinical decision depends on source-verified safety limits [FDA:metformin|section=contraindications]. "
            "Older adults with unstable kidney function need careful monitoring and cautious escalation [NCT01234567]."
        )
        while len(content.split()) < 110:
            content += " Additional source-verified clinical context remains documented [PMID:12345]."

        is_valid, validation = sop_engine.validate_section("contraindications", content)

        self.assertTrue(is_valid)
        self.assertTrue(validation["checks"].get("source_traceability"))

    def test_traceability_appendix_and_annotations(self) -> None:
        evidence_package = {
            "retrieved_at": "2026-06-09T10:00:00+00:00",
            "sources": {
                "pubmed": [
                    {"identifier": "12345", "title": "Evidence title", "source": "pubmed"},
                ],
                "fda": [
                    {
                        "identifier": "metformin",
                        "title": "FDA label for metformin",
                        "metadata": {"sections": ["contraindications", "dosage_and_administration"]},
                    }
                ],
                "ema": [],
                "clinicaltrials": [
                    {"identifier": "NCT01234567", "title": "Trial title", "source": "clinicaltrials"},
                ],
            },
        }

        annotated_sections, rows, retrieved_at = apply_section_traceability(
            {
                "contraindications": (
                    "The narrative explains renal impairment, interaction risk, and monitoring needs. "
                    "Clinical decisions should be verified before publication."
                ),
                "references": "## References\n1. Example",
            },
            evidence_package,
        )

        self.assertIn("PMID:12345", annotated_sections["contraindications"])
        self.assertTrue(rows)
        appendix = build_traceability_appendix(rows, retrieved_at)
        self.assertIn("Claim | Source | Database | Retrieval date", appendix)
        self.assertIn("PubMed", appendix)
        self.assertIn("FDA", appendix)
        self.assertIn("ClinicalTrials.gov", appendix)

    def test_sentence_annotation_adds_markers(self) -> None:
        annotated, rows = annotate_section_with_traceability(
            "This clinical claim needs support. Another scientific claim needs support.",
            ["PMID:12345", "FDA:metformin|section=dosage_and_administration"],
        )
        self.assertIn("PMID:12345", annotated)
        self.assertGreaterEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
