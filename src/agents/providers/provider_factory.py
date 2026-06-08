from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import LLMProvider, ProviderConfig, ProviderError
from .deepseek_provider import DeepSeekProvider
from .google_provider import GoogleProvider
from .groq_provider import GroqProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider


def create_provider(config: ProviderConfig) -> LLMProvider:
    provider = (config.provider or "").strip().lower()
    if provider == "openai":
        return OpenAIProvider(base_url=config.base_url, timeout=config.timeout)
    if provider == "anthropic":
        return AnthropicProvider(base_url=config.base_url, timeout=config.timeout)
    if provider in {"google", "gemini"}:
        return GoogleProvider(base_url=config.base_url, timeout=config.timeout)
    if provider == "deepseek":
        return DeepSeekProvider(base_url=config.base_url, timeout=config.timeout)
    if provider == "groq":
        return GroqProvider(base_url=config.base_url, timeout=config.timeout)
    if provider in {"openrouter", "openrouter-compatible", "openrouter_compatible"}:
        return OpenRouterProvider(base_url=config.base_url, timeout=config.timeout)
    raise ProviderError(
        f"Unsupported provider '{config.provider}'. "
        "Supported providers: openai, anthropic, google/gemini, deepseek, groq, openrouter."
    )

