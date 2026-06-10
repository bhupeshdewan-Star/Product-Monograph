from __future__ import annotations

import unittest

import app


class EvidenceUiTest(unittest.TestCase):
    def test_evidence_source_issue_items_are_source_specific(self) -> None:
        evidence_package = {
            "summary": {"total_records": 0},
            "source_status": {
                "pubmed": {"status": "failed", "error": "PubMed timeout"},
                "fda": {"status": "found", "count": 2, "error": ""},
                "ema": {"status": "unavailable", "error": "EMA unavailable"},
                "clinicaltrials": {"status": "empty", "count": 0, "error": ""},
            },
        }

        issues = app._evidence_source_issue_items(evidence_package)
        labels = [item["label"] for item in issues]
        messages = {item["label"]: item["message"] for item in issues}

        self.assertEqual(labels, ["PubMed", "EMA", "ClinicalTrials.gov"])
        self.assertEqual(messages["PubMed"], "PubMed timeout")
        self.assertEqual(messages["EMA"], "EMA unavailable")
        self.assertEqual(messages["ClinicalTrials.gov"], "No matching records were found.")

    def test_available_evidence_source_labels_uses_source_status_counts(self) -> None:
        evidence_package = {
            "source_status": {
                "pubmed": {"status": "found", "count": 2},
                "fda": {"status": "unavailable", "count": 0},
                "ema": {"status": "found", "count": 1},
                "clinicaltrials": {"status": "empty", "count": 0},
            }
        }

        labels = app._available_evidence_source_labels(evidence_package)

        self.assertEqual(labels, ["✓ PubMed", "✓ EMA"])

    def test_all_sources_failed_detection_uses_total_records(self) -> None:
        evidence_package = {"summary": {"total_records": 0}}
        self.assertTrue(app._evidence_all_sources_failed(evidence_package))

    def test_discovery_warning_is_clean_in_user_mode(self) -> None:
        user_message = app._discovery_warning_to_text("network down", developer_mode=False)
        dev_message = app._discovery_warning_to_text("network down", developer_mode=True)

        self.assertIn("temporarily unavailable", user_message.lower())
        self.assertEqual(dev_message, "network down")

    def test_pending_generation_request_preserves_context(self) -> None:
        generation_config = app.GenerationConfig(
            mode="local",
            provider="openai-compatible local",
            provider_label="Local Model",
            model="gemma4:e4b",
            base_url="http://localhost:11434/v1",
            max_completion_tokens=1500,
            max_research_articles=5,
            temperature=0.2,
            local_compact_prompt_mode=True,
            local_section_generation_mode=True,
            local_compact_evidence_chars=6000,
            local_safe_prompt_tokens=2400,
            demo_mode=False,
            blocked=False,
            blocked_reason=None,
            selection_source="explicit",
            output_label="Local model draft generated using retrieved evidence package.",
            real_llm_call=True,
        )
        generation_sources = {
            "molecule": "Paracetamol",
            "retrieved_at": "2026-06-09T00:00:00Z",
            "summary": {"total_records": 1},
            "evidence_context": "STRUCTURED EVIDENCE PACKAGE",
            "evidence_references": "1. Example reference.",
        }
        evidence_package = app.EvidencePackage.model_validate(
            {
                "molecule": "Paracetamol",
                "retrieved_at": "2026-06-09T00:00:00Z",
                "sources": {},
                "summary": {"total_records": 1},
                "limitations": [],
                "source_errors": [],
                "source_status": {},
                "cache_status": {},
                "evidence_context": "STRUCTURED EVIDENCE PACKAGE",
                "evidence_references": "1. Example reference.",
                "retrieved_with": {},
            }
        )

        pending = app._build_pending_generation_request(
            molecule_name="Paracetamol",
            specialty="",
            generation_config=generation_config,
            generation_sources=generation_sources,
            evidence_package=evidence_package,
            local_evidence_result={"files_loaded": 1},
            local_evidence_summary={"file_names": ["label.pdf"], "word_count": 120},
            source_issues=[{"source": "clinicaltrials", "status": "unavailable"}],
        )
        restored = app._restore_pending_generation_request(pending)

        self.assertEqual(restored["molecule_name"], "Paracetamol")
        self.assertEqual(restored["generation_config"].model, "gemma4:e4b")
        self.assertTrue(restored["generation_config"].local_compact_prompt_mode)
        self.assertTrue(restored["generation_config"].local_section_generation_mode)
        self.assertEqual(restored["generation_sources"]["evidence_context"], "STRUCTURED EVIDENCE PACKAGE")
        self.assertEqual(restored["local_evidence_summary"]["word_count"], 120)

    def test_evidence_issue_messages_are_clean_for_user_mode(self) -> None:
        clinical_message = app._friendly_evidence_issue_message("clinicaltrials", "unavailable", "404 Client Error")
        ema_message = app._friendly_evidence_issue_message("ema", "empty", "")

        self.assertEqual(clinical_message, "ClinicalTrials.gov temporarily unavailable.")
        self.assertEqual(ema_message, "No structured EMA results were found.")


if __name__ == "__main__":
    unittest.main()
