from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from .base import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    provider_name = "openai"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(base_url=base_url or "https://api.openai.com/v1", timeout=timeout)
        hostname = (urlparse(self.base_url or "").hostname or "").lower()
        if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
            self.provider_name = "openai-compatible local"
        else:
            self.provider_name = "openai"

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        api_key: Optional[str],
        temperature: float = 0.2,
        max_completion_tokens: Optional[int] = None,
    ) -> str:
        key = self._resolve_api_key(api_key, ["OPENAI_API_KEY"])
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        return self._chat_completions(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            api_key=key,
            temperature=temperature,
            base_url=self.base_url,
            headers=headers,
            max_completion_tokens=max_completion_tokens,
        )
