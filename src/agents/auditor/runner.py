from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Optional

from ..providers.base import ProviderConfig, ProviderError
from ..providers.provider_factory import create_provider
from ..utils import count_by_severity, extract_json_object, merge_unique_issues, score_from_issues, truncate_text
from ..web.fetcher import fetch_url
from ..web.parser import parse_page_snapshot
from .schema_store import load_schema
from .schemas import AuditCriterion

logger = logging.getLogger(__name__)


FALLBACK_TARGET_HTML = """
<html>
  <head>
    <title>Fallback Audit Target</title>
  </head>
  <body>
    <main>
      <h1>Fallback Audit Target</h1>
      <p>The requested page could not be fetched, so the audit ran against a local fallback target.</p>
    </main>
  </body>
</html>
"""


def _keyword_match(snapshot: dict, criterion: AuditCriterion) -> tuple[bool, list[str]]:
    haystack = " ".join(
        [
            snapshot.get("title", ""),
            snapshot.get("meta_description", ""),
            snapshot.get("text_excerpt", ""),
            " ".join(item.get("text", "") for item in snapshot.get("headings", [])),
        ]
    ).lower()
    keywords = [kw.lower() for kw in criterion.keywords]
    matched = [kw for kw in keywords if kw and kw in haystack]
    return bool(matched), matched


def _heuristic_issue_from_criterion(criterion: AuditCriterion, reason: str, evidence: list[str]) -> dict:
    return {
        "id": criterion.id,
        "title": criterion.title,
        "severity": criterion.severity,
        "category": criterion.category,
        "description": criterion.description,
        "impact": reason,
        "evidence": evidence,
        "recommended_fixes": criterion.remediation_hints
        or [f"Address the checklist item: {criterion.title}"],
        "target": criterion.category,
        "criterion_id": criterion.id,
    }


def _evaluate_schema_heuristically(snapshot: dict, schema: dict) -> dict:
    issues = []
    recommendations = []

    for raw in schema.get("criteria", []):
        criterion = AuditCriterion.model_validate(raw)
        check_type = criterion.check_type
        matched = True
        evidence = []
        reason = "Checklist criterion passed based on heuristic analysis."

        if check_type in {"html", "meta", "structure"}:
            matched, matched_keywords = _keyword_match(snapshot, criterion)
            evidence = matched_keywords or [criterion.title]
            if not matched:
                reason = "No supporting evidence was found in the page snapshot."
        elif check_type == "keyword":
            matched, matched_keywords = _keyword_match(snapshot, criterion)
            evidence = matched_keywords or [criterion.title]
            if not matched:
                reason = "No keyword match was found in the extracted page content."
        else:
            matched = True
            evidence = [criterion.title]

        if not matched:
            issues.append(_heuristic_issue_from_criterion(criterion, reason, evidence))
            recommendations.extend(criterion.remediation_hints or [criterion.title])

    return {
        "issues": issues,
        "recommendations": list(dict.fromkeys(recommendations)),
        "score": score_from_issues(issues),
        "issue_counts": count_by_severity(issues),
    }


def _llm_refine_audit(
    *,
    snapshot: dict,
    schema: dict,
    heuristics: dict,
    provider_config: ProviderConfig,
) -> dict:
    provider = create_provider(provider_config)
    system_prompt = (
        "You are an audit engine that returns JSON only. "
        "Use the supplied audit schema and page snapshot to evaluate the target URL. "
        "Do not invent unsupported findings."
    )
    prompt = {
        "task": "Run the supplied audit schema against the target page and return JSON.",
        "audit_schema": schema,
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
                    "criterion_id": "string",
                }
            ],
            "recommendations": ["string"],
            "coverage_notes": ["string"],
        },
        "constraints": [
            "JSON only",
            "Return evidence-based issues only",
            "Use the schema criteria as the source of truth",
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
        raise ValueError("Audit model output must be a JSON object")
    return parsed


def run_audit(
    target_url: str,
    audit_schema_id: str,
    ai_provider: Optional[ProviderConfig] = None,
    *,
    fetcher=fetch_url,
) -> dict:
    schema = load_schema(audit_schema_id)
    target_fetch_warning = None
    try:
        page = fetcher(target_url)
    except Exception as exc:
        target_fetch_warning = str(exc)
        logger.warning("Audit target fetch failed, using local fallback: %s", exc)
        page = SimpleNamespace(
            html=FALLBACK_TARGET_HTML,
            final_url="inline://audit-target",
        )
    snapshot = parse_page_snapshot(page.html, page.final_url)
    heuristics = _evaluate_schema_heuristically(snapshot, schema.model_dump(mode="json"))

    issues = heuristics["issues"]
    recommendations = heuristics["recommendations"]
    score = heuristics["score"]
    coverage_notes = [
        "Generic schema evaluation relies on keywords and page snapshot structure when no LLM is available.",
    ]
    if target_fetch_warning:
        coverage_notes.append(f"Target fetch failed and the audit ran against fallback HTML: {target_fetch_warning}")
    provider_used = None
    model_used = None

    if ai_provider and ai_provider.provider:
        try:
            llm_result = _llm_refine_audit(
                snapshot=snapshot,
                schema=schema.model_dump(mode="json"),
                heuristics=heuristics,
                provider_config=ai_provider,
            )
            issues = merge_unique_issues(issues, llm_result.get("issues", []))
            recommendations = list(
                dict.fromkeys(recommendations + list(llm_result.get("recommendations", [])))
            )
            score = int(llm_result.get("score", score_from_issues(issues)))
            coverage_notes.extend(list(llm_result.get("coverage_notes", [])))
            provider_used = ai_provider.provider
            model_used = ai_provider.model
            logger.info("Audit run refined with %s", ai_provider.provider)
        except (ProviderError, ValueError, TypeError) as exc:
            coverage_notes.append(f"LLM refinement skipped: {exc}")
            logger.warning("Audit run refinement failed: %s", exc)

    return {
        "success": True,
        "audit_type": schema.audit_type,
        "schema_id": schema.schema_id,
        "source_url": schema.source_url,
        "target_url": target_url,
        "score": score,
        "summary": {
            "human_readable": (
                f"Audit found {len(issues)} issue(s) across "
                f"{schema.criteria and len(schema.criteria) or 0} criteria."
            ),
            "score": score,
            "issue_counts": count_by_severity(issues),
        },
        "issues": issues,
        "recommendations": recommendations,
        "coverage_notes": coverage_notes,
        "provider_used": provider_used,
        "model_used": model_used,
        "schema": schema.model_dump(mode="json"),
        "target_fetch_warning": target_fetch_warning,
    }

