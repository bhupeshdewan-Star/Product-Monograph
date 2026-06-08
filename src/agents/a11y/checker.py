from __future__ import annotations

import logging
from typing import Any, Optional

from ..providers.base import ProviderConfig, ProviderError
from ..providers.provider_factory import create_provider
from ..utils import extract_json_object, merge_unique_issues, score_from_issues, truncate_text
from ..web.fetcher import fetch_url
from ..web.parser import parse_page_snapshot
from .rules import evaluate_accessibility

logger = logging.getLogger(__name__)


def _llm_refine_accessibility(
    *,
    snapshot: dict,
    heuristics: dict,
    provider_config: ProviderConfig,
) -> dict:
    provider = create_provider(provider_config)
    system_prompt = (
        "You are a strict accessibility auditor. "
        "Return JSON only. Use current WCAG principles as the basis. "
        "Never invent issues that are not supported by the supplied evidence."
    )
    prompt = {
        "task": "Review the landing page accessibility evidence and return a JSON object with score, summary, issues, recommendations, and coverage_notes.",
        "page_snapshot": snapshot,
        "heuristic_findings": heuristics,
        "output_schema": {
            "score": "integer 0-100",
            "summary": "human readable string",
            "issues": [
                {
                    "id": "string",
                    "title": "string",
                    "severity": "critical|high|medium|low",
                    "category": "string",
                    "description": "string",
                    "impact": "string",
                    "evidence": ["string"],
                    "recommended_fixes": ["string"],
                    "wcag_references": ["string"],
                }
            ],
            "recommendations": ["string"],
            "coverage_notes": ["string"],
        },
        "constraints": [
            "JSON only",
            "Keep issues specific and evidence-based",
            "Do not exceed 10 issues unless necessary",
        ],
    }
    content = provider.generate(
        prompt=truncate_text(str(prompt), 14000),
        system_prompt=system_prompt,
        model=provider_config.model,
        api_key=provider_config.api_key,
        temperature=provider_config.temperature,
    )
    parsed = extract_json_object(content)
    if not isinstance(parsed, dict):
        raise ValueError("Accessibility model output must be a JSON object")
    return parsed


def check_accessibility(
    url: str,
    ai_provider: Optional[ProviderConfig] = None,
    *,
    fetcher=fetch_url,
) -> dict[str, Any]:
    page = fetcher(url)
    snapshot = parse_page_snapshot(page.html, page.final_url)
    heuristics = evaluate_accessibility(snapshot)

    issues = heuristics["issues"]
    score = heuristics["score"]
    summary = heuristics["summary"]
    recommendations = []
    for issue in issues:
        recommendations.extend(issue.get("recommended_fixes", []))
    recommendations = list(dict.fromkeys(recommendations))
    coverage_notes = list(heuristics.get("coverage_notes", []))
    provider_used = None
    model_used = None

    if ai_provider and ai_provider.provider:
        try:
            llm_result = _llm_refine_accessibility(
                snapshot=snapshot,
                heuristics=heuristics,
                provider_config=ai_provider,
            )
            issues = merge_unique_issues(issues, llm_result.get("issues", []))
            score = int(llm_result.get("score", score_from_issues(issues)))
            summary = str(llm_result.get("summary", summary))
            recommendations = list(
                dict.fromkeys(
                    recommendations + list(llm_result.get("recommendations", []))
                )
            )
            coverage_notes = list(
                dict.fromkeys(
                    coverage_notes + list(llm_result.get("coverage_notes", []))
                )
            )
            provider_used = ai_provider.provider
            model_used = ai_provider.model
            logger.info("Accessibility analysis refined with %s", ai_provider.provider)
        except (ProviderError, ValueError, TypeError) as exc:
            coverage_notes.append(f"LLM refinement skipped: {exc}")
            logger.warning("Accessibility refinement failed: %s", exc)

    return {
        "success": True,
        "audit_type": "accessibility",
        "url": url,
        "final_url": page.final_url,
        "score": score,
        "summary": {
            "human_readable": summary,
            "score": score,
            "issue_counts": heuristics["issue_counts"],
        },
        "issues": issues,
        "recommendations": recommendations,
        "coverage_notes": coverage_notes,
        "provider_used": provider_used,
        "model_used": model_used,
        "raw_snapshot": snapshot,
    }

