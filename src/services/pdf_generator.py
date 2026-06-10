"""
PDF Generator: Creates professional, SOP-compliant PDF monographs.
Supports Unicode, markdown tables, bullets, and styled placeholder callouts.
"""
from __future__ import annotations

import os
from datetime import datetime
from html import escape
from typing import Dict, List

from reportlab.lib.colors import HexColor, black, grey, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.services.render_helpers import (
    is_bullet_block,
    is_markdown_table,
    normalize_unicode_text,
    parse_markdown_table,
    placeholder_items,
)


class MonographPDFGenerator:
    """Generates professional SOP-compliant PDF monographs."""

    def __init__(self, output_dir: str = "data/monographs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.body_font, self.bold_font = self._register_unicode_fonts()
        self.styles = getSampleStyleSheet()
        self._define_custom_styles()

    def _register_unicode_fonts(self) -> tuple[str, str]:
        try:
            from matplotlib import font_manager

            regular = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="normal"))
            bold = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold"))
            pdfmetrics.registerFont(TTFont("PMC-DejaVuSans", regular))
            pdfmetrics.registerFont(TTFont("PMC-DejaVuSans-Bold", bold))
            return "PMC-DejaVuSans", "PMC-DejaVuSans-Bold"
        except Exception:
            return "Helvetica", "Helvetica-Bold"

    def _define_custom_styles(self) -> None:
        self.styles.add(
            ParagraphStyle(
                name="MonographTitle",
                parent=self.styles["Heading1"],
                fontName=self.bold_font,
                fontSize=24,
                textColor=HexColor("#1a1a1a"),
                spaceAfter=18,
                alignment=TA_CENTER,
                leading=28,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=self.styles["Heading2"],
                fontName=self.bold_font,
                fontSize=14,
                textColor=HexColor("#2c5aa0"),
                spaceAfter=10,
                spaceBefore=14,
                leading=18,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SubsectionHeading",
                parent=self.styles["Heading3"],
                fontName=self.bold_font,
                fontSize=12,
                textColor=HexColor("#2c5aa0"),
                spaceAfter=6,
                spaceBefore=8,
                leading=15,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="BodyTextJustified",
                parent=self.styles["BodyText"],
                fontName=self.body_font,
                fontSize=10.5,
                alignment=TA_JUSTIFY,
                spaceAfter=7,
                leading=14,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Callout",
                parent=self.styles["BodyText"],
                fontName=self.body_font,
                fontSize=10.2,
                textColor=HexColor("#17324d"),
                leading=13,
            )
        )

    def generate_pdf(self, monograph_data: Dict, output_filename: str = None) -> str:
        if not output_filename:
            molecule_name = monograph_data.get("molecule_name", "Monograph").replace(" ", "_")
            output_filename = f"{molecule_name}_monograph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        filepath = os.path.join(self.output_dir, output_filename)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.7 * inch,
            leftMargin=0.7 * inch,
            topMargin=0.8 * inch,
            bottomMargin=0.75 * inch,
            title=f"Product Monograph: {monograph_data.get('molecule_name', '')}",
            author="Product Monograph Champ",
        )

        story: List = []
        story.extend(self._build_title_page(monograph_data))
        story.append(PageBreak())
        story.extend(self._build_table_of_contents(monograph_data))
        story.append(PageBreak())

        if monograph_data.get("executive_summary"):
            story.extend(self._build_named_section("Executive Summary", monograph_data["executive_summary"]))
            story.append(Spacer(1, 0.18 * inch))

        for section_name, section_content in monograph_data.get("sections", {}).items():
            story.extend(self._build_named_section(section_name.replace("_", " ").title(), section_content))
            story.append(Spacer(1, 0.18 * inch))

        if monograph_data.get("draft_placeholders"):
            story.append(PageBreak())
            story.extend(self._build_placeholders(monograph_data["draft_placeholders"]))

        if monograph_data.get("validation"):
            story.append(PageBreak())
            story.extend(self._build_validation_summary(monograph_data))

        story.append(PageBreak())
        story.extend(self._build_disclaimer())

        doc.build(story)
        print(f"[OK] PDF generated: {filepath}")
        return filepath

    def _build_title_page(self, monograph_data: Dict) -> List:
        story: List = [Spacer(1, 1.3 * inch)]
        title = normalize_unicode_text(monograph_data.get("molecule_name", "Product Monograph"))
        story.append(Paragraph(escape(title), self.styles["MonographTitle"]))
        story.append(Spacer(1, 0.25 * inch))

        metadata = [
            f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y')}",
            "<b>Status:</b> Draft - Auto-Generated",
            f"<b>Validation Score:</b> {monograph_data.get('validation', {}).get('overall_compliance_score', 'N/A')}%",
            f"<b>Total Sections:</b> {len(monograph_data.get('sections', {}))}",
        ]
        for line in metadata:
            story.append(Paragraph(line, self.styles["BodyTextJustified"]))
            story.append(Spacer(1, 0.05 * inch))

        story.append(Spacer(1, 0.2 * inch))
        notice = (
            "<b>IMPORTANT NOTICE:</b> This product monograph is a draft generated for medical "
            "and regulatory review only. It must be checked against source documents before any "
            "clinical or publication use."
        )
        story.append(
            Table(
                [[Paragraph(notice, self.styles["Callout"])]],
                colWidths=[6.7 * inch],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#eef5fb")),
                        ("BOX", (0, 0), (-1, -1), 1, HexColor("#2c5aa0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 12),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ]
                ),
            )
        )
        return story

    def _build_table_of_contents(self, monograph_data: Dict) -> List:
        story: List = [Paragraph("Table of Contents", self.styles["Heading1"]), Spacer(1, 0.12 * inch)]
        sections = monograph_data.get("sections", {})
        for i, section_name in enumerate(sections.keys(), 1):
            story.append(Paragraph(f"{i}. {escape(section_name.replace('_', ' ').title())}", self.styles["BodyTextJustified"]))
        return story

    def _build_named_section(self, section_title: str, content: str) -> List:
        story: List = [Paragraph(escape(normalize_unicode_text(section_title)), self.styles["SectionHeading"])]
        story.extend(self._render_content(content, section_title=section_title))
        return story

    def _render_content(self, content: str, section_title: str = "") -> List:
        story: List = []
        for block in (content or "").split("\n\n"):
            block = normalize_unicode_text(block.strip())
            if not block:
                continue
            if block.startswith("## "):
                story.append(Paragraph(escape(block[3:].strip()), self.styles["SubsectionHeading"]))
            elif is_markdown_table(block):
                rows = parse_markdown_table(block)
                if rows:
                    story.append(self._table_flowable(rows))
            elif is_bullet_block(block):
                for line in block.splitlines():
                    item = line[2:].strip()
                    story.append(Paragraph(f"• {escape(item)}", self.styles["BodyTextJustified"]))
            elif block.startswith("[") and "Placeholder" in block:
                story.append(self._placeholder_flowable(section_title, block))
            else:
                story.append(Paragraph(escape(block), self.styles["BodyTextJustified"]))
            story.append(Spacer(1, 0.06 * inch))
        return story

    def _table_flowable(self, rows: list[list[str]]) -> Table:
        styled_rows = []
        for row_index, row in enumerate(rows):
            styled_rows.append(
                [
                    Paragraph(
                        escape(normalize_unicode_text(cell)),
                        self.styles["Callout"] if row_index == 0 else self.styles["BodyTextJustified"],
                    )
                    for cell in row
                ]
            )
        table_width = 6.7 * inch
        col_width = table_width / max(1, len(rows[0]))
        table = Table(styled_rows, repeatRows=1, hAlign="LEFT", colWidths=[col_width for _ in rows[0]])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2c5aa0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("FONTNAME", (0, 0), (-1, 0), self.bold_font),
                    ("FONTNAME", (0, 1), (-1, -1), self.body_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEADING", (0, 0), (-1, -1), 11),
                    ("GRID", (0, 0), (-1, -1), 0.5, grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f5f7fa")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return table

    def _placeholder_flowable(self, section_title: str, text: str) -> Table:
        body = f"<b>{escape(normalize_unicode_text(section_title))}</b><br/>{escape(normalize_unicode_text(text))}"
        return Table(
            [[Paragraph(body, self.styles["Callout"])]],
            colWidths=[6.7 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fff8e7")),
                    ("BOX", (0, 0), (-1, -1), 1, HexColor("#d8a800")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        )

    def _build_placeholders(self, placeholders: Dict) -> List:
        story: List = [Paragraph("Draft Placeholders", self.styles["SectionHeading"]), Spacer(1, 0.12 * inch)]
        for item in placeholder_items(placeholders):
            story.append(
                Table(
                    [[Paragraph(
                        f"<b>{escape(item['label'])}</b><br/><font size='9'>{escape(item['instruction'])}</font>",
                        self.styles["Callout"],
                    )]],
                    colWidths=[6.7 * inch],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f4f8fc")),
                            ("BOX", (0, 0), (-1, -1), 1, HexColor("#2c5aa0")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    ),
                )
            )
            story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_validation_summary(self, monograph_data: Dict) -> List:
        validation = monograph_data.get("validation", {})
        score = float(validation.get("overall_compliance_score", 0) or 0)
        status = validation.get("status", "UNKNOWN")
        critical_issues = validation.get("critical_issues", [])
        missing = validation.get("mandatory_sections_missing", [])
        details = validation.get("section_details", {})

        story: List = [Paragraph("Validation Summary", self.styles["SectionHeading"]), Spacer(1, 0.08 * inch)]
        summary_lines = [
            f"<b>Overall compliance:</b> {score:.1f}%",
            f"<b>Status:</b> {status}",
            f"<b>Sections validated:</b> {validation.get('sections_validated', 0)}",
            f"<b>Sections compliant:</b> {validation.get('sections_compliant', 0)}",
        ]
        story.append(
            Table(
                [[Paragraph("<br/>".join(summary_lines), self.styles["Callout"])]],
                colWidths=[6.7 * inch],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#eef5fb")),
                        ("BOX", (0, 0), (-1, -1), 1, HexColor("#2c5aa0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                ),
            )
        )
        story.append(Spacer(1, 0.12 * inch))

        if missing:
            story.append(Paragraph("Missing mandatory sections", self.styles["SubsectionHeading"]))
            for item in missing:
                story.append(Paragraph(f"• {escape(str(item).replace('_', ' ').title())}", self.styles["BodyTextJustified"]))

        if critical_issues:
            story.append(Paragraph("Critical issues", self.styles["SubsectionHeading"]))
            for issue in critical_issues:
                story.append(Paragraph(f"• {escape(str(issue))}", self.styles["BodyTextJustified"]))

        story.append(Paragraph("Section status indicators", self.styles["SubsectionHeading"]))
        for section_name, detail in details.items():
            section_score = float(detail.get("compliance_score", 0) or 0)
            issue_text = "; ".join(detail.get("issues", [])) or "No issues detected"
            status_text = detail.get("status", "UNKNOWN")
            color = "#dff5e1" if status_text == "PASS" else "#fff0d9"
            story.append(
                Table(
                    [[
                        Paragraph(
                            f"<b>{escape(section_name.replace('_', ' ').title())}</b><br/>"
                            f"Status: {escape(status_text)} | Score: {section_score:.1f}%<br/>"
                            f"{escape(issue_text)}",
                            self.styles["Callout"],
                        )
                    ]],
                    colWidths=[6.7 * inch],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), HexColor(color)),
                            ("BOX", (0, 0), (-1, -1), 1, HexColor("#9aa7b3")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 7),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ]
                    ),
                )
            )
            story.append(Spacer(1, 0.06 * inch))
        return story

    def _build_disclaimer(self) -> List:
        return [
            Paragraph("Regulatory Disclaimer", self.styles["Heading1"]),
            Spacer(1, 0.12 * inch),
            Paragraph(
                (
                    "This product monograph was automatically generated using artificial intelligence "
                    "and information from public medical databases. While efforts have been made to "
                    "ensure accuracy and adherence to regulatory standards, all claims should be "
                    "independently verified against original sources and regulatory guidance before use."
                ),
                self.styles["BodyTextJustified"],
            ),
            Spacer(1, 0.08 * inch),
            Paragraph(
                "DRAFT STATUS: This document is not for distribution without medical and regulatory review.",
                self.styles["BodyTextJustified"],
            ),
        ]

    def generate_sample_table(self) -> Table:
        data = [
            ["Parameter", "Value", "Unit", "Reference"],
            ["Cmax", "2.5-3.2", "mg/L", "Fasting"],
            ["Tmax", "2-4", "hours", "With food"],
            ["Half-life", "4-6", "hours", "Serum"],
            ["AUC", "15-20", "mg·h/L", "Single dose"],
        ]
        table = Table(data, colWidths=[2 * inch, 1.5 * inch, 1.2 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2c5aa0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), self.bold_font),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f0f0f0")]),
                ]
            )
        )
        return table


pdf_generator = MonographPDFGenerator()


if __name__ == "__main__":
    print("PDF Generator initialized")
    print(f"Output directory: {pdf_generator.output_dir}")
