from __future__ import annotations

import unittest
from pathlib import Path

from src.services.evidence_retrieval import (
    EvidencePackage,
    EvidenceRecord,
    EvidenceSourceResult,
    merge_local_evidence_package,
)
from src.services.evidence_retrieval.local_vault import _extract_local_text, collect_local_evidence


FIXTURE_DIR = Path("tests/fixtures/local_vault")


class LocalVaultTest(unittest.TestCase):
    def test_pdf_docx_txt_fixture_extraction(self) -> None:
        cases = {
            "study_report.pdf": ("pdf", "Study report: clinical efficacy overview"),
            "smpc_extract.docx": ("docx", "SmPC Extract"),
            "approved_label.txt": ("txt", "Approved label text for paracetamol"),
        }
        for filename, (kind, expected) in cases.items():
            with self.subTest(filename=filename):
                data = (FIXTURE_DIR / filename).read_bytes()
                text, details = _extract_local_text(
                    {
                        "name": filename,
                        "suffix": Path(filename).suffix.lower(),
                        "bytes": data,
                        "display_path": filename,
                        "full_path": str(FIXTURE_DIR / filename),
                    }
                )
                self.assertIn(expected, text)
                self.assertEqual(details["parser"], kind)

    def test_collect_local_evidence_from_fixture_folder(self) -> None:
        result, summary = collect_local_evidence(folder_paths=[str(FIXTURE_DIR)], include_full_paths=False)

        self.assertEqual(result.source, "local")
        self.assertEqual(result.status, "found")
        self.assertGreaterEqual(result.count, 6)
        self.assertIn("study_report.pdf", summary["file_names"])
        self.assertIn("smpc_extract.docx", summary["file_names"])
        self.assertIn("approved_label.txt", summary["file_names"])
        self.assertGreater(summary["word_count"], 0)
        self.assertTrue(all(not item.get("full_source_path") for item in summary["extraction_details"] if isinstance(item, dict)))

    def test_merge_local_evidence_prioritizes_local_and_keeps_online_sources(self) -> None:
        local_result, local_summary = collect_local_evidence(folder_paths=[str(FIXTURE_DIR)], include_full_paths=False)
        online_package = EvidencePackage(
            molecule="Paracetamol",
            retrieved_at="2026-06-09T00:00:00+00:00",
            sources={
                "pubmed": [EvidenceRecord(source="pubmed", title="PubMed title", identifier="12345")],
                "fda": [],
                "ema": [],
                "clinicaltrials": [],
            },
            source_status={
                "pubmed": EvidenceSourceResult(source="pubmed", status="found", count=1, records=[EvidenceRecord(source="pubmed", title="PubMed title", identifier="12345")]),
            },
        )

        merged = merge_local_evidence_package(online_package, local_result, local_summary, include_local_evidence_in_references=True)

        self.assertIn("local", merged.sources)
        self.assertGreater(len(merged.sources["local"]), 0)
        self.assertTrue(merged.evidence_context.startswith("STRUCTURED EVIDENCE PACKAGE"))
        self.assertIn("[LOCAL]", merged.evidence_context)
        self.assertIn("[PUBMED]", merged.evidence_context)
        self.assertLess(merged.evidence_context.index("[LOCAL]"), merged.evidence_context.index("[PUBMED]"))
        self.assertIn("Local Evidence:", merged.evidence_references)


if __name__ == "__main__":
    unittest.main()
