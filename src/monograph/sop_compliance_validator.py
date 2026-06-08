"""
SOP Compliance Validator
Ensures monographs follow Standard Operating Procedure requirements
Validates formatting, sections, references, tables, and output quality
"""
from typing import Dict, Tuple
import re

class SOPComplianceValidator:
    """Validates monographs against SOP requirements"""

    def __init__(self):
        self.required_sections = [
            'introduction',
            'pharmacology',
            'pharmacokinetics',
            'clinical_efficacy',
            'safety',
            'dosage',
            'contraindications',
            'drug_interactions'
        ]

        self.section_requirements = {
            'introduction': {'min_words': 200, 'max_words': 400, 'priority': 'critical'},
            'pharmacology': {'min_words': 500, 'max_words': 800, 'priority': 'critical'},
            'pharmacokinetics': {'min_words': 400, 'max_words': 1200, 'priority': 'critical'},
            'clinical_efficacy': {'min_words': 600, 'max_words': 1200, 'priority': 'critical'},
            'safety': {'min_words': 400, 'max_words': 800, 'priority': 'critical'},
            'dosage': {'min_words': 300, 'max_words': 600, 'priority': 'high'},
            'contraindications': {'min_words': 100, 'max_words': 300, 'priority': 'high'},
            'drug_interactions': {'min_words': 200, 'max_words': 500, 'priority': 'high'},
        }

    def validate_sop_compliance(self, monograph: Dict) -> Tuple[bool, Dict]:
        """
        Comprehensive SOP compliance check

        Returns: (is_compliant, detailed_report)
        """

        report = {
            'overall_compliant': True,
            'issues': [],
            'warnings': [],
            'section_checks': {},
            'output_format_checks': {},
            'content_quality_checks': {},
            'reference_checks': {},
            'score': 100.0
        }

        # 1. Check sections
        report['section_checks'] = self._check_sections(monograph)
        if not report['section_checks']['all_present']:
            report['issues'].append("Missing required sections")
            report['overall_compliant'] = False

        # 2. Check word counts
        for section, check in report['section_checks'].items():
            if isinstance(check, dict) and check.get('word_count_valid') is False:
                report['warnings'].append(f"{section}: Word count out of range")

        # 3. Check output formats
        report['output_format_checks'] = self._check_output_formats(monograph)
        if not report['output_format_checks']['has_pdf']:
            report['issues'].append("Missing PDF output")
            report['overall_compliant'] = False

        # 4. Check for markdown artifacts
        report['content_quality_checks'] = self._check_content_quality(monograph)
        if report['content_quality_checks']['has_markdown_artifacts']:
            report['warnings'].append("Markdown artifacts found in content - not SOP compliant")
            report['overall_compliant'] = False

        # 5. Check tables
        if report['output_format_checks']['tables_poorly_formatted']:
            report['warnings'].append("Tables not professionally formatted")
            report['overall_compliant'] = False

        # 6. Check references
        report['reference_checks'] = self._check_references(monograph)
        if report['reference_checks']['count'] < 50:
            report['warnings'].append(f"Only {report['reference_checks']['count']} references found (50-100 required)")

        if not report['reference_checks']['vancouver_format']:
            report['issues'].append("References not in Vancouver style")
            report['overall_compliant'] = False

        # 7. Calculate score
        report['score'] = self._calculate_compliance_score(report)

        return report['overall_compliant'], report

    def _check_sections(self, monograph: Dict) -> Dict:
        """Check if all required sections are present and meet word count requirements"""
        sections = monograph.get('sections', {})
        checks = {'all_present': True}

        for section_name in self.required_sections:
            section_content = sections.get(section_name, '')
            word_count = len(section_content.split())

            requirements = self.section_requirements.get(section_name, {})
            min_words = requirements.get('min_words', 0)
            max_words = requirements.get('max_words', 9999)

            is_present = bool(section_content.strip())
            word_count_valid = min_words <= word_count <= max_words

            if not is_present:
                checks['all_present'] = False

            checks[section_name] = {
                'present': is_present,
                'word_count': word_count,
                'min_required': min_words,
                'max_required': max_words,
                'word_count_valid': word_count_valid,
            }

        return checks

    def _check_output_formats(self, monograph: Dict) -> Dict:
        """Check output format compliance"""
        checks = {
            'has_pdf': bool(monograph.get('pdf_path')),
            'has_word': bool(monograph.get('word_path')),
            'has_json': bool(monograph.get('json_path')),
            'has_google_docs': bool(monograph.get('google_docs_path')),
            'tables_properly_formatted': self._check_table_formatting(monograph),
            'tables_poorly_formatted': not self._check_table_formatting(monograph),
        }
        return checks

    def _check_table_formatting(self, monograph: Dict) -> bool:
        """Check if tables are professionally formatted"""
        sections = monograph.get('sections', {})

        for section, content in sections.items():
            # Check for markdown table syntax
            if '|' in content and '---' in content:
                # Markdown tables - not ideal for PDF
                return False

            # Check for table-like content
            if 'parameter' in content.lower() and 'value' in content.lower():
                # Tables should be in Word/PDF, not markdown
                return False

        return True

    def _check_content_quality(self, monograph: Dict) -> Dict:
        """Check content quality and formatting"""
        sections = monograph.get('sections', {})
        all_content = ' '.join(sections.values())

        markdown_patterns = {
            'headers': r'^#+\s',
            'bold': r'\*\*',
            'italics': r'[^\\]\*[^\\]',
            'inline_code': r'`[^`]',
            'links': r'\[.+?\]\(.+?\)',
        }

        artifact_count = 0
        for pattern_type, pattern in markdown_patterns.items():
            matches = re.findall(pattern, all_content, flags=re.MULTILINE)
            artifact_count += len(matches)

        checks = {
            'has_markdown_artifacts': artifact_count > 5,
            'markdown_artifact_count': artifact_count,
            'text_properly_cleaned': artifact_count <= 5,
        }

        return checks

    def _check_references(self, monograph: Dict) -> Dict:
        """Check reference formatting and quantity"""
        references = monograph.get('references', '')
        vancouver_refs = monograph.get('vancouver_references', '')

        # Count references
        all_refs = references + '\n' + vancouver_refs
        ref_count = len(re.findall(r'\[\d+\]', all_refs))

        # Check Vancouver format
        has_vancouver = bool(re.search(r'\[\d+\]\s+\w+\s+\w+.*\d{4}', all_refs))

        checks = {
            'count': ref_count,
            'minimum_count': 50,
            'maximum_count': 100,
            'meets_minimum': ref_count >= 50,
            'within_optimal_range': 50 <= ref_count <= 100,
            'vancouver_format': has_vancouver,
            'has_doi': bool(re.search(r'doi:', all_refs)),
        }

        return checks

    def _calculate_compliance_score(self, report: Dict) -> float:
        """Calculate overall compliance score (0-100)"""
        score = 100.0

        # Deductions
        if not report['output_format_checks'].get('has_pdf'):
            score -= 10
        if not report['output_format_checks'].get('has_word'):
            score -= 5
        if report['output_format_checks'].get('tables_poorly_formatted'):
            score -= 10
        if report['content_quality_checks'].get('has_markdown_artifacts'):
            score -= 15
        if not report['reference_checks'].get('vancouver_format'):
            score -= 10
        if report['reference_checks'].get('count') < 50:
            score -= 20
        if not report['section_checks'].get('all_present'):
            score -= 25

        return max(0.0, score)

    def generate_sop_report(self, monograph: Dict, detailed: bool = True) -> str:
        """Generate detailed SOP compliance report"""
        is_compliant, report = self.validate_sop_compliance(monograph)

        output = f"""
╔════════════════════════════════════════════════════════════════════╗
║             SOP COMPLIANCE VALIDATION REPORT                       ║
╠════════════════════════════════════════════════════════════════════╣

Molecule: {monograph.get('molecule_name', 'Unknown')}
Generated: {monograph.get('generation_timestamp', 'Unknown')}

OVERALL STATUS: {'[OK] COMPLIANT' if is_compliant else '[ERROR] NON-COMPLIANT'}
Compliance Score: {report['score']:.1f}/100

"""

        if report['issues']:
            output += "CRITICAL ISSUES:\n"
            for issue in report['issues']:
                output += f"  [ERROR] {issue}\n"
            output += "\n"

        if report['warnings']:
            output += "WARNINGS:\n"
            for warning in report['warnings']:
                output += f"  [WARN] {warning}\n"
            output += "\n"

        if detailed:
            output += "SECTION REQUIREMENTS:\n"
            output += "─────────────────────\n"
            for section in self.required_sections:
                check = report['section_checks'].get(section, {})
                if isinstance(check, dict):
                    status = "[OK]" if check.get('word_count_valid') else "[ERROR]"
                    output += f"{status} {section.upper():<25}: {check.get('word_count', 0):>4} words (required: {check.get('min_required', 0)}-{check.get('max_required', 0)})\n"

            output += "\nOUTPUT FORMATS:\n"
            output += "───────────────\n"
            for format_type, has_it in report['output_format_checks'].items():
                if 'check' not in format_type:
                    status = "[OK]" if has_it else "[ERROR]"
                    output += f"{status} {format_type.upper()}\n"

            output += "\nREFERENCES:\n"
            output += "───────────\n"
            ref_check = report['reference_checks']
            output += f"Count: {ref_check.get('count', 0)} (Required: 50-100)\n"
            output += f"Vancouver Format: {'[OK] Yes' if ref_check.get('vancouver_format') else '[ERROR] No'}\n"
            output += f"DOI Included: {'[OK] Yes' if ref_check.get('has_doi') else '[ERROR] No'}\n"

        output += """

RECOMMENDATIONS:
────────────────
"""

        recommendations = []
        if report['overall_compliant']:
            recommendations.append("[OK] Monograph meets SOP requirements - Ready for review")
        else:
            if not report['output_format_checks'].get('has_pdf'):
                recommendations.append("Generate PDF output")
            if report['content_quality_checks'].get('has_markdown_artifacts'):
                recommendations.append("Clean markdown artifacts from content")
            if not report['reference_checks'].get('vancouver_format'):
                recommendations.append("Format references in Vancouver style")
            if report['reference_checks'].get('count') < 50:
                recommendations.append(f"Add more references (need {50 - report['reference_checks'].get('count', 0)} more)")

        for rec in recommendations:
            output += f"• {rec}\n"

        output += """
═══════════════════════════════════════════════════════════════════════
"""

        return output


# Initialize globally
sop_validator = SOPComplianceValidator()
