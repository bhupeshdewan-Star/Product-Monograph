from __future__ import annotations

import os
from typing import Optional

import requests

from .base import LLMProvider, ProviderError


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(base_url=base_url or "https://api.anthropic.com/v1", timeout=timeout)

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        api_key: Optional[str],
        temperature: float = 0.2,
        max_completion_tokens: Optional[int] = None,
    ) -> str:
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError(
                "Missing API key for provider 'anthropic'. Pass it at runtime or set ANTHROPIC_API_KEY."
            )

        payload = {
            "model": model,
            "max_tokens": max_completion_tokens or 2048,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        response = requests.post(
            f"{self.base_url.rstrip('/')}/messages",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise ProviderError(
                f"anthropic request failed with {response.status_code}: {response.text}"
            )
        data = response.json()
        try:
            return "".join(part.get("text", "") for part in data["content"])
        except Exception as exc:
            raise ProviderError(f"Unexpected response format from anthropic: {data}") from exc
