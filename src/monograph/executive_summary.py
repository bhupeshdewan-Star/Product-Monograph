from __future__ import annotations

from typing import Optional

from src.agents.providers.base import ProviderConfig, ProviderError
from src.agents.providers.provider_factory import create_provider
from src.monograph.prompts import (
    build_executive_summary_prompt,
)


class ExecutiveSummaryGenerator:
    """Generates clinical executive summaries without provider lock-in."""

    def __init__(self, provider_config: Optional[ProviderConfig] = None):
        self.provider_config = provider_config

    def generate_executive_summary(
        self,
        molecule_name: str,
        sources: dict,
        hcp_specialty: str = "General Practitioner",
        provider_config: Optional[ProviderConfig] = None,
    ) -> str:
        cfg = provider_config or self.provider_config
        prompt = build_executive_summary_prompt(molecule_name, hcp_specialty, sources)
        if cfg and cfg.provider:
            try:
                provider = create_provider(cfg)
                return provider.generate(
                    prompt=prompt,
                    system_prompt=(
                        "You write concise, evidence-based clinical summaries. "
                        "Return only the requested content."
                    ),
                    model=cfg.model,
                    api_key=cfg.api_key,
                    temperature=cfg.temperature,
                )
            except (ProviderError, ValueError, TypeError) as exc:
                return self._fallback_summary(molecule_name, sources, hcp_specialty, str(exc))
        return self._fallback_summary(molecule_name, sources, hcp_specialty)

    def generate_hcp_specialty_summary(self, molecule_name: str, specialty: str) -> str:
        return self._fallback_specialty_pearl(molecule_name, specialty)

    def generate_quick_reference_box(self, molecule_name: str) -> str:
        return self._fallback_quick_reference(molecule_name)

    def _fallback_summary(
        self,
        molecule_name: str,
        sources: dict,
        hcp_specialty: str,
        error: Optional[str] = None,
    ) -> str:
        article_count = sources.get("total_articles", 0)
        pubmed_articles = len(sources.get("sources", {}).get("pubmed", []))
        fda_articles = len(sources.get("sources", {}).get("fda", []))
        note = f"\n\n_Model refinement skipped: {error}_" if error else ""
        return (
            f"## Executive Summary: {molecule_name}\n\n"
            f"{molecule_name} is reviewed for use in {hcp_specialty} practice.\n\n"
            f"Evidence base: {article_count} total source(s) "
            f"({pubmed_articles} PubMed, {fda_articles} FDA).\n\n"
            f"### Clinical Overview\n"
            f"- Summarize the main mechanism and therapeutic role of {molecule_name}.\n"
            f"- Highlight the most relevant clinical use cases for {hcp_specialty} care.\n\n"
            f"### Safety and Monitoring\n"
            f"- Summarize key safety considerations and monitoring priorities.\n"
            f"- Call out any important contraindications or population-specific cautions.\n\n"
            f"### Practice Summary\n"
            f"- Use the most clinically relevant evidence when counseling patients.\n"
            f"- Balance benefit, safety, and operational simplicity in the target setting.{note}"
        )

    def _fallback_specialty_pearl(self, molecule_name: str, specialty: str) -> str:
        return (
            f"## Key Clinical Pearls for {specialty}s\n\n"
            f"- {molecule_name} should be considered in the context of the target specialty and its monitoring burden.\n"
            f"- Review interactions, contraindications, and organ-function adjustments before prescribing.\n"
            f"- Confirm that the evidence base matches the clinical use case.\n\n"
            f"## Quick Reference\n\n"
            f"- Mechanism: summarize the primary clinical mechanism.\n"
            f"- Indication: verify the evidence-supported use.\n"
            f"- Dose: confirm dose and route from authoritative sources.\n"
            f"- Monitoring: review adverse effects, labs, and follow-up timing.\n"
            f"- Cautions: screen for contraindications and interactions.\n"
        )

    def _fallback_quick_reference(self, molecule_name: str) -> str:
        return (
            f"## {molecule_name.upper()} - Quick Reference\n\n"
            f"- Mechanism: summarize the primary clinical mechanism.\n"
            f"- Indication: verify the approved or evidence-supported use.\n"
            f"- Dose: confirm dose and route from authoritative sources.\n"
            f"- Monitoring: review adverse effects, labs, and follow-up timing.\n"
            f"- Cautions: screen for contraindications and interactions.\n"
        )


executive_summary_generator = ExecutiveSummaryGenerator()
