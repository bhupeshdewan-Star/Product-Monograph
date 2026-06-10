from __future__ import annotations

import json
from typing import Dict

from config import MEDICAL_DISCLAIMER
from src.services.evidence_retrieval.traceability import collect_source_markers, markers_for_section


def build_section_prompt(
    molecule_name: str,
    section_name: str,
    section_spec: Dict,
    research_sources: Dict,
    sop_constraints: str,
) -> str:
    if _use_local_compact_prompt(research_sources):
        return build_local_compact_section_prompt(
            molecule_name=molecule_name,
            section_name=section_name,
            section_spec=section_spec,
            research_sources=research_sources,
            sop_constraints=sop_constraints,
        )
    evidence_context = research_sources.get("evidence_context") or research_sources.get("formatted_text", "")
    evidence_package = research_sources.get("evidence_package", {})
    traceability_markers = collect_source_markers(evidence_package)
    section_markers = markers_for_section(section_name, traceability_markers)
    source_summary = {
        "total_articles": research_sources.get("total_articles", 0),
        "pubmed": len(research_sources.get("sources", {}).get("pubmed", [])),
        "fda": len(research_sources.get("sources", {}).get("fda", [])),
        "ema": len(research_sources.get("sources", {}).get("ema", [])),
        "clinicaltrials": len(research_sources.get("sources", {}).get("clinicaltrials", [])),
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

EVIDENCE PACKAGE:
{json.dumps(evidence_package, indent=2, default=str)[:4500]}

EVIDENCE CONTEXT:
{evidence_context[:4500]}

TRACEABILITY REQUIREMENTS:
- Every scientific sentence must carry one or more source identifiers in square brackets.
- Use PMID tags for PubMed-backed statements.
- Use FDA tags that include the FDA label identifier and relevant section for label-backed statements.
- Use NCT tags for ClinicalTrials.gov-backed statements.
- If evidence is incomplete, state the limitation rather than inventing unsupported claims.
- Available source markers for this section: {", ".join(section_markers) if section_markers else "none"}

REQUIREMENTS:
- Write clear, evidence-based medical content
- Use markdown section headers
- Keep the section scoped to the requested topic
- Prefer concise clinical language over marketing language
- Include caveats where evidence is limited

{_section_guidance(section_name)}

Return only the section content.
"""


def build_local_compact_section_prompt(
    molecule_name: str,
    section_name: str,
    section_spec: Dict,
    research_sources: Dict,
    sop_constraints: str,
) -> str:
    evidence_context = research_sources.get("evidence_context") or research_sources.get("formatted_text", "")
    evidence_package = research_sources.get("evidence_package", {})
    retrieved_with = research_sources.get("retrieved_with", {}) or {}
    compact_chars = int(retrieved_with.get("local_compact_evidence_chars") or 6000)
    section_markers = markers_for_section(section_name, collect_source_markers(evidence_package))
    source_summary = {
        "total_articles": research_sources.get("total_articles", 0),
        "local": len(research_sources.get("sources", {}).get("local", [])),
        "pubmed": len(research_sources.get("sources", {}).get("pubmed", [])),
        "fda": len(research_sources.get("sources", {}).get("fda", [])),
        "ema": len(research_sources.get("sources", {}).get("ema", [])),
        "clinicaltrials": len(research_sources.get("sources", {}).get("clinicaltrials", [])),
    }
    return f"""
You are drafting a concise pharmaceutical product monograph section for a local model first draft.

MOLECULE: {molecule_name}
SECTION: {section_spec.get('title', section_name)}

Write a compact, evidence-based section in approximately 120-260 words.
Do not include raw JSON, long SOP instructions, or a verbose regulatory appendix.
Use only the compact evidence summary below. Keep the language clinical and concise.
Every scientific statement must carry a source identifier when supported.

SOURCE SUMMARY:
{json.dumps(source_summary, indent=2)}

AVAILABLE SOURCE MARKERS:
{", ".join(section_markers) if section_markers else "none"}

COMPACT EVIDENCE SUMMARY (first {compact_chars} characters max):
{evidence_context[:compact_chars]}

CORE WRITING RULES:
- Keep the section concise and professionally worded.
- Use only evidence from the compact summary and selected source markers.
- Prefer short paragraphs and simple bullet points where useful.
- If evidence is limited, state that limitation clearly.
- Do not invent citations, tables, or figures.

{_local_section_guidance(section_name)}

Return only the requested section content.
"""


def build_references_prompt(molecule_name: str, research_sources: Dict) -> str:
    evidence_context = research_sources.get("evidence_context") or research_sources.get("formatted_text", "")
    return f"""
Format references for a pharmaceutical monograph using only the retrieved evidence.

MOLECULE: {molecule_name}
SOURCE DATA:
{json.dumps(research_sources.get('sources', {}), default=str)[:3000]}

EVIDENCE CONTEXT:
{evidence_context[:3000]}

Write a concise Vancouver-style references section.
Do not fabricate citations or source details.
Return only the reference list.
"""


def build_executive_summary_prompt(molecule_name: str, specialty: str, sources: Dict) -> str:
    if _use_local_compact_prompt(sources):
        return build_local_compact_executive_summary_prompt(molecule_name, specialty, sources)
    article_count = sources.get("total_articles", 0)
    audience = specialty.strip() if specialty and specialty.strip() else "general clinical practice"
    evidence_context = sources.get("evidence_context") or sources.get("formatted_text", "")
    return f"""
Create an executive summary for {molecule_name}.

Target audience: {audience}
Evidence base: {article_count} total source(s)
Evidence context:
{evidence_context[:3500]}

Requirements:
- 3 to 4 short paragraphs
- Clear molecule-centric clinical focus
- Include strengths, safety notes, and practical considerations
- Avoid marketing language
- End with a short practice summary
- State evidence limitations clearly if the live evidence package is incomplete

Return only the executive summary content.
"""


def build_local_compact_executive_summary_prompt(molecule_name: str, specialty: str, sources: Dict) -> str:
    article_count = sources.get("total_articles", 0)
    audience = specialty.strip() if specialty and specialty.strip() else "general clinical practice"
    evidence_context = sources.get("evidence_context") or sources.get("formatted_text", "")
    retrieved_with = sources.get("retrieved_with", {}) or {}
    compact_chars = int(retrieved_with.get("local_compact_evidence_chars") or 6000)
    return f"""
Create a concise executive summary for {molecule_name}.

Target audience: {audience}
Evidence base: {article_count} total source(s)

Use only the compact evidence summary below.
Write 2 to 3 short paragraphs, keep the tone clinical, and avoid long appendix-style text.
State evidence limitations clearly if the evidence package is limited.

COMPACT EVIDENCE SUMMARY (first {compact_chars} characters max):
{evidence_context[:compact_chars]}

Return only the executive summary content.
"""


def build_quick_reference_prompt(molecule_name: str, specialty: str) -> str:
    audience = specialty.strip() if specialty and specialty.strip() else "general clinical practice"
    return f"""
Create a concise clinical quick-reference box for {molecule_name}.

Target audience: {audience}

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


def _local_section_guidance(section_name: str) -> str:
    guidance = {
        "introduction": "- Give a brief clinical overview and why the molecule matters.",
        "rationale": "- Explain the clinical need it addresses in 1-2 short paragraphs.",
        "pharmacology": "- Summarize mechanism and relevant pharmacodynamic facts concisely.",
        "pharmacokinetics": "- Cover absorption, distribution, metabolism, and elimination briefly.",
        "clinical_efficacy": "- Focus on key evidence and outcomes in compact form.",
        "safety": "- Summarize common, important, and serious safety points with citations.",
        "dosage": "- Describe usual dosing and major adjustments without excessive detail.",
        "contraindications": "- List the main situations where use is inappropriate.",
        "drug_interactions": "- Summarize the most important interaction risks.",
    }
    return guidance.get(section_name, "- Follow the section scope carefully and remain concise.")


def _use_local_compact_prompt(research_sources: Dict) -> bool:
    retrieved_with = research_sources.get("retrieved_with", {}) or {}
    return bool(
        retrieved_with.get("local_compact_prompt_mode")
        or retrieved_with.get("local_section_generation_mode")
    )
