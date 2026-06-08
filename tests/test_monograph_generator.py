from __future__ import annotations

import unittest

from src.monograph.generator import synthesis_engine


class MonographGeneratorTest(unittest.TestCase):
    def test_generate_monograph_structure(self) -> None:
        sources = {
            "molecule": "Metformin",
            "sources": {
                "pubmed": [
                    {
                        "title": "Metformin clinical outcomes",
                        "authors": ["A. Author"],
                        "journal": "Journal of Medicine",
                        "publication_date": "2025",
                        "doi": "10.1000/example",
                        "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
                    }
                ],
                "fda": [
                    {
                        "drug_name": "Metformin",
                        "indications": "Type 2 diabetes",
                        "url": "https://www.fda.gov/",
                    }
                ],
                "google_scholar": [],
                "open_access": [],
            },
            "total_articles": 2,
            "formatted_text": "Sample source summary for Metformin",
        }

        monograph = synthesis_engine.generate_monograph("Metformin", sources)

        self.assertEqual(monograph["molecule_name"], "Metformin")
        self.assertIn("introduction", monograph["sections"])
        self.assertIn("references", monograph["sections"])
        self.assertGreater(monograph["total_tokens_used"], 0)
        self.assertIn("quality_scores", monograph)


if __name__ == "__main__":
    unittest.main()
