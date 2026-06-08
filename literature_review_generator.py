"""
Literature Review Generator
Creates tabulated summaries of 20+ articles with Vancouver-style references
"""
from typing import List, Dict
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS

class LiteratureReviewGenerator:
    """Generates structured literature review tables from research articles"""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def generate_literature_table(self, molecule_name: str, articles: List[Dict]) -> str:
        """
        Generate a tabulated literature review with key findings
        Returns markdown table with: Author/Year | Study Type | Population | Key Findings | Evidence Level
        """

        if not articles:
            return "No articles available for literature review"

        # Prepare article summaries for Claude
        article_text = self._prepare_article_summaries(articles[:25])  # Top 25 articles

        prompt = f"""You are a pharmaceutical expert. Create a comprehensive literature review table for {molecule_name}.

ARTICLES DATA:
{article_text}

Create a detailed markdown table with these columns:
1. **Ref** - Vancouver style reference number [1], [2], etc.
2. **Author/Year** - First author and publication year
3. **Study Type** - RCT/Meta-analysis/Cohort/Case report/Review
4. **Patient Population** - N = sample size, patient type
5. **Key Findings** - Main outcomes and effect sizes (e.g., HbA1c reduction: 1.2%, CI 0.8-1.6%)
6. **Evidence Level** - 1A/1B/2/3/4
7. **Clinical Significance** - Brief conclusion (Positive/Neutral/Conflicting)

Format as a clean markdown table. Include 20-25 articles. For each article:
- Extract or infer realistic clinical data
- Include confidence intervals where applicable
- Assign evidence levels based on study design
- Highlight key clinical implications

Start with the table immediately, no introduction needed."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            table_content = message.content[0].text
            return table_content

        except Exception as e:
            return f"Error generating literature table: {str(e)}"

    def generate_vancouver_references(self, articles: List[Dict]) -> str:
        """
        Generate Vancouver-style references from articles
        Format: [#] Author(s). Title. Journal. Year;Volume(Issue):Pages.
        """

        if not articles:
            return "No references available"

        vancouver_refs = []

        for i, article in enumerate(articles[:25], 1):
            ref = self._format_vancouver_reference(article, i)
            vancouver_refs.append(ref)

        return "\n".join(vancouver_refs)

    def _format_vancouver_reference(self, article: Dict, ref_number: int) -> str:
        """Format single article as Vancouver style reference"""

        authors = article.get('authors', ['Unknown'])
        if isinstance(authors, list):
            # Format as "FirstA, LastA et al."
            first_authors = authors[:3]
            author_str = ", ".join(first_authors)
            if len(authors) > 3:
                author_str += " et al."
        else:
            author_str = str(authors)

        title = article.get('title', 'Unknown Title')
        journal = article.get('journal', article.get('source', 'Unknown Journal'))
        year = article.get('year', 'N/A')
        doi = article.get('doi', '')

        # Vancouver format: [#] Authors. Title. Journal. Year;Vol(Issue):Pages. doi.
        ref = f"[{ref_number}] {author_str}. {title}. {journal}. {year}."

        if doi:
            ref += f" doi:{doi}"

        return ref

    def _prepare_article_summaries(self, articles: List[Dict]) -> str:
        """Prepare article data for Claude processing"""

        text = ""
        for i, article in enumerate(articles, 1):
            text += f"\nArticle {i}:\n"
            text += f"- Title: {article.get('title', 'N/A')}\n"
            text += f"- Authors: {', '.join(article.get('authors', ['Unknown']))}\n"
            text += f"- Year: {article.get('year', 'N/A')}\n"
            text += f"- Journal: {article.get('journal', article.get('source', 'N/A'))}\n"
            text += f"- DOI: {article.get('doi', 'N/A')}\n"
            if article.get('indications'):
                text += f"- Indications: {article.get('indications')}\n"
            if article.get('adverse_reactions'):
                text += f"- Safety: {article.get('adverse_reactions')}\n"

        return text

    def generate_evidence_summary(self, molecule_name: str, articles: List[Dict]) -> str:
        """
        Generate a summary of evidence quality and gaps
        Analyzes distribution of evidence levels
        """

        prompt = f"""Analyze the evidence base for {molecule_name} based on these {len(articles)} articles:

{self._prepare_article_summaries(articles[:20])}

Provide:
1. **Evidence Quality Summary**
   - Number of Level 1A studies (RCTs/Meta-analyses)
   - Number of Level 1B studies (Large RCTs)
   - Number of Level 2-3 studies
   - Overall evidence strength

2. **Key Clinical Endpoints Supported by Evidence**
   - List primary indications with evidence level
   - Notable efficacy data
   - Safety profile summary

3. **Evidence Gaps**
   - Populations not well-studied
   - Outcomes needing more research
   - Drug interactions not adequately studied

4. **Strength of Recommendation**
   - Strong recommendation (consistent Level 1A evidence)
   - Moderate recommendation (Level 1B/2 evidence)
   - Weak recommendation (conflicting/limited evidence)

Format as sections with bullet points for clarity."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating evidence summary: {str(e)}"


# Initialize globally
literature_generator = LiteratureReviewGenerator()
