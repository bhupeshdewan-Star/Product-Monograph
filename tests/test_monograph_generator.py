from __future__ import annotations

import unittest

from src.monograph.generator import synthesis_engine


class MonographGeneratorTest(unittest.TestCase):
    def test_generate_monograph_structure(self) -> None:
        for molecule in ("Paracetamol", "Teriparatide"):
            with self.subTest(molecule=molecule):
                sources = {
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

                monograph = synthesis_engine.generate_monograph(molecule, sources)

                self.assertEqual(monograph["molecule_name"], molecule)
                self.assertIn("introduction", monograph["sections"])
                self.assertIn("references", monograph["sections"])
                self.assertGreater(monograph["total_tokens_used"], 0)
                self.assertIn("quality_scores", monograph)


if __name__ == "__main__":
    unittest.main()
