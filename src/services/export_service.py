from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, Optional
from xml.sax.saxutils import escape as xml_escape

from config import APP_NAME, MONOGRAPHS_DIR
from src.services.document_generators import google_docs_generator, word_generator
from src.services.pdf_generator import pdf_generator
from src.services.render_helpers import (
    html_table,
    is_bullet_block,
    is_markdown_table,
    normalize_unicode_text,
    parse_markdown_table,
    placeholder_callout_html,
    placeholder_items,
    split_blocks,
)


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

    def export_xlsx(self, monograph: Dict, filename: Optional[str] = None) -> str:
        path = self.output_dir / (filename or f"{self._slug(monograph.get('molecule_name', APP_NAME))}.xlsx")
        self._write_minimal_xlsx(path, monograph)
        return str(path)

    def export_print_ready(self, monograph: Dict, filename: Optional[str] = None) -> str:
        path = self.output_dir / (
            filename or f"{self._slug(monograph.get('molecule_name', APP_NAME))}_print_ready.html"
        )
        path.write_text(self._build_print_ready_html(monograph), encoding="utf-8")
        return str(path)

    def export_bundle(self, monograph: Dict) -> Dict[str, str]:
        bundle = {
            "json": self.export_json(monograph),
            "markdown": self.export_markdown(monograph),
            "print_ready": self.export_print_ready(monograph),
        }
        try:
            bundle["pdf"] = self.export_pdf(monograph)
        except Exception as exc:
            bundle["pdf_error"] = str(exc)
        try:
            bundle["word"] = self.export_word(monograph)
        except Exception as exc:
            bundle["word_error"] = str(exc)
        try:
            bundle["xlsx"] = self.export_xlsx(monograph)
        except Exception as exc:
            bundle["xlsx_error"] = str(exc)
        try:
            bundle["google_docs"] = self.export_google_docs(monograph)
        except Exception as exc:
            bundle["google_docs_error"] = str(exc)
        return bundle

    def _build_markdown(self, monograph: Dict) -> str:
        lines = [
            f"# {monograph.get('molecule_name', APP_NAME)}",
            "",
            monograph.get("disclaimer", ""),
            "",
            f"**Generation mode:** {monograph.get('generation_label', 'Draft')}",
            "",
        ]
        placeholders = monograph.get("draft_placeholders") or {}
        if placeholders:
            lines.extend(["## Draft Placeholders", ""])
            for section_name, items in placeholders.items():
                lines.append(f"### {section_name.title()}")
                for item in items:
                    label = item.get("label", "Placeholder")
                    status = item.get("status", "draft placeholder")
                    instruction = item.get("instruction", "")
                    lines.append(f"- {label} ({status}): {instruction}")
                lines.append("")
        for section_name, content in monograph.get("sections", {}).items():
            lines.extend([f"## {section_name.replace('_', ' ').title()}", "", str(content), ""])
        if monograph.get("executive_summary"):
            lines.extend(["## Executive Summary", "", str(monograph["executive_summary"]), ""])
        validation = monograph.get("validation")
        if validation:
            lines.extend(["## Validation", "", "```json", json.dumps(validation, indent=2), "```", ""])
        return "\n".join(lines)

    def _build_print_ready_html(self, monograph: Dict) -> str:
        sections_html = []
        for section_name, content in monograph.get("sections", {}).items():
            sections_html.append(
                f"""
                <section class="page-break">
                  <h2>{escape(section_name.replace('_', ' ').title())}</h2>
                  <div class="content">{self._markdownish_to_html(str(content))}</div>
                </section>
                """
            )
        placeholder_html = ""
        items = placeholder_items(monograph.get("draft_placeholders"))
        if items:
            placeholder_html = "<section><h2>Draft Placeholders</h2>" + "".join(
                placeholder_callout_html(item) for item in items
            ) + "</section>"
        validation_html = ""
        if monograph.get("validation"):
            validation_html = f"""
                <section class="page-break">
                  <h2>Validation</h2>
                  {self._validation_summary_html(monograph.get("validation"))}
                </section>
            """
        generated_at = escape(monograph.get("generated_at", ""))
        label = escape(monograph.get("generation_label", "Draft"))
        disclaimer = escape(monograph.get("disclaimer", ""))
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(monograph.get('molecule_name', APP_NAME))} - Print Ready</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ font-family: "Segoe UI", Arial, sans-serif; margin: 34px; color: #1f2937; line-height: 1.6; font-size: 15px; }}
    h1, h2, h3 {{ color: #123a63; margin-bottom: 0.4rem; }}
    h1 {{ font-size: 30px; margin-top: 0; }}
    h2 {{ font-size: 22px; margin-top: 1.2rem; border-bottom: 1px solid #d7e0ea; padding-bottom: 0.25rem; }}
    h3 {{ font-size: 18px; margin-top: 1rem; }}
    .meta {{ background: #f3f6fb; border: 1px solid #d7e0ea; border-radius: 12px; padding: 16px; margin-bottom: 20px; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e8eef6; color: #123a63; font-size: 12px; margin-left: 8px; }}
    .content p {{ margin: 0 0 0.85rem 0; }}
    .content ul {{ margin: 0.3rem 0 0.9rem 1.2rem; }}
    .page-break {{ page-break-after: always; break-after: page; }}
    pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e5e7eb; }}
    table.mono-table {{ width: 100%; border-collapse: collapse; margin: 0.75rem 0 1rem 0; font-size: 14px; }}
    table.mono-table th {{ background: #2c5aa0; color: white; padding: 10px; border: 1px solid #b9c7d8; text-align: left; }}
    table.mono-table td {{ padding: 10px; border: 1px solid #d7e0ea; vertical-align: top; }}
    table.mono-table tr:nth-child(even) td {{ background: #f7f9fc; }}
    .placeholder-box {{ border: 1px solid #d8a800; background: #fff8e7; border-radius: 12px; padding: 14px; margin: 0.8rem 0; }}
    .placeholder-label {{ font-weight: 700; color: #7a5b00; margin-bottom: 0.25rem; }}
    .placeholder-status {{ display: inline-block; background: #f3e2a1; color: #5a4200; border-radius: 999px; padding: 2px 8px; font-size: 12px; margin-bottom: 0.45rem; }}
    .placeholder-instruction {{ margin-top: 0.35rem; }}
    @media print {{
      body {{ margin: 16mm; }}
      .page-break {{ page-break-after: always; }}
    }}
  </style>
</head>
<body>
  <h1>{escape(monograph.get('molecule_name', APP_NAME))}</h1>
  <div class="meta">
    <p><strong>Generation label:</strong> {label}</p>
    <p><strong>Generated at:</strong> {generated_at}</p>
    <p><strong>Disclaimer:</strong> {disclaimer}</p>
  </div>
  {placeholder_html}
  <section>
    <h2>Executive Summary</h2>
    <div class="content">{self._markdownish_to_html(str(monograph.get('executive_summary', '')))}</div>
  </section>
  {''.join(sections_html)}
  {validation_html}
</body>
</html>"""

    def _markdownish_to_html(self, text: str) -> str:
        blocks = []
        for block in split_blocks(normalize_unicode_text(text)):
            if block.startswith("## "):
                blocks.append(f"<h3>{escape(block[3:].strip())}</h3>")
            elif is_markdown_table(block):
                rows = parse_markdown_table(block)
                if rows:
                    blocks.append(html_table(rows))
            elif is_bullet_block(block):
                items = "".join(f"<li>{escape(line[2:].strip())}</li>" for line in block.splitlines() if line.startswith("- "))
                blocks.append(f"<ul>{items}</ul>")
            elif block.startswith("[") and "Placeholder" in block:
                blocks.append(f"<div class='placeholder-box'><div class='placeholder-instruction'>{escape(block)}</div></div>")
            else:
                blocks.append(f"<p>{escape(block)}</p>")
        return "".join(blocks) if blocks else "<p></p>"

    def _validation_summary_html(self, validation: Dict) -> str:
        score = float(validation.get("overall_compliance_score", 0) or 0)
        status = validation.get("status", "UNKNOWN")
        missing = validation.get("mandatory_sections_missing", [])
        critical = validation.get("critical_issues", [])
        details = validation.get("section_details", {})
        html = [
            "<div class='meta'>",
            f"<p><strong>Overall compliance:</strong> {score:.1f}%</p>",
            f"<p><strong>Status:</strong> {escape(str(status))}</p>",
            f"<p><strong>Sections validated:</strong> {validation.get('sections_validated', 0)}</p>",
            f"<p><strong>Sections compliant:</strong> {validation.get('sections_compliant', 0)}</p>",
            "</div>",
        ]
        if missing:
            html.append("<h3>Missing mandatory sections</h3><ul>")
            html.extend(f"<li>{escape(str(item).replace('_', ' ').title())}</li>" for item in missing)
            html.append("</ul>")
        if critical:
            html.append("<h3>Critical issues</h3><ul>")
            html.extend(f"<li>{escape(str(item))}</li>" for item in critical)
            html.append("</ul>")
        html.append("<h3>Section status indicators</h3>")
        for section_name, detail in details.items():
            section_score = float(detail.get("compliance_score", 0) or 0)
            issue_text = "; ".join(detail.get("issues", [])) or "No issues detected"
            status_text = detail.get("status", "UNKNOWN")
            color = "#dff5e1" if status_text == "PASS" else "#fff0d9"
            html.append(
                f"<div class='placeholder-box' style='background:{color};border-color:#9aa7b3;'>"
                f"<div class='placeholder-label'>{escape(section_name.replace('_', ' ').title())}</div>"
                f"<div class='placeholder-status'>Status: {escape(status_text)} | Score: {section_score:.1f}%</div>"
                f"<div class='placeholder-instruction'>{escape(issue_text)}</div>"
                f"</div>"
            )
        return "".join(html)

    def _write_minimal_xlsx(self, path: Path, monograph: Dict) -> None:
        rows = self._xlsx_rows(monograph)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", self._xlsx_content_types())
            zf.writestr("_rels/.rels", self._xlsx_root_rels())
            zf.writestr("docProps/core.xml", self._xlsx_core_props(monograph))
            zf.writestr("docProps/app.xml", self._xlsx_app_props(monograph))
            zf.writestr("xl/workbook.xml", self._xlsx_workbook())
            zf.writestr("xl/_rels/workbook.xml.rels", self._xlsx_workbook_rels())
            zf.writestr("xl/styles.xml", self._xlsx_styles())
            zf.writestr("xl/worksheets/sheet1.xml", self._xlsx_sheet(rows))

    def _xlsx_rows(self, monograph: Dict) -> list[list[str]]:
        rows: list[list[str]] = [
            ["Product Monograph", str(monograph.get("molecule_name", APP_NAME))],
            ["Generation label", str(monograph.get("generation_label", ""))],
            ["Disclaimer", str(monograph.get("disclaimer", ""))],
            ["Generated at", str(monograph.get("generated_at", ""))],
            [],
            ["Section", "Content"],
        ]
        placeholders = monograph.get("draft_placeholders") or {}
        if placeholders:
            rows.append(["Draft placeholders", ""])
            for bucket, entries in placeholders.items():
                for entry in entries:
                    rows.append([
                        f"{bucket.title()} - {entry.get('label', 'Placeholder')}",
                        f"{entry.get('status', 'draft placeholder')}: {entry.get('instruction', '')}",
                    ])
        for section_name, content in monograph.get("sections", {}).items():
            rows.append([section_name.replace("_", " ").title(), str(content)])
        if monograph.get("executive_summary"):
            rows.append(["Executive Summary", str(monograph.get("executive_summary"))])
        if monograph.get("validation"):
            rows.append(["Validation", json.dumps(monograph.get("validation"), indent=2, ensure_ascii=False)])
        return rows

    def _xlsx_content_types(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

    def _xlsx_root_rels(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

    def _xlsx_core_props(self, monograph: Dict) -> str:
        created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{xml_escape(str(monograph.get('molecule_name', APP_NAME)))}</dc:title>
  <dc:creator>Product Monograph Champ</dc:creator>
  <cp:lastModifiedBy>Product Monograph Champ</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>"""

    def _xlsx_app_props(self, monograph: Dict) -> str:
        total = len(monograph.get("sections", {}))
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Product Monograph Champ</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>1</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="1" baseType="lpstr">
      <vt:lpstr>Monograph</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
  <Company>Product Monograph Champ</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>1.0</AppVersion>
  <TotalTime>0</TotalTime>
  <Words>{total}</Words>
</Properties>"""

    def _xlsx_workbook(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Monograph" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    def _xlsx_workbook_rels(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    def _xlsx_styles(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><color rgb="FF000000"/><name val="Arial"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

    def _xlsx_sheet(self, rows: list[list[str]]) -> str:
        sheet_rows = []
        for row_index, row in enumerate(rows, start=1):
            cells = []
            for col_index, value in enumerate(row, start=1):
                if value is None or value == "":
                    continue
                cell_ref = f"{self._column_letter(col_index)}{row_index}"
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr" s="0"><is><t xml:space="preserve">{xml_escape(str(value))}</t></is></c>'
                )
            sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="18"/>
  <sheetData>
    {''.join(sheet_rows)}
  </sheetData>
</worksheet>"""

    @staticmethod
    def _column_letter(index: int) -> str:
        result = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result

    @staticmethod
    def _slug(text: str) -> str:
        safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")
        return safe or "monograph"


export_service = ExportService()
