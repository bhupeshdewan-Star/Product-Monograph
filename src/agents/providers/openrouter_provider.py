from __future__ import annotations

from typing import Optional

from .base import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    provider_name = "openrouter"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(base_url=base_url or "https://openrouter.ai/api/v1", timeout=timeout)

    def generate(
        self,
        prompt,
        system_prompt,
        model,
        api_key,
        temperature: float = 0.2,
        max_completion_tokens: Optional[int] = None,
    ) -> str:
        key = self._resolve_api_key(api_key, ["OPENROUTER_API_KEY"])
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "MedicoExpress Global Agents",
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
