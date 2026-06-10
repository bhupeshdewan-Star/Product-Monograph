from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from src.agents.providers.base import ProviderConfig
from src.monograph.generator import synthesis_engine
from src.services.evidence_retrieval.cache import EvidenceCache
from src.services.evidence_retrieval.clinicaltrials_client import ClinicalTrialsClient
from src.services.evidence_retrieval.ema_client import EMAClient
from src.services.evidence_retrieval.fda_client import FDAClient
from src.services.evidence_retrieval.normalizer import build_vancouver_references, normalize_evidence_package
from src.services.evidence_retrieval.orchestrator import EvidenceRetrievalOrchestrator
from src.services.evidence_retrieval.pubmed_client import PubMedClient
from src.services.evidence_retrieval.schemas import EvidenceRecord, EvidenceSourceResult


class EvidenceRetrievalTest(unittest.TestCase):
    def test_pubmed_client_parsing_with_mocked_response(self) -> None:
        esearch = Mock()
        esearch.raise_for_status.return_value = None
        esearch.json.return_value = {"esearchresult": {"idlist": ["12345"]}}

        esummary = Mock()
        esummary.raise_for_status.return_value = None
        esummary.json.return_value = {
            "result": {
                "12345": {
                    "title": "Paracetamol clinical trial",
                    "source": "Journal of Medicine",
                    "pubdate": "2024 Jan",
                    "authors": [{"name": "Doe J"}],
                    "articleids": [{"idtype": "doi", "value": "10.1000/pmid"}],
                }
            }
        }

        efetch = Mock()
        efetch.raise_for_status.return_value = None
        efetch.text = """
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation><PMID>12345</PMID></MedlineCitation>
            <Article>
              <Abstract>
                <AbstractText>First sentence.</AbstractText>
                <AbstractText>Second sentence.</AbstractText>
              </Abstract>
            </Article>
          </PubmedArticle>
        </PubmedArticleSet>
        """

        with patch(
            "src.services.evidence_retrieval.pubmed_client.requests.get",
            side_effect=[esearch, esummary, efetch],
        ):
            result = PubMedClient(timeout=5).fetch("Paracetamol", max_results=5)

        self.assertEqual(result.status, "found")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.records[0].identifier, "12345")
        self.assertIn("First sentence", result.records[0].abstract)
        self.assertEqual(result.records[0].doi, "10.1000/pmid")

    def test_fda_client_parsing_with_mocked_response(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "results": [
                {
                    "openfda": {
                        "generic_name": ["paracetamol"],
                        "brand_name": ["BrandX"],
                    },
                    "indications_and_usage": ["For pain relief."],
                    "warnings": ["Hepatotoxicity risk."],
                    "contraindications": ["Severe liver disease."],
                    "dosage_and_administration": ["500 mg every 6 hours."],
                    "adverse_reactions": ["Nausea."],
                    "drug_interactions": ["Alcohol."],
                    "clinical_pharmacology": ["Analgesic and antipyretic."],
                    "effective_time": "20240101",
                }
            ]
        }

        with patch("src.services.evidence_retrieval.fda_client.requests.get", return_value=response):
            result = FDAClient(timeout=5).fetch("Paracetamol", max_results=5)

        self.assertEqual(result.status, "found")
        self.assertEqual(result.count, 1)
        self.assertIn("For pain relief", result.records[0].indications)
        self.assertIn("Hepatotoxicity", result.records[0].warnings)
        self.assertIn("Alcohol", result.records[0].metadata["drug_interactions"])

    def test_clinicaltrials_client_parsing_with_mocked_response(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.url = "https://clinicaltrials.gov/api/v2/studies?query.term=Paracetamol&pageSize=5"
        response.content = b"{\"studies\": []}"
        response.json.return_value = {
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCT01234567",
                            "briefTitle": "Paracetamol efficacy study",
                            "officialTitle": "Paracetamol efficacy study official",
                        },
                        "statusModule": {
                            "overallStatus": "Completed",
                            "startDateStruct": {"date": "January 2024"},
                            "completionDateStruct": {"date": "June 2025"},
                        },
                        "designModule": {
                            "phases": ["Phase 3"],
                            "enrollmentInfo": {"count": 120},
                        },
                        "conditionsModule": {"conditions": ["Pain"]},
                        "armsInterventionsModule": {
                            "interventions": [{"name": "Paracetamol"}]
                        },
                        "outcomesModule": {
                            "primaryOutcomes": [
                                {
                                    "measure": "Pain score",
                                    "timeFrame": "6 weeks",
                                    "description": "Primary efficacy endpoint",
                                }
                            ],
                            "secondaryOutcomes": [
                                {"measure": "Safety", "description": "Adverse events"}
                            ],
                        },
                        "sponsorCollaboratorsModule": {
                            "leadSponsor": {"name": "Sample Sponsor"}
                        },
                    }
                }
            ]
        }

        with patch("src.services.evidence_retrieval.clinicaltrials_client.requests.get", return_value=response):
            result = ClinicalTrialsClient(timeout=5).fetch("Paracetamol", max_results=5)

        self.assertEqual(result.status, "found")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.records[0].identifier, "NCT01234567")
        self.assertEqual(result.records[0].title, "Paracetamol efficacy study")
        self.assertEqual(result.records[0].status, "Completed")
        self.assertEqual(result.records[0].phase, "Phase 3")
        self.assertEqual(result.records[0].conditions, ["Pain"])
        self.assertEqual(result.records[0].interventions, ["Paracetamol"])
        self.assertIn("Pain score", result.records[0].outcomes[0])
        self.assertIn("Safety", " ".join(result.records[0].outcomes))
        self.assertEqual(result.records[0].sponsor, "Sample Sponsor")
        self.assertEqual(result.records[0].enrollment, "120")
        self.assertEqual(result.records[0].start_date, "January 2024")
        self.assertEqual(result.records[0].completion_date, "June 2025")
        self.assertEqual(result.records[0].url, "https://clinicaltrials.gov/study/NCT01234567")
        self.assertEqual(result.records[0].metadata["database"], "ClinicalTrials.gov")
        self.assertEqual(result.records[0].metadata["source_section"], "protocolSection")

    def test_clinicaltrials_client_no_records_found(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.url = "https://clinicaltrials.gov/api/v2/studies?query.term=Paracetamol&pageSize=5"
        response.content = b"{\"studies\": []}"
        response.json.return_value = {"studies": []}

        with patch("src.services.evidence_retrieval.clinicaltrials_client.requests.get", return_value=response):
            result = ClinicalTrialsClient(timeout=5).fetch("Paracetamol", max_results=5)

        self.assertEqual(result.status, "empty")
        self.assertEqual(result.count, 0)
        self.assertIn("No ClinicalTrials.gov studies found", result.error)

    def test_clinicaltrials_client_service_unavailable(self) -> None:
        with patch(
            "src.services.evidence_retrieval.clinicaltrials_client.requests.get",
            side_effect=requests.exceptions.ConnectionError("down"),
        ):
            result = ClinicalTrialsClient(timeout=5).fetch("Paracetamol", max_results=5)

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.count, 0)
        self.assertIn("down", result.error)

    def test_ema_graceful_unavailable_behavior(self) -> None:
        with patch("src.services.evidence_retrieval.ema_client.requests.get", side_effect=ConnectionError("unavailable")):
            result = EMAClient(timeout=5).fetch("Paracetamol", max_results=5)

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.count, 0)
        self.assertIn("unavailable", (result.error or "").lower())

    def test_evidence_normalizer_combines_counts_and_context(self) -> None:
        results = {
            "pubmed": EvidenceSourceResult(
                source="pubmed",
                status="found",
                count=1,
                records=[EvidenceRecord(source="pubmed", title="PubMed Title", identifier="1", url="https://pubmed.ncbi.nlm.nih.gov/1/")],
            ),
            "fda": EvidenceSourceResult(source="fda", status="found", count=1, records=[EvidenceRecord(source="fda", title="FDA Label", url="https://fda.gov/")]),
            "ema": EvidenceSourceResult(source="ema", status="unavailable", error="no data"),
            "clinicaltrials": EvidenceSourceResult(source="clinicaltrials", status="empty"),
        }

        package = normalize_evidence_package("Paracetamol", results)

        self.assertEqual(package.summary.total_records, 2)
        self.assertEqual(package.summary.pubmed_count, 1)
        self.assertEqual(package.summary.fda_count, 1)
        self.assertIn("PubMed Title", package.evidence_context)
        self.assertIn("No live evidence retrieved" if package.summary.total_records == 0 else "Limitations", package.evidence_context or "Limitations")

    def test_evidence_package_passed_into_generation_prompt(self) -> None:
        evidence_sources = {
            "molecule": "Paracetamol",
            "retrieved_at": "2026-06-09T00:00:00Z",
            "sources": {
                "pubmed": [],
                "fda": [],
                "ema": [],
                "clinicaltrials": [],
                "open_access": [],
            },
            "summary": {
                "total_records": 1,
                "pubmed_count": 1,
                "fda_count": 0,
                "ema_count": 0,
                "clinicaltrials_count": 0,
            },
            "total_articles": 1,
            "limitations": [],
            "source_errors": [],
            "source_status": {},
            "cache_status": {"hit": False},
            "evidence_context": "STRUCTURED EVIDENCE PACKAGE\nPubMed Title: Example evidence",
            "evidence_references": "1. Example reference.",
        }
        provider_cfg = ProviderConfig(
            provider="openai",
            model="gpt-4o-mini",
            api_key="runtime-key",
            base_url="https://api.openai.com/v1",
            strict=False,
        )

        class CapturingProvider:
            def __init__(self) -> None:
                self.calls = []

            def generate(self, *args, **kwargs):
                self.calls.append(kwargs)
                return "generated section"

        capturing = CapturingProvider()
        with patch("src.monograph.generator.create_provider", return_value=capturing):
            synthesis_engine.generate_monograph("Paracetamol", evidence_sources, provider_cfg)

        self.assertTrue(capturing.calls)
        self.assertTrue(any("STRUCTURED EVIDENCE PACKAGE" in call["prompt"] for call in capturing.calls))

    def test_local_model_mode_receives_evidence_context(self) -> None:
        evidence_sources = {
            "molecule": "Paracetamol",
            "retrieved_at": "2026-06-09T00:00:00Z",
            "sources": {
                "pubmed": [],
                "fda": [],
                "ema": [],
                "clinicaltrials": [],
                "open_access": [],
            },
            "summary": {
                "total_records": 1,
                "pubmed_count": 1,
                "fda_count": 0,
                "ema_count": 0,
                "clinicaltrials_count": 0,
            },
            "total_articles": 1,
            "limitations": [],
            "source_errors": [],
            "source_status": {},
            "cache_status": {"hit": False},
            "evidence_context": "STRUCTURED EVIDENCE PACKAGE\nClinicalTrials.gov evidence included",
            "evidence_references": "1. Example reference.",
        }
        provider_cfg = ProviderConfig(
            provider="openai",
            model="gemma4:e4b-it-qat",
            api_key=None,
            base_url="http://localhost:11434/v1",
            strict=True,
        )

        class CapturingProvider:
            def __init__(self) -> None:
                self.calls = []

            def generate(self, *args, **kwargs):
                self.calls.append(kwargs)
                return "generated section"

        capturing = CapturingProvider()
        with patch("src.monograph.generator.create_provider", return_value=capturing):
            synthesis_engine.generate_monograph("Paracetamol", evidence_sources, provider_cfg)

        self.assertTrue(capturing.calls)
        self.assertTrue(any("ClinicalTrials.gov" in call["prompt"] or "STRUCTURED EVIDENCE PACKAGE" in call["prompt"] for call in capturing.calls))

    def test_source_failure_does_not_crash_generation(self) -> None:
        class FailingClient:
            def fetch(self, *args, **kwargs):
                raise RuntimeError("PubMed unavailable")

        class SuccessClient:
            def __init__(self, source: str) -> None:
                self.source = source

            def fetch(self, molecule: str, max_results: int = 30):
                return EvidenceSourceResult(
                    source=self.source,  # type: ignore[arg-type]
                    status="found",
                    count=1,
                    records=[EvidenceRecord(source=self.source, title=f"{self.source} title", identifier=self.source.upper(), url="https://example.com")],
                )

        orchestrator = EvidenceRetrievalOrchestrator(
            cache=EvidenceCache(Path(tempfile.mkdtemp())),
            pubmed_client=FailingClient(),
            fda_client=SuccessClient("fda"),
            ema_client=SuccessClient("ema"),
            clinicaltrials_client=SuccessClient("clinicaltrials"),
        )
        package = orchestrator.retrieve_evidence("Paracetamol", max_results=5)

        self.assertEqual(package.summary.total_records, 3)
        self.assertTrue(any("PUBMED" in error for error in package.source_errors))

    def test_all_source_failure_produces_user_friendly_warning(self) -> None:
        class FailingClient:
            def fetch(self, *args, **kwargs):
                raise RuntimeError("source down")

        orchestrator = EvidenceRetrievalOrchestrator(
            cache=EvidenceCache(Path(tempfile.mkdtemp())),
            pubmed_client=FailingClient(),
            fda_client=FailingClient(),
            ema_client=FailingClient(),
            clinicaltrials_client=FailingClient(),
        )
        package = orchestrator.retrieve_evidence("Paracetamol", max_results=5)

        self.assertEqual(package.summary.total_records, 0)
        self.assertIn("No live evidence retrieved", " ".join(package.limitations))

    def test_no_fabricated_citations(self) -> None:
        package = normalize_evidence_package(
            "Paracetamol",
            {
                "pubmed": EvidenceSourceResult(
                    source="pubmed",
                    status="found",
                    count=1,
                    records=[
                        EvidenceRecord(
                            source="pubmed",
                            title="Known evidence",
                            journal="Journal",
                            year="2025",
                            identifier="12345",
                            url="https://pubmed.ncbi.nlm.nih.gov/12345/",
                        )
                    ],
                ),
                "fda": EvidenceSourceResult(source="fda", status="empty"),
                "ema": EvidenceSourceResult(source="ema", status="empty"),
                "clinicaltrials": EvidenceSourceResult(
                    source="clinicaltrials",
                    status="found",
                    count=1,
                    records=[
                        EvidenceRecord(
                            source="clinicaltrials",
                            title="Trial evidence",
                            identifier="NCT12345678",
                            url="https://clinicaltrials.gov/study/NCT12345678",
                        )
                    ],
                ),
            },
        )
        refs = build_vancouver_references(package)

        self.assertIn("PMID:12345", refs)
        self.assertIn("NCT12345678", refs)
        self.assertNotIn("No live references were retrieved", refs)
        self.assertNotIn("doi:10.0000/sample", refs)


if __name__ == "__main__":
    unittest.main()
