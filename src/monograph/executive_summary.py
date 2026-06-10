from __future__ import annotations

from typing import Optional

from src.agents.providers.base import ProviderConfig, ProviderError
from src.agents.providers.provider_factory import create_provider
from src.monograph.fallback_content import (
    build_fallback_executive_summary,
    build_fallback_quick_reference,
    build_fallback_specialty_pearl,
)
from src.monograph.prompts import build_executive_summary_prompt


class ExecutiveSummaryGenerator:
    """Generates clinical executive summaries without provider lock-in."""

    def __init__(self, provider_config: Optional[ProviderConfig] = None):
        self.provider_config = provider_config

    def generate_executive_summary(
        self,
        molecule_name: str,
        sources: dict,
        hcp_specialty: str = "",
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
                if getattr(cfg, "strict", False):
                    raise
                return self._fallback_summary(molecule_name, sources, hcp_specialty, str(exc))
        return self._fallback_summary(molecule_name, sources, hcp_specialty)

    def generate_hcp_specialty_summary(self, molecule_name: str, specialty: str) -> str:
        return build_fallback_specialty_pearl(molecule_name, specialty)

    def generate_quick_reference_box(self, molecule_name: str) -> str:
        return build_fallback_quick_reference(molecule_name)

    def _fallback_summary(
        self,
        molecule_name: str,
        sources: dict,
        hcp_specialty: str,
        error: Optional[str] = None,
    ) -> str:
        return build_fallback_executive_summary(molecule_name, sources, hcp_specialty or "", error)


executive_summary_generator = ExecutiveSummaryGenerator()
