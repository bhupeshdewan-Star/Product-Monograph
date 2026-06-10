"""
Markdown Cleaner
Removes markdown formatting artifacts from generated text
Ensures professional output without ## ** - etc.
"""
import re

class MarkdownCleaner:
    """Cleans markdown formatting from text"""

    def clean_text(self, text: str) -> str:
        """
        Remove all markdown formatting from text

        Removes:
        - ## (headers)
        - ** (bold)
        - __ (underline)
        - * (italics)
        - _ (italics)
        - [text](url) (links)
        - - (bullet points)
        - > (blockquotes)
        - ` (code)
        """

        if not text:
            return ""

        # Remove headers (##, ###, ####, etc.)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)

        # Remove italics (*text* or _text_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)

        # Remove links [text](url)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

        # Remove inline code (`code`)
        text = re.sub(r'`(.+?)`', r'\1', text)

        # Remove code blocks (```code```)
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Remove blockquotes (> text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # Remove bullet points (- text)
        # But preserve the actual text
        text = re.sub(r'^\s*[-•*]\s+', '', text, flags=re.MULTILINE)

        # Remove numbered lists (1. text)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # Remove horizontal rules (---, ***, ___)
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

        # Clean up extra whitespace
        # Remove multiple spaces
        text = re.sub(r' {2,}', ' ', text)

        # Remove multiple newlines (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove leading/trailing whitespace from each line
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)

        # Remove leading/trailing whitespace overall
        text = text.strip()

        return text

    def clean_section(self, section_name: str, content: str) -> str:
        """Clean a section of text"""
        # Clean the main content
        cleaned = self.clean_text(content)
        return cleaned

    def clean_all_sections(self, sections_dict: dict) -> dict:
        """Clean all sections in a monograph"""
        cleaned_sections = {}

        for section_name, content in sections_dict.items():
            cleaned_sections[section_name] = self.clean_section(section_name, content)

        return cleaned_sections

    def extract_clean_paragraphs(self, text: str) -> list:
        """Extract clean paragraphs from text"""
        # Clean the text first
        cleaned = self.clean_text(text)

        # Split into paragraphs
        paragraphs = cleaned.split('\n\n')

        # Remove empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def clean_and_structure(self, text: str) -> dict:
        """Clean text and structure into paragraphs"""
        paragraphs = self.extract_clean_paragraphs(text)

        return {
            'cleaned_text': '\n\n'.join(paragraphs),
            'paragraph_count': len(paragraphs),
            'paragraphs': paragraphs
        }

    def validate_cleaned_output(self, text: str) -> dict:
        """Validate that markdown has been properly removed"""
        issues = []

        # Check for remaining markdown patterns
        patterns = {
            'headers': r'^#+\s',
            'bold': r'\*\*|\__',
            'italics': r'(?<![*_])\*(?![*_])|_(?![_])',
            'links': r'\[.+?\]\(.+?\)',
            'code': r'`[^`]*`',
            'blockquotes': r'^>\s',
            'bullet_points': r'^\s*[-•]\s',
        }

        for issue_type, pattern in patterns.items():
            matches = re.findall(pattern, text, flags=re.MULTILINE)
            if matches:
                issues.append({
                    'type': issue_type,
                    'count': len(matches),
                    'examples': matches[:3]
                })

        is_clean = len(issues) == 0

        return {
            'is_clean': is_clean,
            'issue_count': len(issues),
            'issues': issues
        }

    def generate_cleaning_report(self, original: str, cleaned: str) -> str:
        """Generate report on cleaning process"""
        validation = self.validate_cleaned_output(cleaned)

        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║              MARKDOWN CLEANING VALIDATION REPORT                   ║
╠════════════════════════════════════════════════════════════════════╣

CLEANING STATUS: {'[OK] CLEAN' if validation['is_clean'] else '[ERROR] ISSUES FOUND'}

METRICS:
────────
Original Length: {len(original)} characters
Cleaned Length: {len(cleaned)} characters
Reduction: {len(original) - len(cleaned)} characters ({(1 - len(cleaned)/len(original))*100:.1f}%)

Original Paragraphs: {len(original.split(chr(10)+chr(10)))}
Cleaned Paragraphs: {len(cleaned.split(chr(10)+chr(10)))}

ISSUES FOUND: {validation['issue_count']}
"""

        if validation['issues']:
            report += "─────────────────────────────────────────────────────────────────────\n"
            for issue in validation['issues']:
                report += f"\n{issue['type'].upper()}:\n"
                report += f"  Count: {issue['count']}\n"
                report += f"  Examples: {', '.join([str(e) for e in issue['examples'][:2]])}\n"
        else:
            report += "─────────────────────────────────────────────────────────────────────\n"
            report += "[OK] NO MARKDOWN ARTIFACTS FOUND\n"

        report += """
SAMPLE OUTPUT (First 200 chars):
──────────────────────────────────
"""

        sample = cleaned[:200] + "..." if len(cleaned) > 200 else cleaned
        report += f"\n{sample}\n"

        report += """
═══════════════════════════════════════════════════════════════════════
"""

        return report


# Initialize globally
markdown_cleaner = MarkdownCleaner()
