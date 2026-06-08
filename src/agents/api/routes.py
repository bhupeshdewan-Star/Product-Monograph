from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ..a11y.checker import check_accessibility
from ..a11y.schemas import A11yCheckRequest
from ..auditor.builder import build_audit_schema
from ..auditor.runner import run_audit
from ..auditor.schemas import (
    AuditBuildAndRunRequest,
    AuditBuildRequest,
    AuditRunRequest,
)
from ..providers.base import ProviderConfig
from ..runtime.cache import build_cache_key
from .state import get_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


def _state():
    return get_state()


def _provider_config(payload):
    if not payload:
        return None
    return ProviderConfig(
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
        temperature=payload.temperature,
        base_url=payload.base_url,
    )


def _request_id(request: Request, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def _client_id(request: Request, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    header_client = request.headers.get("X-Client-Id")
    if header_client:
        return header_client
    return request.client.host if request.client else "default"


def _apply_rate_limit(request: Request, client_id: str) -> dict[str, Any]:
    allowed, status = _state().rate_limiter.allow(client_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "success": False,
                "error": "Rate limit exceeded",
                "rate_limit": status,
                "request_id": _request_id(request),
            },
        )
    return status


def _cache_lookup(prefix: str, payload: dict[str, Any]) -> Any:
    return _state().cache.get(build_cache_key(prefix, payload))


def _cache_store(prefix: str, payload: dict[str, Any], value: Any) -> None:
    _state().cache.set(build_cache_key(prefix, payload), value)


@router.post("/a11y/check")
def a11y_check(payload: A11yCheckRequest, request: Request):
    try:
        _apply_rate_limit(request, _client_id(request))
        provider_config = _provider_config(payload.ai_provider)
        cache_payload = {
            "url": payload.url,
            "provider": provider_config.model_dump(mode="json") if provider_config else None,
        }
        cached = _cache_lookup("a11y_check", cache_payload)
        if cached is not None:
            _state().history.record(
                {
                    "event_type": "a11y_check",
                    "target": payload.url,
                    "audit_type": "accessibility",
                    "score": cached.get("score"),
                    "issue_count": len(cached.get("issues", [])),
                    "provider": cached.get("provider_used"),
                    "model": cached.get("model_used"),
                    "cached": True,
                }
            )
            return cached
        result = check_accessibility(payload.url, provider_config)
        _cache_store("a11y_check", cache_payload, result)
        _state().history.record(
            {
                "event_type": "a11y_check",
                "target": payload.url,
                "audit_type": "accessibility",
                "score": result.get("score"),
                "issue_count": len(result.get("issues", [])),
                "provider": result.get("provider_used"),
                "model": result.get("model_used"),
            }
        )
        return result
    except Exception as exc:
        logger.exception("A11y check failed")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/auditor/build")
def auditor_build(payload: AuditBuildRequest, request: Request):
    try:
        _apply_rate_limit(request, _client_id(request))
        provider_config = _provider_config(payload.ai_provider)
        cache_payload = {
            "checklist_url": payload.checklist_url,
            "provider": provider_config.model_dump(mode="json") if provider_config else None,
        }
        cached = _cache_lookup("auditor_build", cache_payload)
        if cached is not None:
            _state().history.record(
                {
                    "event_type": "audit_build",
                    "target": payload.checklist_url,
                    "audit_type": cached.get("audit_type"),
                    "schema_id": cached.get("schema_id"),
                    "issue_count": len(cached.get("schema", {}).get("criteria", [])),
                    "provider": cached.get("schema", {}).get("metadata", {}).get("llm_provider"),
                    "cached": True,
                }
            )
            return cached
        result = build_audit_schema(payload.checklist_url, provider_config)
        _cache_store("auditor_build", cache_payload, result)
        schema = result.get("schema")
        if schema:
            _state().registry.register_schema(schema, result.get("generated_schema_path"))
        _state().history.record(
            {
                "event_type": "audit_build",
                "target": payload.checklist_url,
                "audit_type": result.get("audit_type"),
                "schema_id": result.get("schema_id"),
                "issue_count": len(result.get("schema", {}).get("criteria", [])),
                "provider": result.get("schema", {}).get("metadata", {}).get("llm_provider"),
            }
        )
        return result
    except Exception as exc:
        logger.exception("Audit schema build failed")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/auditor/run")
def auditor_run(payload: AuditRunRequest, request: Request):
    try:
        _apply_rate_limit(request, _client_id(request))
        provider_config = _provider_config(payload.ai_provider)
        cache_payload = {
            "target_url": payload.target_url,
            "audit_schema_id": payload.audit_schema_id,
            "provider": provider_config.model_dump(mode="json") if provider_config else None,
        }
        cached = _cache_lookup("auditor_run", cache_payload)
        if cached is not None:
            _state().history.record(
                {
                    "event_type": "audit_run",
                    "target": payload.target_url,
                    "audit_type": cached.get("audit_type"),
                    "schema_id": cached.get("schema_id"),
                    "score": cached.get("score"),
                    "issue_count": len(cached.get("issues", [])),
                    "provider": cached.get("provider_used"),
                    "model": cached.get("model_used"),
                    "cached": True,
                }
            )
            return cached
        result = run_audit(
            payload.target_url,
            payload.audit_schema_id,
            provider_config,
        )
        _cache_store("auditor_run", cache_payload, result)
        _state().history.record(
            {
                "event_type": "audit_run",
                "target": payload.target_url,
                "audit_type": result.get("audit_type"),
                "schema_id": result.get("schema_id"),
                "score": result.get("score"),
                "issue_count": len(result.get("issues", [])),
                "provider": result.get("provider_used"),
                "model": result.get("model_used"),
            }
        )
        return result
    except Exception as exc:
        logger.exception("Audit run failed")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/auditor/build-and-run")
def auditor_build_and_run(payload: AuditBuildAndRunRequest, request: Request):
    try:
        _apply_rate_limit(request, _client_id(request))
        provider_config = _provider_config(payload.ai_provider)
        built = build_audit_schema(
            payload.checklist_url,
            provider_config,
        )
        run_result = run_audit(
            payload.target_url,
            built["schema_id"],
            provider_config,
        )
        if built.get("schema"):
            _state().registry.register_schema(built["schema"], built.get("generated_schema_path"))
        _state().history.record(
            {
                "event_type": "audit_build_and_run",
                "target": payload.target_url,
                "audit_type": run_result.get("audit_type"),
                "schema_id": built.get("schema_id"),
                "score": run_result.get("score"),
                "issue_count": len(run_result.get("issues", [])),
                "provider": run_result.get("provider_used"),
                "model": run_result.get("model_used"),
            }
        )
        return {
            "success": True,
            "built_schema": built,
            "run_result": run_result,
        }
    except Exception as exc:
        logger.exception("Build-and-run failed")
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/cache/stats")
def cache_stats():
    return _state().cache.stats()


@router.post("/cache/clear")
def cache_clear():
    _state().cache.clear()
    return {"success": True, "status": "cache_cleared"}


@router.get("/ratelimit/status")
def rate_limit_status(request: Request):
    return _state().rate_limiter.status(_client_id(request))


@router.get("/auditor/registry")
def auditor_registry():
    entries = _state().registry.list_entries()
    return {
        "success": True,
        "total_count": len(entries),
        "agents": entries,
    }


@router.get("/auditor/history")
def auditor_history(limit: int = 100):
    events = _state().history.list_entries(limit=limit)
    return {
        "success": True,
        "total_count": len(events),
        "events": events,
    }
