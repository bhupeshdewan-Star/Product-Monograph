"""
Multi-format Document Generators
Creates professional documents in PDF, Word (.docx), and Google Docs formats
"""
import os
from datetime import datetime
from typing import Dict, List
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

class WordDocumentGenerator:
    """Generates professional MS Word (.docx) monographs with proper formatting"""

    def __init__(self, output_dir: str = "data/monographs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_word_monograph(self, monograph_data: Dict, output_filename: str = None) -> str:
        """
        Generate Word document with professional formatting
        Includes tables, headers, styles, and proper spacing
        """
        if not output_filename:
            molecule_name = monograph_data.get('molecule_name', 'Monograph').replace(' ', '_')
            output_filename = f"{molecule_name}_monograph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        filepath = os.path.join(self.output_dir, output_filename)

        # Create document
        doc = Document()

        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Title page
        self._add_title_page(doc, monograph_data)
        doc.add_page_break()

        # Table of contents
        self._add_table_of_contents(doc, monograph_data)
        doc.add_page_break()

        # Executive summary
        if monograph_data.get('executive_summary'):
            self._add_section(doc, "Executive Summary", monograph_data['executive_summary'])
            doc.add_page_break()

        # Main sections
        for section_name, section_content in monograph_data.get('sections', {}).items():
            self._add_section(doc, section_name.replace('_', ' ').title(), section_content)

        # Literature review table
        if monograph_data.get('literature_table'):
            doc.add_page_break()
            self._add_literature_table(doc, monograph_data['literature_table'])

        # Indian market context
        if monograph_data.get('indian_context'):
            doc.add_page_break()
            self._add_section(doc, "India-Specific Context", monograph_data['indian_context'])

        # References
        if monograph_data.get('references'):
            doc.add_page_break()
            self._add_references(doc, monograph_data['references'])

        # Disclaimer
        doc.add_page_break()
        self._add_disclaimer(doc)

        # Save document
        doc.save(filepath)
        print(f"[OK] Word document generated: {filepath}")
        return filepath

    def _add_title_page(self, doc: Document, monograph_data: Dict):
        """Add professional title page"""
        # Add spacing
        for _ in range(5):
            doc.add_paragraph()

        # Title
        title = doc.add_paragraph()
        title_run = title.add_run(monograph_data.get('molecule_name', 'Product Monograph'))
        title_run.font.size = Pt(28)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(26, 26, 26)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()

        # Subtitle
        subtitle = doc.add_paragraph("Product Monograph")
        subtitle_run = subtitle.runs[0]
        subtitle_run.font.size = Pt(14)
        subtitle_run.font.color.rgb = RGBColor(100, 100, 100)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()
        doc.add_paragraph()

        # Metadata
        metadata = [
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            f"Status: Draft - Auto-Generated",
            f"Compliance Score: {monograph_data.get('compliance_score', 'N/A')}%",
            f"Total Sections: {len(monograph_data.get('sections', {}))}",
        ]

        for line in metadata:
            p = doc.add_paragraph(line)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)

        doc.add_paragraph()
        doc.add_paragraph()

        # Important notice
        notice = doc.add_paragraph()
        notice_run = notice.add_run(
            "IMPORTANT NOTICE: This product monograph was auto-generated using artificial "
            "intelligence. While efforts were made to ensure accuracy, this document requires "
            "medical review before distribution to healthcare professionals."
        )
        notice_run.font.size = Pt(10)
        notice_run.font.italic = True
        notice.paragraph_format.space_before = Pt(12)
        notice.paragraph_format.space_after = Pt(12)

    def _add_table_of_contents(self, doc: Document, monograph_data: Dict):
        """Add table of contents"""
        heading = doc.add_heading('Table of Contents', level=1)
        heading.runs[0].font.color.rgb = RGBColor(44, 90, 160)

        sections = monograph_data.get('sections', {})
        for i, section_name in enumerate(sections.keys(), 1):
            section_title = section_name.replace('_', ' ').title()
            p = doc.add_paragraph(f"{i}. {section_title}")
            p.paragraph_format.left_indent = Inches(0.25)

    def _add_section(self, doc: Document, section_title: str, content: str):
        """Add a section with proper formatting"""
        heading = doc.add_heading(section_title, level=1)
        heading.runs[0].font.color.rgb = RGBColor(44, 90, 160)

        # Parse markdown-like content
        paragraphs = content.split('\n\n')

        for para_text in paragraphs:
            if not para_text.strip():
                continue

            if para_text.startswith('##'):
                # Subsection
                subsection = para_text.replace('##', '').strip()
                sub_heading = doc.add_heading(subsection, level=2)
                sub_heading.runs[0].font.color.rgb = RGBColor(70, 130, 180)

            elif para_text.startswith('- '):
                # Bullet list
                items = para_text.split('\n- ')
                for item in items:
                    item_clean = item.replace('- ', '').strip()
                    doc.add_paragraph(item_clean, style='List Bullet')

            else:
                # Regular paragraph
                p = doc.add_paragraph(para_text.strip())
                p.paragraph_format.space_after = Pt(6)

    def _add_literature_table(self, doc: Document, literature_data: str):
        """Add literature review table"""
        heading = doc.add_heading('Literature Review', level=1)
        heading.runs[0].font.color.rgb = RGBColor(44, 90, 160)

        # Parse table from markdown (simplified)
        lines = literature_data.split('\n')

        # Create table (assumes markdown table format)
        table = doc.add_table(rows=1, cols=7)
        table.style = 'Light Grid Accent 1'

        # Header
        header_cells = table.rows[0].cells
        headers = ['Ref', 'Author/Year', 'Study Type', 'Population', 'Key Findings', 'Level', 'Clinical Significance']
        for i, header in enumerate(headers):
            header_cells[i].text = header
            # Bold header
            for paragraph in header_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
            # Header background color
            self._shade_cell(header_cells[i], "2C5AA0")

        # Add rows from literature data (simplified - in production, parse actual data)
        for line in lines[2:]:  # Skip header separator
            if line.strip() and '|' in line:
                cells_data = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
                if len(cells_data) >= 7:
                    row_cells = table.add_row().cells
                    for i, data in enumerate(cells_data[:7]):
                        row_cells[i].text = data

    def _add_references(self, doc: Document, references: str):
        """Add references section"""
        heading = doc.add_heading('References', level=1)
        heading.runs[0].font.color.rgb = RGBColor(44, 90, 160)

        for ref_line in references.split('\n'):
            if ref_line.strip():
                p = doc.add_paragraph(ref_line.strip())
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.hanging_indent = Inches(-0.5)
                p.paragraph_format.space_after = Pt(6)

    def _add_disclaimer(self, doc: Document):
        """Add regulatory disclaimer"""
        heading = doc.add_heading('Regulatory Disclaimer', level=1)
        heading.runs[0].font.color.rgb = RGBColor(44, 90, 160)

        disclaimer_text = """This product monograph was automatically generated using artificial intelligence and information from public medical databases. While efforts have been made to ensure accuracy, the following qualifications apply:

1. AUTO-GENERATED CONTENT: This document was not prepared by a licensed medical professional. All claims should be independently verified.

2. REGULATORY COMPLIANCE: This document is a draft summary and may not reflect current regulatory status. For authoritative information, consult FDA, EMA, PMDA, or CDSCO websites.

3. MEDICAL REVIEW REQUIRED: This document must be reviewed by a qualified medical professional before distribution.

4. LIABILITY: Use of this document is at the user's sole risk. The generator assumes no liability for consequences.

5. ORIGINAL SOURCES: All citations should be verified against original publications."""

        p = doc.add_paragraph(disclaimer_text)
        p.paragraph_format.space_after = Pt(6)

        footer = doc.add_paragraph(f"\nGenerated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}")
        footer.runs[0].font.italic = True
        footer.runs[0].font.size = Pt(9)

    def _shade_cell(self, cell, color: str):
        """Shade cell background color"""
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), color)
        cell._element.get_or_add_tcPr().append(shading_elm)


class GoogleDocsGenerator:
    """Generates Google Docs format (via export)"""

    def __init__(self, output_dir: str = "data/monographs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_google_docs_template(self, monograph_data: Dict) -> str:
        """
        Create a template/instruction file for importing to Google Docs
        In production, would use Google Docs API
        """
        filename = f"{monograph_data.get('molecule_name', 'Monograph')}_GoogleDocs_Import_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = os.path.join(self.output_dir, filename)

        content = f"""# IMPORT INSTRUCTIONS FOR GOOGLE DOCS

Molecule: {monograph_data.get('molecule_name')}
Generated: {datetime.now().strftime('%B %d, %Y')}

## STEPS TO CREATE IN GOOGLE DOCS:

1. Create new Google Doc at docs.google.com
2. Copy and paste the content below into Google Docs
3. Format as needed (Docs will auto-format some elements)
4. Share with colleagues using Google Docs sharing

## DOCUMENT CONTENT:

=== START OF CONTENT ===

# {monograph_data.get('molecule_name')} - PRODUCT MONOGRAPH

## EXECUTIVE SUMMARY
{monograph_data.get('executive_summary', 'N/A')}

## MAIN SECTIONS

{self._format_sections(monograph_data)}

## LITERATURE REVIEW
{monograph_data.get('literature_table', 'N/A')}

## INDIA-SPECIFIC CONTEXT
{monograph_data.get('indian_context', 'N/A')}

## REFERENCES
{monograph_data.get('references', 'N/A')}

=== END OF CONTENT ===

## GOOGLE DOCS API ALTERNATIVE (For Future Implementation):

To automatically create Google Docs:
1. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
2. Create Google Cloud project and enable Docs API
3. Use google.docs API to create and format documents programmatically

See: https://developers.google.com/docs/api/quickstart/python
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Google Docs import template: {filepath}")
        return filepath

    def _format_sections(self, monograph_data: Dict) -> str:
        """Format sections for Google Docs"""
        formatted = ""
        for section_name, section_content in monograph_data.get('sections', {}).items():
            section_title = section_name.replace('_', ' ').title()
            formatted += f"\n### {section_title}\n\n{section_content}\n\n"
        return formatted


# Initialize globally
word_generator = WordDocumentGenerator()
google_docs_generator = GoogleDocsGenerator()
