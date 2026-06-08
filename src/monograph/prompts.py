from __future__ import annotations

import json
from typing import Dict

from config import MEDICAL_DISCLAIMER


def build_section_prompt(
    molecule_name: str,
    section_name: str,
    section_spec: Dict,
    research_sources: Dict,
    sop_constraints: str,
) -> str:
    source_summary = {
        "total_articles": research_sources.get("total_articles", 0),
        "pubmed": len(research_sources.get("sources", {}).get("pubmed", [])),
        "fda": len(research_sources.get("sources", {}).get("fda", [])),
        "open_access": len(research_sources.get("sources", {}).get("open_access", [])),
    }
    return f"""
You are writing a pharmaceutical product monograph section.

MOLECULE: {molecule_name}
SECTION: {section_spec.get('title', section_name)}

SOP CONSTRAINTS:
{sop_constraints}

SOURCE SUMMARY:
{json.dumps(source_summary, indent=2)}

SOURCE EXCERPT:
{research_sources.get('formatted_text', '')[:3000]}

REQUIREMENTS:
- Write clear, evidence-based medical content
- Use markdown section headers
- Keep the section scoped to the requested topic
- Prefer concise clinical language over marketing language
- Include caveats where evidence is limited

{_section_guidance(section_name)}

Return only the section content.
"""


def build_references_prompt(molecule_name: str, research_sources: Dict) -> str:
    return f"""
Format references for a pharmaceutical monograph.

MOLECULE: {molecule_name}
SOURCE DATA:
{json.dumps(research_sources.get('sources', {}), default=str)[:3000]}

Write a concise Vancouver-style references section.
Return only the reference list.
"""


def build_executive_summary_prompt(molecule_name: str, specialty: str, sources: Dict) -> str:
    article_count = sources.get("total_articles", 0)
    return f"""
Create an executive summary for {molecule_name}.

Target specialty: {specialty}
Evidence base: {article_count} total source(s)

Requirements:
- 3 to 4 short paragraphs
- Clear clinical focus for the target specialty
- Include strengths, safety notes, and practical considerations
- Avoid marketing language
- End with a short practice summary

Return only the executive summary content.
"""


def build_quick_reference_prompt(molecule_name: str, specialty: str) -> str:
    return f"""
Create a concise clinical quick-reference box for {molecule_name}.

Target specialty: {specialty}

Requirements:
- Key mechanism
- Common use cases
- Monitoring considerations
- Important cautions
- Keep it scannable

Return only the quick-reference content.
"""


def build_disclaimer_block() -> str:
    return MEDICAL_DISCLAIMER


def _section_guidance(section_name: str) -> str:
    guidance = {
        "introduction": "- Summarize the clinical context and why the molecule matters.",
        "rationale": "- Explain why the product is used and what problem it addresses.",
        "pharmacology": "- Explain mechanism, pharmacodynamics, and comparative context.",
        "pharmacokinetics": "- Cover absorption, distribution, metabolism, and elimination.",
        "clinical_efficacy": "- Summarize efficacy by indication and key outcomes.",
        "safety": "- Summarize adverse events, contraindications, and monitoring.",
        "dosage": "- Describe standard dosing and adjustments when relevant.",
        "contraindications": "- List patient groups or situations where use is inappropriate.",
        "drug_interactions": "- Summarize relevant interaction risks and management.",
    }
    return guidance.get(section_name, "- Follow the section scope carefully.")
