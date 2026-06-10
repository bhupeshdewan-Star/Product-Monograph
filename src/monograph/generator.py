from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from config import SOP_SECTIONS
from src.agents.providers.base import ProviderConfig, ProviderError
from src.agents.providers.provider_factory import create_provider
from src.monograph.fallback_content import (
    build_draft_placeholders,
    build_fallback_references,
    build_fallback_section,
)
from src.monograph.prompts import build_references_prompt, build_section_prompt
from src.monograph.sop_engine import sop_engine
from src.services.evidence_retrieval.traceability import (
    apply_section_traceability,
    build_traceability_appendix,
)


def _estimate_tokens(text: str) -> int:
    words = max(1, len(text.split()))
    return int(words * 1.25)


class ProductMonographGenerator:
    """Generate product monographs with optional provider-agnostic LLM refinement."""

    def __init__(self, provider_config: Optional[ProviderConfig] = None):
        self.provider_config = provider_config
        self.sop_constraints = sop_engine.get_sop_prompt_injection()
        self.generation_log: list[dict] = []
        self.last_generation_diagnostics: list[dict] = []

    def generate_monograph(
        self,
        molecule_name: str,
        research_sources: Dict,
        provider_config: Optional[ProviderConfig] = None,
    ) -> Dict:
        started_at = time.time()
        cfg = provider_config or self.provider_config
        generation_mode = self._resolve_generation_mode(cfg)
        self.last_generation_diagnostics = []

        monograph = {
            "molecule_name": molecule_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": {},
            "generation_time": 0.0,
            "total_tokens_used": 0,
            "quality_scores": {},
            "generation_mode": generation_mode,
            "generation_label": (
                getattr(cfg, "output_label", "")
                or (
                    "Demo draft generated from fallback/sample data."
                    if generation_mode == "demo"
                    else (
                        "Local model draft generated using retrieved evidence package."
                        if generation_mode == "local"
                        else "AI-generated draft for expert review."
                    )
                )
            ),
            "provider_used": cfg.provider if cfg else None,
            "model_used": cfg.model if cfg else None,
            "disclaimer": "This document is a draft for medical/regulatory review only.",
            "draft_placeholders": build_draft_placeholders(molecule_name),
            "provider_request_diagnostics": [],
            "source_summary": {
                "total_articles": research_sources.get("total_articles", 0),
                "pubmed": len(research_sources.get("sources", {}).get("pubmed", [])),
                "fda": len(research_sources.get("sources", {}).get("fda", [])),
                "open_access": len(research_sources.get("sources", {}).get("open_access", [])),
            },
        }

        local_prompt_mode = bool((research_sources.get("retrieved_with") or {}).get("local_compact_prompt_mode"))
        local_section_generation_mode = bool((research_sources.get("retrieved_with") or {}).get("local_section_generation_mode"))
        section_names = self._section_generation_order(local_prompt_mode or local_section_generation_mode)

        if generation_mode == "local" and (local_prompt_mode or local_section_generation_mode):
            for section_name in section_names:
                try:
                    section_content, tokens_used = self.generate_section(
                        section_name,
                        molecule_name,
                        research_sources,
                        cfg,
                    )
                    monograph["sections"][section_name] = section_content
                    monograph["total_tokens_used"] += tokens_used
                except Exception as exc:
                    self.generation_log.append(
                        {"section": section_name, "status": "error", "error": str(exc)}
                    )
                    monograph["sections"][section_name] = self._fallback_section(
                        section_name, molecule_name, research_sources
                    )
        else:
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
        monograph["sections"], traceability_rows, retrieved_at = self.build_traceability_layers(
            monograph["sections"],
            research_sources,
        )
        if monograph.get("executive_summary"):
            evidence_package = research_sources.get("evidence_package") or {}
            summary_sections, summary_rows, _ = apply_section_traceability(
                {"executive_summary": monograph["executive_summary"]},
                evidence_package,
            )
            monograph["executive_summary"] = summary_sections.get("executive_summary", monograph["executive_summary"])
            traceability_rows.extend(summary_rows)
        monograph["evidence_traceability"] = traceability_rows
        monograph["traceability_appendix"] = build_traceability_appendix(
            traceability_rows,
            retrieved_at or datetime.now(timezone.utc).isoformat(),
        )
        monograph["sections"]["evidence_traceability_appendix"] = monograph["traceability_appendix"]
        monograph["provider_request_diagnostics"] = list(self.last_generation_diagnostics)
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
                max_completion_tokens=getattr(provider_config, "max_completion_tokens", None),
            )
            diagnostics = getattr(provider, "last_request_diagnostics", {}) or {}
            if diagnostics:
                self.last_generation_diagnostics.append(
                    {
                        "section": section_name,
                        "provider": provider_config.provider,
                        "model": provider_config.model,
                        "request_diagnostics": diagnostics,
                    }
                )
            tokens_used = _estimate_tokens(prompt + "\n" + content)
            self.generation_log.append(
                {"section": section_name, "status": "success", "tokens": tokens_used}
            )
            return content, tokens_used
        except (ProviderError, ValueError, TypeError) as exc:
            if provider_config and getattr(provider_config, "strict", False):
                self.generation_log.append(
                    {
                        "section": section_name,
                        "status": "error",
                        "error": str(exc),
                        "strict": True,
                    }
                )
                raise
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
            diagnostics = getattr(provider, "last_request_diagnostics", {}) if "provider" in locals() else {}
            if diagnostics:
                self.last_generation_diagnostics.append(
                    {
                        "section": section_name,
                        "provider": provider_config.provider,
                        "model": provider_config.model,
                        "request_diagnostics": diagnostics,
                    }
                )
            return fallback, tokens_used

    def generate_references(
        self,
        molecule_name: str,
        research_sources: Dict,
        provider_config: Optional[ProviderConfig] = None,
    ) -> Tuple[str, int]:
        evidence_references = research_sources.get("evidence_references")
        if evidence_references:
            return evidence_references, _estimate_tokens(evidence_references)
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
                    max_completion_tokens=getattr(provider_config, "max_completion_tokens", None),
                )
                tokens_used = _estimate_tokens(prompt + "\n" + content)
                return content, tokens_used
            except (ProviderError, ValueError, TypeError):
                if provider_config and getattr(provider_config, "strict", False):
                    raise

        references = self._fallback_references(molecule_name, research_sources)
        return references, _estimate_tokens(references)

    def _fallback_section(
        self,
        section_name: str,
        molecule_name: str,
        research_sources: Dict,
    ) -> str:
        return build_fallback_section(section_name, molecule_name, research_sources)

    def _fallback_references(self, molecule_name: str, research_sources: Dict) -> str:
        return build_fallback_references(molecule_name, research_sources)

    def _quality_score(self, sections: Dict[str, str]) -> Dict[str, float]:
        scores = {}
        for section_name, content in sections.items():
            score = 100.0
            if len(content.split()) < 120 and section_name not in {"references", "contraindications"}:
                score -= 15.0
            scores[section_name] = max(0.0, round(score, 1))
        return scores

    @staticmethod
    def _section_generation_order(local_mode: bool) -> list[str]:
        base_order = [name for name in SOP_SECTIONS.keys() if name != "references"]
        if not local_mode:
            return base_order
        priority = ["introduction", "pharmacology", "pharmacokinetics", "safety", "dosage"]
        ordered = [name for name in priority if name in base_order]
        ordered.extend([name for name in base_order if name not in ordered])
        return ordered

    @staticmethod
    def _resolve_generation_mode(provider_config: Optional[ProviderConfig]) -> str:
        if not provider_config:
            return "demo"
        base_url = getattr(provider_config, "base_url", None) or ""
        provider = getattr(provider_config, "provider", "")
        if base_url and any(token in base_url.lower() for token in ("localhost", "127.0.0.1", "0.0.0.0", "::1")):
            return "local"
        if provider == "openai" and base_url:
            return "local"
        return "ai"

    def build_traceability_layers(self, sections: Dict[str, str], research_sources: Dict) -> tuple[Dict[str, str], list[dict], str]:
        evidence_package = research_sources.get("evidence_package") or {}
        if not evidence_package and research_sources.get("sources"):
            evidence_package = {
                "retrieved_at": research_sources.get("retrieved_at") or datetime.now(timezone.utc).isoformat(),
                "sources": research_sources.get("sources", {}),
            }
        if not evidence_package:
            return sections, [], ""
        annotated_sections, traceability_rows, retrieved_at = apply_section_traceability(
            sections,
            evidence_package,
        )
        return annotated_sections, traceability_rows, retrieved_at


ProviderAgnosticSynthesisEngine = ProductMonographGenerator
synthesis_engine = ProductMonographGenerator()
