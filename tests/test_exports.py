from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from src.monograph.generator import synthesis_engine
from src.services.export_service import ExportService


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


class ExportServiceTest(unittest.TestCase):
    def test_export_bundle_includes_required_formats(self) -> None:
        monograph = synthesis_engine.generate_monograph("Metformin", _sample_sources("Metformin"))

        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(output_dir=Path(tmpdir))
            bundle = service.export_bundle(monograph)

            self.assertIn("json", bundle)
            self.assertIn("markdown", bundle)
            self.assertIn("print_ready", bundle)
            self.assertIn("xlsx", bundle)

            for key in ("json", "markdown", "print_ready", "xlsx"):
                self.assertTrue(Path(bundle[key]).exists(), msg=f"{key} export missing")

            self.assertTrue(zipfile.is_zipfile(bundle["xlsx"]))
            with zipfile.ZipFile(bundle["xlsx"]) as archive:
                self.assertIn("xl/workbook.xml", archive.namelist())
                self.assertIn("xl/worksheets/sheet1.xml", archive.namelist())

            print_ready = Path(bundle["print_ready"]).read_text(encoding="utf-8").lower()
            self.assertIn("print ready", print_ready)
            self.assertIn("draft placeholder", print_ready)


if __name__ == "__main__":
    unittest.main()
