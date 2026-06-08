from __future__ import annotations

import logging
from typing import Optional

from ..providers.base import ProviderConfig, ProviderError
from ..providers.provider_factory import create_provider
from ..utils import extract_json_object, slugify, truncate_text
from ..web.fetcher import fetch_url
from ..web.parser import parse_checklist_document, parse_page_snapshot
from .schema_store import save_schema
from .schemas import AuditCriterion, AuditSchema

logger = logging.getLogger(__name__)


def _infer_audit_type(title: str, source_text: str) -> str:
    text = f"{title} {source_text}".lower()
    if "accessibility" in text or "a11y" in text:
        return "accessibility"
    if "seo" in text or "search engine" in text:
        return "seo"
    if "performance" in text or "speed" in text:
        return "performance"
    if "security" in text or "vulnerability" in text:
        return "security"
    if "compliance" in text:
        return "compliance"
    if "ux" in text or "user experience" in text:
        return "ux"
    if "content" in text:
        return "content"
    return "landing_page_audit"


def _infer_check_type(text: str) -> str:
    lowered = text.lower()
    keywords = [
        "alt",
        "heading",
        "label",
        "contrast",
        "keyboard",
        "aria",
        "viewport",
        "image",
        "link",
        "button",
        "form",
        "semantic",
        "title",
        "meta description",
        "canonical",
        "robots",
        "schema",
        "performance",
        "script",
        "load",
        "privacy",
        "cookie",
    ]
    if any(token in lowered for token in ["alt", "heading", "label", "contrast", "keyboard", "aria", "viewport", "form", "button", "link", "semantic", "image"]):
        return "html"
    if any(token in lowered for token in ["title", "meta description", "canonical", "robots", "schema"]):
        return "meta"
    if any(token in lowered for token in ["performance", "load", "script"]):
        return "structure"
    if any(token in lowered for token in ["privacy", "cookie", "consent"]):
        return "structure"
    return "llm"


def _criterion_keywords(text: str) -> list[str]:
    tokens = [token.strip(".,:;()[]") for token in text.lower().split()]
    important = [token for token in tokens if len(token) > 3]
    return important[:8]


def _build_criteria_from_document(doc: dict) -> list[AuditCriterion]:
    criteria = []
    items = doc.get("items", [])
    for index, item in enumerate(items, start=1):
        text = item.get("text", "").strip()
        if not text:
            continue
        section = item.get("section") or "General"
        severity = "medium"
        if any(word in text.lower() for word in ["must", "required", "critical", "essential"]):
            severity = "high"
        if any(word in text.lower() for word in ["optional", "nice to have"]):
            severity = "low"
        criteria.append(
            AuditCriterion(
                id=f"c{index:02d}",
                title=text[:120],
                description=f"Checklist item derived from section '{section}'.",
                severity=severity,
                weight=10 if severity == "high" else 6 if severity == "medium" else 3,
                category=slugify(section, "general"),
                check_type=_infer_check_type(text),
                keywords=_criterion_keywords(text),
                evidence_hints=[section] if section else [],
                remediation_hints=[f"Address the checklist item: {text}"],
            )
        )
    return criteria


def _llm_refine_schema(doc: dict, provider_config: ProviderConfig) -> dict:
    provider = create_provider(provider_config)
    system_prompt = (
        "You convert public audit checklists into reusable audit schemas. "
        "Return JSON only. Preserve the checklist intent and make the schema reusable across websites."
    )
    prompt = {
        "task": "Extract audit criteria and return a reusable schema JSON.",
        "checklist_document": doc,
        "output_schema": {
            "schema_id": "string",
            "audit_type": "string",
            "name": "string",
            "criteria": [
                {
                    "id": "string",
                    "title": "string",
                    "description": "string",
                    "severity": "critical|high|medium|low",
                    "weight": "integer",
                    "category": "string",
                    "check_type": "html|meta|structure|keyword|llm",
                    "keywords": ["string"],
                    "evidence_hints": ["string"],
                    "remediation_hints": ["string"],
                }
            ],
        },
        "constraints": [
            "JSON only",
            "Focus on reusable criteria, not commentary",
            "Do not invent criteria unrelated to the checklist",
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
        raise ValueError("Audit schema model output must be a JSON object")
    return parsed


def build_audit_schema(
    checklist_url: str,
    ai_provider: Optional[ProviderConfig] = None,
    *,
    fetcher=fetch_url,
) -> dict:
    page = fetcher(checklist_url)
    doc = parse_checklist_document(page.html, page.final_url)
    title = doc.get("title") or doc.get("h1") or "Checklist"
    audit_type = _infer_audit_type(title, doc.get("source_text", ""))
    criteria = _build_criteria_from_document(doc)
    schema_id = slugify(f"{audit_type}_v1", "audit_schema_v1")
    schema = AuditSchema(
        schema_id=schema_id,
        audit_type=audit_type,
        name=title or audit_type.replace("_", " ").title(),
        source_url=checklist_url,
        source_title=title,
        criteria=criteria,
        scoring={
            "max_score": 100,
            "penalty_by_severity": {"critical": 25, "high": 15, "medium": 8, "low": 3},
        },
        metadata={
            "source_final_url": page.final_url,
            "criteria_count": len(criteria),
        },
    )

    if ai_provider and ai_provider.provider:
        try:
            refined = _llm_refine_schema(doc, ai_provider)
            if isinstance(refined.get("audit_type"), str):
                schema.audit_type = refined["audit_type"]
            if isinstance(refined.get("name"), str):
                schema.name = refined["name"]
            if isinstance(refined.get("schema_id"), str):
                schema.schema_id = slugify(refined["schema_id"], schema.schema_id)
            if isinstance(refined.get("criteria"), list) and refined["criteria"]:
                schema.criteria = [AuditCriterion.model_validate(item) for item in refined["criteria"]]
            logger.info("Checklist schema refined with %s", ai_provider.provider)
        except (ProviderError, ValueError, TypeError) as exc:
            schema.metadata["llm_refinement_error"] = str(exc)
            logger.warning("Schema refinement skipped: %s", exc)

    path = save_schema(schema)
    schema.metadata["saved_path"] = str(path)
    return {
        "success": True,
        "audit_type": schema.audit_type,
        "schema_id": schema.schema_id,
        "source_url": checklist_url,
        "source_title": schema.source_title,
        "schema": schema.model_dump(mode="json"),
        "generated_schema_path": str(path),
    }

