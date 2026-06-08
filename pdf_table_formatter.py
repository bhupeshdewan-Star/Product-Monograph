"""
Professional PDF Table Formatter
Converts markdown/plain tables to professional ReportLab tables
Fixes formatting issues in PDF output
"""
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import re

class PDFTableFormatter:
    """Converts tables to professional PDF format"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_table_styles()

    def _setup_table_styles(self):
        """Define professional table styles"""
        # Header style
        self.header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.whitesmoke,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=6,
            spaceBefore=6
        )

        # Data style
        self.data_style = ParagraphStyle(
            'TableData',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=4,
            spaceBefore=4,
            leading=11
        )

    def format_literature_table(self, articles_data: list) -> Table:
        """
        Create professional literature review table

        Columns: Ref | Author/Year | Type | Population | Key Findings | Level | Significance
        """

        # Table header
        headers = [
            'Ref',
            'Author/Year',
            'Study Type',
            'Population',
            'Key Findings',
            'Level',
            'Clinical Significance'
        ]

        # Convert to Paragraph objects for proper text wrapping
        header_row = [Paragraph(h, self.header_style) for h in headers]

        # Data rows
        data_rows = [header_row]

        for article in articles_data:
            row = [
                Paragraph(f"[{article.get('ref_number', '')}]", self.data_style),
                Paragraph(self._format_author_year(article), self.data_style),
                Paragraph(article.get('study_type', 'N/A'), self.data_style),
                Paragraph(article.get('population', 'N/A'), self.data_style),
                Paragraph(article.get('key_findings', 'N/A'), self.data_style),
                Paragraph(article.get('evidence_level', 'N/A'), self.data_style),
                Paragraph(article.get('clinical_significance', 'N/A'), self.data_style),
            ]
            data_rows.append(row)

        # Create table
        col_widths = [
            0.6 * inch,  # Ref
            1.2 * inch,  # Author/Year
            1.0 * inch,  # Study Type
            1.0 * inch,  # Population
            1.8 * inch,  # Key Findings
            0.6 * inch,  # Level
            1.2 * inch   # Clinical Significance
        ]

        table = Table(data_rows, colWidths=col_widths)

        # Apply professional styling
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5AA0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

            # Data styling
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),

            # Reference column centered
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'CENTER'),  # Evidence level

            # Valign
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # Borders
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C5AA0')),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2C5AA0')),
        ]))

        return table

    def format_pharmacokinetics_table(self) -> Table:
        """Create pharmacokinetics parameters table"""

        data = [
            ['Parameter', 'Value', 'Unit', 'Notes'],
            ['Cmax', '2.5-3.2', 'mg/L', 'Fasting state'],
            ['Tmax', '2-4', 'hours', 'With food'],
            ['Half-life', '4-6', 'hours', 'Serum'],
            ['AUC', '15-20', 'mg·h/L', 'Single dose'],
            ['Bioavailability', '85-95', '%', 'Oral'],
            ['Protein Binding', '90', '%', 'Plasma proteins'],
            ['Metabolism', 'Hepatic', 'CYP450', 'Primary route'],
            ['Elimination', 'Renal', '%', '70% unchanged'],
        ]

        # Convert to Paragraph objects
        styled_data = []
        for i, row in enumerate(data):
            if i == 0:  # Header
                styled_row = [Paragraph(f"<b>{cell}</b>", self.header_style) for cell in row]
            else:
                styled_row = [Paragraph(cell, self.data_style) for cell in row]
            styled_data.append(styled_row)

        table = Table(styled_data, colWidths=[1.5*inch, 1*inch, 1*inch, 2*inch])

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5AA0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),

            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C5AA0')),
        ]))

        return table

    def format_adverse_events_table(self, adverse_events: dict) -> Table:
        """Create CIOMS adverse events classification table"""

        data = [
            ['Frequency', 'Range', 'Description', 'Examples'],
        ]

        cioms_categories = {
            'Very Common': ('≥10%', 'Very frequent occurrence'),
            'Common': ('≥1%, <10%', 'Frequent but not very common'),
            'Uncommon': ('≥0.1%, <1%', 'Occasional occurrence'),
            'Rare': ('≥0.01%, <0.1%', 'Seldom encountered'),
            'Very Rare': ('<0.01%', 'Extremely rare'),
        }

        for category, (range_val, description) in cioms_categories.items():
            examples = adverse_events.get(category, 'N/A')
            data.append([category, range_val, description, examples])

        # Convert to Paragraph objects
        styled_data = []
        for i, row in enumerate(data):
            if i == 0:  # Header
                styled_row = [Paragraph(f"<b>{cell}</b>", self.header_style) for cell in row]
            else:
                styled_row = [Paragraph(cell, self.data_style) for cell in row]
            styled_data.append(styled_row)

        table = Table(styled_data, colWidths=[1.2*inch, 1*inch, 1.8*inch, 2.5*inch])

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5AA0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),

            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C5AA0')),
        ]))

        return table

    def _format_author_year(self, article: dict) -> str:
        """Format author and year"""
        authors = article.get('authors', ['Unknown'])
        if isinstance(authors, list):
            if len(authors) > 3:
                author_str = f"{authors[0]} et al"
            else:
                author_str = ", ".join(authors)
        else:
            author_str = str(authors)

        year = article.get('year', 'N/A')
        return f"{author_str}, {year}"


# Initialize globally
pdf_table_formatter = PDFTableFormatter()
