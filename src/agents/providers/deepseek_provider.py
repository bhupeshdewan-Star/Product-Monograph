from __future__ import annotations

from typing import Optional

from .base import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    provider_name = "deepseek"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(base_url=base_url or "https://api.deepseek.com", timeout=timeout)

    def generate(
        self,
        prompt,
        system_prompt,
        model,
        api_key,
        temperature: float = 0.2,
        max_completion_tokens: Optional[int] = None,
    ) -> str:
        key = self._resolve_api_key(api_key, ["DEEPSEEK_API_KEY"])
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
