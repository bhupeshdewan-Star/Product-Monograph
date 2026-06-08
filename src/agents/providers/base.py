from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
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
    timeout: float = 60.0


class LLMProvider(ABC):
    provider_name = "base"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        self.base_url = base_url
        self.timeout = timeout

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        api_key: Optional[str],
        temperature: float = 0.2,
    ) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    def _post_json(self, url: str, headers: dict, payload: dict) -> dict:
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise ProviderError(
                f"{self.provider_name} request failed with {response.status_code}: {response.text}"
            )
        return response.json()

    def _resolve_api_key(self, api_key: Optional[str], env_names: list[str]) -> str:
        key = api_key or next((os.getenv(name) for name in env_names if os.getenv(name)), None)
        if not key:
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
    ) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        data = self._post_json(f"{base_url.rstrip('/')}/chat/completions", headers, payload)
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise ProviderError(f"Unexpected response format from {self.provider_name}: {data}") from exc

