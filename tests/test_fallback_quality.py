from __future__ import annotations

import unittest

from config import SOP_SECTIONS
from src.monograph.executive_summary import executive_summary_generator
from src.monograph.generator import synthesis_engine
from src.monograph.validators import validator


def _sample_sources(molecule: str) -> dict:
    return {
        "molecule": molecule,
        "sources": {
            "pubmed": [
                {
                    "title": f"{molecule} clinical outcomes",
                    "authors": ["A. Author"],
                    "journal": "Journal of Medicine",
                    "publication_date": "2025",
                    "doi": "10.1000/example",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
                }
            ],
            "fda": [
                {
                    "drug_name": molecule,
                    "indications": "Sample indication",
                    "url": "https://www.fda.gov/",
                }
            ],
            "google_scholar": [],
            "open_access": [],
        },
        "total_articles": 2,
        "formatted_text": f"Sample source summary for {molecule}",
    }


class FallbackQualityTest(unittest.TestCase):
    def test_demo_monographs_are_section_complete(self) -> None:
        placeholders = (
            "summarize the main mechanism",
            "highlight the most relevant clinical use cases",
            "summarize key safety considerations",
            "balance benefit, safety, and operational simplicity",
        )

        for molecule in ("Teriparatide", "Paracetamol", "Ibuprofen", "Metformin"):
            with self.subTest(molecule=molecule):
                sources = _sample_sources(molecule)
                monograph = synthesis_engine.generate_monograph(molecule, sources)
                executive_summary = executive_summary_generator.generate_executive_summary(
                    molecule,
                    sources,
                    "General Practitioner",
                )

                validation_input = {"molecule_name": monograph["molecule_name"], **monograph["sections"]}
                is_valid, validation_report = validator.validate_and_score(validation_input)

                self.assertTrue(monograph["sections"]["introduction"].strip())
                self.assertGreaterEqual(
                    validation_report["overall_compliance_score"],
                    75.0,
                    msg=f"{molecule} validation score too low: {validation_report['overall_compliance_score']}",
                )
                self.assertTrue(is_valid or validation_report["overall_compliance_score"] >= 75.0)

                for section_name, spec in SOP_SECTIONS.items():
                    if section_name == "references":
                        continue
                    content = monograph["sections"][section_name]
                    if "min_words" in spec:
                        self.assertGreaterEqual(
                            len(content.split()),
                            spec["min_words"],
                            msg=f"{molecule} {section_name} below minimum words",
                        )

                self.assertIn("Level 1A", monograph["sections"]["clinical_efficacy"])
                self.assertIn("RCTs", monograph["sections"]["clinical_efficacy"])
                self.assertIn("meta-analyses", monograph["sections"]["clinical_efficacy"].lower())
                self.assertIn("%", monograph["sections"]["clinical_efficacy"])
                self.assertIn("(", monograph["sections"]["clinical_efficacy"])

                safety = monograph["sections"]["safety"].lower()
                self.assertIn("very common", safety)
                self.assertIn("common", safety)
                self.assertIn("uncommon", safety)
                self.assertIn("rare", safety)
                self.assertIn("very rare", safety)
                self.assertIn("contraindications", safety)
                self.assertIn("drug interactions", safety)

                dosage = monograph["sections"]["dosage"].lower()
                self.assertIn("recommended dose", dosage)
                self.assertIn("dosage adjustments", dosage)
                self.assertIn("administration", dosage)

                references = monograph["sections"]["references"].lower()
                self.assertIn("source record", references)
                self.assertIn("not a verified citation", references)
                self.assertNotIn("summarize the main mechanism", references)

                executive_lower = executive_summary.lower()
                for phrase in placeholders:
                    self.assertNotIn(phrase, executive_lower)
                self.assertIn("practice", executive_lower)
                self.assertIn("safety", executive_lower)


if __name__ == "__main__":
    unittest.main()
