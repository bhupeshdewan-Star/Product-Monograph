from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class ModelDiscoveryResult:
    provider: str
    source: str
    models: list[str]
    discovered_at: float
    cache_key: str
    warning: Optional[str] = None


class ModelDiscoveryService:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, ModelDiscoveryResult] = {}

    def discover_models(
        self,
        *,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> ModelDiscoveryResult:
        provider = (provider or "").strip().lower()
        cache_key = self._cache_key(provider, base_url)
        now = time.time()
        cached = self._cache.get(cache_key)
        if cached and not force_refresh and now - cached.discovered_at < self.ttl_seconds:
            return ModelDiscoveryResult(
                provider=cached.provider,
                source="cached",
                models=cached.models,
                discovered_at=cached.discovered_at,
                cache_key=cache_key,
                warning=cached.warning,
            )

        discovery = self._discover(provider=provider, api_key=api_key, base_url=base_url)
        discovery.cache_key = cache_key
        self._cache[cache_key] = discovery
        return discovery

    def clear(self) -> None:
        self._cache.clear()

    def _discover(
        self,
        *,
        provider: str,
        api_key: Optional[str],
        base_url: Optional[str],
    ) -> ModelDiscoveryResult:
        discovered_at = time.time()
        if provider == "openai":
            return self._discover_openai_like(
                provider=provider,
                api_key=api_key,
                base_url=base_url or "https://api.openai.com/v1",
                auth_header="Authorization",
                auth_value_prefix="Bearer ",
                endpoints=("/models",),
            )
        if provider == "anthropic":
            return self._discover_anthropic(api_key=api_key, base_url=base_url or "https://api.anthropic.com/v1")
        if provider in {"google", "gemini"}:
            return self._discover_google(api_key=api_key, base_url=base_url or "https://generativelanguage.googleapis.com/v1beta")
        if provider == "deepseek":
            return self._discover_openai_like(
                provider=provider,
                api_key=api_key,
                base_url=base_url or "https://api.deepseek.com/v1",
                auth_header="Authorization",
                auth_value_prefix="Bearer ",
                endpoints=("/models",),
            )
        if provider == "groq":
            return self._discover_openai_like(
                provider=provider,
                api_key=api_key,
                base_url=base_url or "https://api.groq.com/openai/v1",
                auth_header="Authorization",
                auth_value_prefix="Bearer ",
                endpoints=("/models",),
            )
        if provider == "openrouter":
            return self._discover_openai_like(
                provider=provider,
                api_key=api_key,
                base_url=base_url or "https://openrouter.ai/api/v1",
                auth_header="Authorization",
                auth_value_prefix="Bearer ",
                endpoints=("/models",),
            )
        if provider == "openai-compatible local":
            return self._discover_local(base_url=base_url or "http://localhost:1234/v1")
        return ModelDiscoveryResult(
            provider=provider,
            source="manual",
            models=[],
            discovered_at=discovered_at,
            cache_key="",
            warning=f"Model discovery is not implemented for provider '{provider}'.",
        )

    def _discover_openai_like(
        self,
        *,
        provider: str,
        api_key: Optional[str],
        base_url: str,
        auth_header: str,
        auth_value_prefix: str,
        endpoints: tuple[str, ...],
    ) -> ModelDiscoveryResult:
        models: list[str] = []
        warning: Optional[str] = None
        for endpoint in endpoints:
            try:
                headers = {}
                if api_key:
                    headers[auth_header] = f"{auth_value_prefix}{api_key}"
                response = requests.get(
                    f"{base_url.rstrip('/')}{endpoint}",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code >= 400:
                    warning = f"Model discovery request failed with {response.status_code}."
                    continue
                data = response.json()
                models = sorted(self._extract_openai_like_models(data))
                if models:
                    return ModelDiscoveryResult(
                        provider=provider,
                        source="live",
                        models=models,
                        discovered_at=time.time(),
                        cache_key="",
                        warning=None,
                    )
            except Exception as exc:
                warning = str(exc)
                continue
        return ModelDiscoveryResult(
            provider=provider,
            source="manual",
            models=[],
            discovered_at=time.time(),
            cache_key="",
            warning=warning or "No models could be retrieved.",
        )

    def _discover_anthropic(
        self,
        *,
        api_key: Optional[str],
        base_url: str,
    ) -> ModelDiscoveryResult:
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        try:
            response = requests.get(f"{base_url.rstrip('/')}/models", headers=headers, timeout=10)
            if response.status_code < 400:
                models = []
                data = response.json()
                for item in data.get("data", []) or data.get("models", []):
                    model_id = item.get("id") or item.get("name")
                    if model_id:
                        models.append(str(model_id).replace("models/", ""))
                if models:
                    return ModelDiscoveryResult(
                        provider="anthropic",
                        source="live",
                        models=sorted(dict.fromkeys(models)),
                        discovered_at=time.time(),
                        cache_key="",
                        warning=None,
                    )
            warning = f"Anthropic model discovery failed with {response.status_code}: {response.text}"
        except Exception as exc:
            warning = str(exc)
        return ModelDiscoveryResult(
            provider="anthropic",
            source="manual",
            models=[],
            discovered_at=time.time(),
            cache_key="",
            warning=warning,
        )

    def _discover_google(
        self,
        *,
        api_key: Optional[str],
        base_url: str,
    ) -> ModelDiscoveryResult:
        if not api_key:
            return ModelDiscoveryResult(
                provider="google",
                source="manual",
                models=[],
                discovered_at=time.time(),
                cache_key="",
                warning="Google model discovery requires a key. Manual model entry remains available.",
            )
        try:
            response = requests.get(
                f"{base_url.rstrip('/')}/models",
                params={"key": api_key},
                timeout=10,
            )
            if response.status_code < 400:
                data = response.json()
                models: list[str] = []
                for item in data.get("models", []):
                    model_id = item.get("name") or item.get("baseModelId") or item.get("id")
                    if model_id:
                        model_id = str(model_id).replace("models/", "")
                        models.append(model_id)
                if models:
                    return ModelDiscoveryResult(
                        provider="google",
                        source="live",
                        models=sorted(dict.fromkeys(models)),
                        discovered_at=time.time(),
                        cache_key="",
                        warning=None,
                    )
            warning = f"Google model discovery failed with {response.status_code}: {response.text}"
        except Exception as exc:
            warning = str(exc)
        return ModelDiscoveryResult(
            provider="google",
            source="manual",
            models=[],
            discovered_at=time.time(),
            cache_key="",
            warning=warning,
        )

    def _discover_local(self, *, base_url: str) -> ModelDiscoveryResult:
        warnings: list[str] = []
        for suffix in ("/v1/models", "/models"):
            try:
                response = requests.get(f"{base_url.rstrip('/')}{suffix}", timeout=5)
                if response.status_code < 400:
                    models = self._prioritize_local_models(
                        self._extract_openai_like_models(response.json())
                    )
                    if models:
                        return ModelDiscoveryResult(
                            provider="openai-compatible local",
                            source="live",
                            models=models,
                            discovered_at=time.time(),
                            cache_key="",
                            warning=None,
                        )
                warnings.append(f"{suffix}: {response.status_code}")
            except Exception as exc:
                warnings.append(f"{suffix}: {exc}")
        return ModelDiscoveryResult(
            provider="openai-compatible local",
            source="manual",
            models=[],
            discovered_at=time.time(),
            cache_key="",
            warning="; ".join(warnings) if warnings else "No local models could be retrieved.",
        )

    @staticmethod
    def _extract_openai_like_models(data: Any) -> list[str]:
        models: list[str] = []
        for item in data.get("data", []) if isinstance(data, dict) else []:
            model_id = item.get("id") or item.get("name")
            if model_id:
                models.append(str(model_id))
        for item in data.get("models", []) if isinstance(data, dict) else []:
            model_id = item.get("id") or item.get("name")
            if model_id:
                models.append(str(model_id).replace("models/", ""))
        return list(dict.fromkeys(models))

    @staticmethod
    def _prioritize_local_models(models: list[str]) -> list[str]:
        def sort_key(model_id: str) -> tuple[int, str]:
            lowered = model_id.lower()
            if "embed" in lowered or "embedding" in lowered:
                priority = 3
            elif "phi" in lowered or "mini" in lowered:
                priority = 0
            elif "instruct" in lowered or "chat" in lowered:
                priority = 1
            else:
                priority = 2
            return priority, lowered

        return sorted(models, key=sort_key)

    @staticmethod
    def _cache_key(provider: str, base_url: Optional[str]) -> str:
        raw = f"{provider}|{(base_url or '').strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


model_discovery_service = ModelDiscoveryService()
