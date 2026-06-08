"""
PDF Generator: Creates professional, SOP-compliant PDF monographs
Includes tables, charts, formatted text, and regulatory disclaimers
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
from typing import Dict, List
import re

class MonographPDFGenerator:
    """Generates professional SOP-compliant PDF monographs"""

    def __init__(self, output_dir: str = "data/monographs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Define custom styles
        self.styles = getSampleStyleSheet()
        self._define_custom_styles()

    def _define_custom_styles(self):
        """Define custom paragraph styles for monograph"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='MonographTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderColor=HexColor('#2c5aa0'),
            borderWidth=2,
            borderPadding=5
        ))

        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#2c5aa0'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))

        # Body text - justified
        self.styles.add(ParagraphStyle(
            name='BodyTextJustified',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        ))

        # Highlight box for key findings
        self.styles.add(ParagraphStyle(
            name='HighlightBox',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=HexColor('#1a3a52'),
            spaceAfter=6,
            leading=12,
            backColor=HexColor('#e8f0f7'),
            borderColor=HexColor('#2c5aa0'),
            borderPadding=5
        ))

    def generate_pdf(self, monograph_data: Dict, output_filename: str = None) -> str:
        """
        Generate complete PDF monograph from monograph data
        Returns path to generated PDF
        """
        if not output_filename:
            molecule_name = monograph_data.get('molecule_name', 'Monograph').replace(' ', '_')
            output_filename = f"{molecule_name}_monograph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        filepath = os.path.join(self.output_dir, output_filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch,
            title=f"Product Monograph: {monograph_data.get('molecule_name', '')}",
            author="Automated Monograph Generator"
        )

        # Build document content
        story = []

        # Title Page
        story.extend(self._build_title_page(monograph_data))
        story.append(PageBreak())

        # Table of Contents
        story.extend(self._build_table_of_contents(monograph_data))
        story.append(PageBreak())

        # Main sections
        for section_name, section_content in monograph_data.get('sections', {}).items():
            story.extend(self._build_section(section_name, section_content))
            story.append(Spacer(1, 0.3*inch))

        # Regulatory Disclaimer
        story.append(PageBreak())
        story.extend(self._build_disclaimer())

        # Build PDF
        doc.build(story)

        print(f"[OK] PDF generated: {filepath}")
        return filepath

    def _build_title_page(self, monograph_data: Dict) -> List:
        """Build title page"""
        story = []

        # Spacing
        story.append(Spacer(1, 1.5*inch))

        # Title
        title = monograph_data.get('molecule_name', 'Product Monograph')
        story.append(Paragraph(f"<b>{title}</b>", self.styles['MonographTitle']))

        story.append(Spacer(1, 0.3*inch))

        # Metadata
        metadata = [
            f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y')}",
            f"<b>Status:</b> Draft - Auto-Generated",
            f"<b>Compliance Score:</b> {monograph_data.get('compliance_score', 'N/A')}%",
            f"<b>Total Sections:</b> {len(monograph_data.get('sections', {}))}",
        ]

        for line in metadata:
            story.append(Paragraph(line, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

        story.append(Spacer(1, 0.5*inch))

        # Important notice
        notice = """
        <font size=10><i>
        <b>IMPORTANT NOTICE:</b> This product monograph was auto-generated using artificial
        intelligence and research from public medical databases. While efforts were made to ensure
        accuracy, this document requires medical review before distribution to healthcare professionals.
        This is a DRAFT document and should not be used for clinical decision-making without expert review.
        </i></font>
        """
        story.append(Paragraph(notice, self.styles['BodyText']))

        return story

    def _build_table_of_contents(self, monograph_data: Dict) -> List:
        """Build table of contents"""
        story = []

        story.append(Paragraph("Table of Contents", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))

        sections = monograph_data.get('sections', {})
        for i, section_name in enumerate(sections.keys(), 1):
            section_title = section_name.replace('_', ' ').title()
            story.append(Paragraph(f"{i}. {section_title}", self.styles['Normal']))

        return story

    def _build_section(self, section_name: str, section_content: str) -> List:
        """Build a document section"""
        story = []

        # Section heading
        section_title = section_name.replace('_', ' ').title()
        story.append(Paragraph(f"<b>{section_title}</b>", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.15*inch))

        # Parse and format section content
        paragraphs = section_content.split('\n\n')

        for para in paragraphs:
            if not para.strip():
                continue

            # Handle subsections (starts with ##)
            if para.startswith('##'):
                subsection_title = para.replace('##', '').strip()
                story.append(Paragraph(f"<b>{subsection_title}</b>", self.styles['SubsectionHeading']))

            # Handle bold/italic formatting
            elif para.startswith('**') or para.startswith('__'):
                # This is a key finding - highlight it
                clean_text = para.replace('**', '').replace('__', '').strip()
                story.append(Paragraph(f"<b>{clean_text}</b>", self.styles['HighlightBox']))

            # Handle lists
            elif para.startswith('- '):
                items = [item.replace('- ', '').strip() for item in para.split('\n- ')]
                for item in items:
                    story.append(Paragraph(f"• {item}", self.styles['BodyTextJustified']))

            # Regular paragraph
            else:
                story.append(Paragraph(para.strip(), self.styles['BodyTextJustified']))

            story.append(Spacer(1, 0.1*inch))

        return story

    def _build_disclaimer(self) -> List:
        """Build regulatory disclaimer page"""
        story = []

        story.append(Paragraph("Regulatory Disclaimer", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))

        disclaimer = """
        <font size=9>
        <b>DISCLAIMER:</b>
        <br/><br/>
        This product monograph was automatically generated using artificial intelligence and information
        from public medical databases including PubMed, FDA, and open-access repositories. While efforts
        have been made to ensure accuracy and adherence to regulatory standards, the following qualifications apply:
        <br/><br/>
        <b>1. AUTO-GENERATED CONTENT:</b> This document was not prepared by a licensed medical professional.
        All claims and information should be independently verified against original sources and regulatory authorities.
        <br/><br/>
        <b>2. REGULATORY COMPLIANCE:</b> This document is intended as a draft summary and may not reflect
        the most current regulatory status. For authoritative regulatory information, consult:
        <br/>• FDA: <font color="blue">https://www.fda.gov</font>
        <br/>• EMA: <font color="blue">https://www.ema.europa.eu</font>
        <br/>• DCGI (India): <font color="blue">https://www.dcgi.gov.in</font>
        <br/><br/>
        <b>3. MEDICAL REVIEW REQUIRED:</b> This document must be reviewed and approved by a qualified
        medical professional before distribution to healthcare professionals.
        <br/><br/>
        <b>4. LIABILITY:</b> The use of this document is at the user's sole risk. The generator and authors
        assume no liability for any consequences arising from the use or misuse of this document.
        <br/><br/>
        <b>5. ORIGINAL SOURCES:</b> All citations should be verified against original publications and
        regulatory documents.
        <br/><br/>
        <b>Generated on:</b> {date}
        <br/>
        <b>Status:</b> DRAFT - NOT FOR DISTRIBUTION
        </font>
        """.format(date=datetime.now().strftime('%B %d, %Y at %H:%M UTC'))

        story.append(Paragraph(disclaimer, self.styles['Normal']))

        return story

    def generate_sample_table(self) -> Table:
        """Generate a sample formatted table (for clinical trials, etc.)"""
        data = [
            ['Parameter', 'Value', 'Unit', 'Reference'],
            ['Cmax', '2.5-3.2', 'mg/L', 'Fasting'],
            ['Tmax', '2-4', 'hours', 'With food'],
            ['Half-life', '4-6', 'hours', 'Serum'],
            ['AUC', '15-20', 'mg·h/L', 'Single dose'],
        ]

        table = Table(data, colWidths=[2*inch, 1.5*inch, 1.2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f0f0f0')]),
        ]))

        return table


# Initialize globally
pdf_generator = MonographPDFGenerator()

if __name__ == "__main__":
    print("PDF Generator initialized")
    print(f"Output directory: {pdf_generator.output_dir}")
