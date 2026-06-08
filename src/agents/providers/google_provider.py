from __future__ import annotations

import os
from typing import Optional

import requests

from .base import LLMProvider, ProviderError


class GoogleProvider(LLMProvider):
    provider_name = "google"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(
            base_url=base_url or "https://generativelanguage.googleapis.com/v1beta",
            timeout=timeout,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        api_key: Optional[str],
        temperature: float = 0.2,
    ) -> str:
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ProviderError(
                "Missing API key for provider 'google'. Pass it at runtime or set GEMINI_API_KEY."
            )

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
            },
        }
        response = requests.post(
            f"{self.base_url.rstrip('/')}/models/{model}:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise ProviderError(f"google request failed with {response.status_code}: {response.text}")
        data = response.json()
        try:
            return "".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"])
        except Exception as exc:
            raise ProviderError(f"Unexpected response format from google: {data}") from exc

