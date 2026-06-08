from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from config import APP_NAME, MONOGRAPHS_DIR
from src.services.document_generators import google_docs_generator, word_generator
from src.services.pdf_generator import pdf_generator


class ExportService:
    def __init__(self, output_dir: Path = MONOGRAPHS_DIR) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, monograph: Dict, filename: Optional[str] = None) -> str:
        path = self.output_dir / (filename or f"{self._slug(monograph.get('molecule_name', APP_NAME))}.json")
        path.write_text(json.dumps(monograph, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def export_markdown(self, monograph: Dict, filename: Optional[str] = None) -> str:
        path = self.output_dir / (filename or f"{self._slug(monograph.get('molecule_name', APP_NAME))}.md")
        path.write_text(self._build_markdown(monograph), encoding="utf-8")
        return str(path)

    def export_pdf(self, monograph: Dict, filename: Optional[str] = None) -> str:
        return pdf_generator.generate_pdf(monograph, output_filename=filename)

    def export_word(self, monograph: Dict, filename: Optional[str] = None) -> str:
        return word_generator.generate_word_monograph(monograph, output_filename=filename)

    def export_google_docs(self, monograph: Dict) -> str:
        return google_docs_generator.create_google_docs_template(monograph)

    def export_bundle(self, monograph: Dict) -> Dict[str, str]:
        bundle = {
            "json": self.export_json(monograph),
            "markdown": self.export_markdown(monograph),
        }
        try:
            bundle["pdf"] = self.export_pdf(monograph)
        except Exception as exc:
            bundle["pdf_error"] = str(exc)
        try:
            bundle["word"] = self.export_word(monograph)
        except Exception as exc:
            bundle["word_error"] = str(exc)
        return bundle

    def _build_markdown(self, monograph: Dict) -> str:
        lines = [
            f"# {monograph.get('molecule_name', APP_NAME)}",
            "",
            monograph.get("disclaimer", ""),
            "",
        ]
        for section_name, content in monograph.get("sections", {}).items():
            lines.extend([f"## {section_name.replace('_', ' ').title()}", "", str(content), ""])
        validation = monograph.get("validation")
        if validation:
            lines.extend(["## Validation", "", "```json", json.dumps(validation, indent=2), "```", ""])
        return "\n".join(lines)

    @staticmethod
    def _slug(text: str) -> str:
        safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")
        return safe or "monograph"


export_service = ExportService()
