from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from config import SOP_SECTIONS
from src.agents.providers.base import ProviderConfig, ProviderError
from src.agents.providers.provider_factory import create_provider
from src.monograph.prompts import build_references_prompt, build_section_prompt
from src.monograph.sop_engine import sop_engine


def _estimate_tokens(text: str) -> int:
    words = max(1, len(text.split()))
    return int(words * 1.25)


def _source_titles(research_sources: Dict, source_name: str, limit: int = 5) -> list[str]:
    items = research_sources.get("sources", {}).get(source_name, [])
    titles = []
    for item in items[:limit]:
        title = item.get("title") or item.get("drug_name") or item.get("source") or ""
        if title:
            titles.append(str(title))
    return titles


class ProductMonographGenerator:
    """Generate product monographs with optional provider-agnostic LLM refinement."""

    def __init__(self, provider_config: Optional[ProviderConfig] = None):
        self.provider_config = provider_config
        self.sop_constraints = sop_engine.get_sop_prompt_injection()
        self.generation_log: list[dict] = []

    def generate_monograph(
        self,
        molecule_name: str,
        research_sources: Dict,
        provider_config: Optional[ProviderConfig] = None,
    ) -> Dict:
        started_at = time.time()
        cfg = provider_config or self.provider_config

        monograph = {
            "molecule_name": molecule_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": {},
            "generation_time": 0.0,
            "total_tokens_used": 0,
            "quality_scores": {},
            "provider_used": cfg.provider if cfg else None,
            "model_used": cfg.model if cfg else None,
            "disclaimer": "This document is a draft for medical/regulatory review only.",
            "source_summary": {
                "total_articles": research_sources.get("total_articles", 0),
                "pubmed": len(research_sources.get("sources", {}).get("pubmed", [])),
                "fda": len(research_sources.get("sources", {}).get("fda", [])),
                "open_access": len(research_sources.get("sources", {}).get("open_access", [])),
            },
        }

        section_names = [name for name in SOP_SECTIONS.keys() if name != "references"]
        with ThreadPoolExecutor(max_workers=min(4, max(1, len(section_names)))) as executor:
            futures = {
                executor.submit(
                    self.generate_section,
                    section_name,
                    molecule_name,
                    research_sources,
                    cfg,
                ): section_name
                for section_name in section_names
            }

            for future in as_completed(futures):
                section_name = futures[future]
                try:
                    section_content, tokens_used = future.result()
                    monograph["sections"][section_name] = section_content
                    monograph["total_tokens_used"] += tokens_used
                except Exception as exc:
                    self.generation_log.append(
                        {"section": section_name, "status": "error", "error": str(exc)}
                    )
                    monograph["sections"][section_name] = self._fallback_section(
                        section_name, molecule_name, research_sources
                    )

        references, tokens_used = self.generate_references(
            molecule_name,
            research_sources,
            provider_config=cfg,
        )
        monograph["sections"]["references"] = references
        monograph["total_tokens_used"] += tokens_used
        monograph["generation_time"] = round(time.time() - started_at, 2)
        monograph["quality_scores"] = self._quality_score(monograph["sections"])
        return monograph

    def generate_section(
        self,
        section_name: str,
        molecule_name: str,
        research_sources: Dict,
        provider_config: Optional[ProviderConfig] = None,
    ) -> Tuple[str, int]:
        section_spec = sop_engine.sections.get(section_name, {})
        if not section_spec:
            return "", 0

        prompt = build_section_prompt(
            molecule_name=molecule_name,
            section_name=section_name,
            section_spec=section_spec,
            research_sources=research_sources,
            sop_constraints=self.sop_constraints,
        )

        if not provider_config or not provider_config.provider:
            content = self._fallback_section(section_name, molecule_name, research_sources)
            tokens_used = _estimate_tokens(content)
            self.generation_log.append(
                {"section": section_name, "status": "fallback", "tokens": tokens_used}
            )
            return content, tokens_used

        try:
            provider = create_provider(provider_config)
            content = provider.generate(
                prompt=prompt,
                system_prompt="You are a medical writer. Return only the requested section.",
                model=provider_config.model,
                api_key=provider_config.api_key,
                temperature=provider_config.temperature,
            )
            tokens_used = _estimate_tokens(prompt + "\n" + content)
            self.generation_log.append(
                {"section": section_name, "status": "success", "tokens": tokens_used}
            )
            return content, tokens_used
        except (ProviderError, ValueError, TypeError) as exc:
            fallback = self._fallback_section(section_name, molecule_name, research_sources)
            tokens_used = _estimate_tokens(fallback)
            self.generation_log.append(
                {
                    "section": section_name,
                    "status": "fallback",
                    "error": str(exc),
                    "tokens": tokens_used,
                }
            )
            return fallback, tokens_used

    def generate_references(
        self,
        molecule_name: str,
        research_sources: Dict,
        provider_config: Optional[ProviderConfig] = None,
    ) -> Tuple[str, int]:
        prompt = build_references_prompt(molecule_name, research_sources)
        if provider_config and provider_config.provider:
            try:
                provider = create_provider(provider_config)
                content = provider.generate(
                    prompt=prompt,
                    system_prompt="You format references in Vancouver style. Return only the references.",
                    model=provider_config.model,
                    api_key=provider_config.api_key,
                    temperature=provider_config.temperature,
                )
                tokens_used = _estimate_tokens(prompt + "\n" + content)
                return content, tokens_used
            except (ProviderError, ValueError, TypeError):
                pass

        references = self._fallback_references(molecule_name, research_sources)
        return references, _estimate_tokens(references)

    def _fallback_section(
        self,
        section_name: str,
        molecule_name: str,
        research_sources: Dict,
    ) -> str:
        section_title = SOP_SECTIONS.get(section_name, {}).get(
            "title", section_name.replace("_", " ").title()
        )
        pubmed_titles = _source_titles(research_sources, "pubmed")
        fda_titles = _source_titles(research_sources, "fda")
        open_access_titles = _source_titles(research_sources, "open_access")
        titles = pubmed_titles + fda_titles + open_access_titles
        title_block = "\n".join(f"- {title}" for title in titles[:5]) or "- No source titles available"

        body_map = {
            "introduction": (
                f"{molecule_name} is reviewed for its clinical relevance, evidence base, "
                "and role in practice."
            ),
            "rationale": (
                f"This section explains why {molecule_name} is used and what clinical need it addresses."
            ),
            "pharmacology": (
                f"This section summarizes the mechanism of action, pharmacodynamics, and related context for {molecule_name}."
            ),
            "pharmacokinetics": (
                f"This section covers absorption, distribution, metabolism, elimination, and special-population considerations."
            ),
            "clinical_efficacy": (
                f"This section summarizes clinical outcomes, trial signals, and the evidence base supporting {molecule_name}."
            ),
            "safety": (
                f"This section summarizes adverse events, contraindications, and monitoring considerations for {molecule_name}."
            ),
            "dosage": (
                f"This section describes a practical dosing framework and adjustments where evidence is available."
            ),
            "contraindications": (
                f"This section lists situations where {molecule_name} should be avoided or used with caution."
            ),
            "drug_interactions": (
                f"This section highlights relevant interaction risks and the need for monitoring or dose adjustment."
            ),
        }
        return (
            f"## {section_title}\n\n"
            f"{body_map.get(section_name, f'This section summarizes the available evidence for {molecule_name}.')}\n\n"
            f"### Evidence Snapshot\n"
            f"- PubMed sources reviewed: {len(research_sources.get('sources', {}).get('pubmed', []))}\n"
            f"- FDA sources reviewed: {len(research_sources.get('sources', {}).get('fda', []))}\n"
            f"- Open access sources reviewed: {len(research_sources.get('sources', {}).get('open_access', []))}\n\n"
            f"### Source Themes\n{title_block}\n\n"
            f"_Fallback content generated because no runtime LLM provider was supplied._"
        )

    def _fallback_references(self, molecule_name: str, research_sources: Dict) -> str:
        lines = [f"## References", ""]
        references = []
        for source_name in ("pubmed", "fda", "open_access"):
            for item in research_sources.get("sources", {}).get(source_name, [])[:10]:
                title = item.get("title") or item.get("drug_name") or item.get("source") or ""
                url = item.get("url", "")
                if title:
                    references.append(f"- {title}{f' ({url})' if url else ''}")

        if not references:
            references.append(
                f"- No reference data was available for {molecule_name}. Add source records to populate this section."
            )

        lines.extend(references)
        return "\n".join(lines)

    def _quality_score(self, sections: Dict[str, str]) -> Dict[str, float]:
        scores = {}
        for section_name, content in sections.items():
            score = 100.0
            if len(content.split()) < 120 and section_name not in {"references", "contraindications"}:
                score -= 15.0
            if "fallback" in content.lower():
                score -= 10.0
            scores[section_name] = max(0.0, round(score, 1))
        return scores


ClaudeSynthesisEngine = ProductMonographGenerator
synthesis_engine = ProductMonographGenerator()
