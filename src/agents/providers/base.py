from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
from urllib.parse import urlparse
from typing import Optional

import requests


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.2
    base_url: Optional[str] = None
    max_completion_tokens: Optional[int] = None
    timeout: float = 60.0
    strict: bool = False


class LLMProvider(ABC):
    provider_name = "base"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.last_request_diagnostics: dict = {}

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        words = max(1, len((text or "").split()))
        return int(words * 1.25)

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        api_key: Optional[str],
        temperature: float = 0.2,
        max_completion_tokens: Optional[int] = None,
    ) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    def _is_loopback_url(self, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

    def _request_timeout(self, url: str) -> float:
        if self._is_loopback_url(url):
            return max(self.timeout, 300.0)
        return self.timeout

    def _post_json(self, url: str, headers: dict, payload: dict, timeout: float | None = None) -> dict:
        timeout_value = timeout or self._request_timeout(url)
        self.last_request_diagnostics = {
            "provider_name": self.provider_name,
            "request_url": url,
            "timeout_seconds": timeout_value,
            "request_sent": False,
            "response_received": False,
            "error_type": None,
            "error_message": None,
            "payload": payload,
            "payload_characters": len(json.dumps(payload, ensure_ascii=False)),
        }
        try:
            self.last_request_diagnostics["request_sent"] = True
            response = requests.post(url, headers=headers, json=payload, timeout=timeout_value)
        except requests.exceptions.Timeout as exc:
            self.last_request_diagnostics["error_type"] = "timeout"
            self.last_request_diagnostics["error_message"] = str(exc)
            if self._is_loopback_url(url):
                raise ProviderError(
                    f"Local model timed out. Try reducing Max research results, using a shorter molecule input, "
                    f"or increasing the local timeout. Provider: {self.provider_name}."
                ) from exc
            raise ProviderError(
                f"{self.provider_name} request timed out. Try again or increase the timeout."
            ) from exc
        except requests.exceptions.RequestException as exc:
            self.last_request_diagnostics["error_type"] = "request_exception"
            self.last_request_diagnostics["error_message"] = str(exc)
            raise ProviderError(f"{self.provider_name} request failed: {exc}") from exc
        self.last_request_diagnostics["response_received"] = True
        self.last_request_diagnostics["status_code"] = response.status_code
        if response.status_code >= 400:
            self.last_request_diagnostics["error_type"] = "http_error"
            self.last_request_diagnostics["error_message"] = response.text
            raise ProviderError(
                f"{self.provider_name} request failed with {response.status_code}: {response.text}"
            )
        return response.json()

    def _resolve_api_key(self, api_key: Optional[str], env_names: list[str]) -> str:
        key = api_key or next((os.getenv(name) for name in env_names if os.getenv(name)), None)
        if not key:
            if self.base_url:
                hostname = (urlparse(self.base_url).hostname or "").lower()
                if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
                    return "local"
            raise ProviderError(
                f"Missing API key for provider '{self.provider_name}'. "
                f"Pass it at runtime or set one of: {', '.join(env_names)}"
            )
        return key

    def _chat_completions(
        self,
        *,
        prompt: str,
        system_prompt: str,
        model: str,
        api_key: Optional[str],
        temperature: float,
        base_url: str,
        headers: dict,
        max_completion_tokens: Optional[int] = None,
    ) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        if max_completion_tokens:
            payload["max_tokens"] = max_completion_tokens
            payload["max_completion_tokens"] = max_completion_tokens
        request_url = f"{base_url.rstrip('/')}/chat/completions"
        data = self._post_json(request_url, headers, payload, timeout=self._request_timeout(request_url))
        self.last_request_diagnostics.update(
            {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_completion_tokens,
                "prompt_characters": len(system_prompt or "") + len(prompt or ""),
                "estimated_prompt_tokens": self._estimate_tokens(f"{system_prompt}\n{prompt}"),
            }
        )
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise ProviderError(f"Unexpected response format from {self.provider_name}: {data}") from exc
