from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field

from src.agents.providers.base import ProviderConfig


GENERATION_MODES = ("ai", "demo", "local")
AI_PROVIDER_CHOICES = ("openai", "anthropic", "google", "deepseek", "groq", "openrouter")

PROVIDER_ENV_KEYS = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "google": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "groq": ("GROQ_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "openai-compatible local": (),
}

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "anthropic": "Claude",
    "google": "Gemini",
    "deepseek": "DeepSeek",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "openai-compatible local": "Local Model",
}

PROVIDER_VALIDATION_ORDER = ("openai", "anthropic", "google", "deepseek", "groq", "openrouter")


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _runtime_key(provider: str, api_key: Optional[str]) -> Optional[str]:
    if api_key:
        return api_key
    for env_name in PROVIDER_ENV_KEYS.get(provider, ()):
        value = os.getenv(env_name)
        if value:
            return value
    return None


def _api_key_source(provider: str, api_key: Optional[str]) -> str:
    if api_key:
        return "manual"
    for env_name in PROVIDER_ENV_KEYS.get(provider, ()):
        if os.getenv(env_name):
            return "environment"
    return "none"


def _looks_like_local_base_url(base_url: Optional[str]) -> bool:
    if not base_url:
        return False
    normalized = base_url.lower()
    return any(token in normalized for token in ("localhost", "127.0.0.1", "0.0.0.0", "::1"))


class GenerationConfig(BaseModel):
    mode: str = "ai"
    provider: Optional[str] = None
    provider_label: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    api_key_source: str = "none"
    base_url: Optional[str] = None
    max_completion_tokens: Optional[int] = None
    max_research_articles: int = 30
    temperature: float = 0.3
    local_compact_prompt_mode: bool = False
    local_section_generation_mode: bool = False
    local_compact_evidence_chars: int = 3000
    local_safe_prompt_tokens: int = 2400
    demo_mode: bool = False
    blocked: bool = False
    blocked_reason: Optional[str] = None
    selection_source: str = "demo"
    output_label: str = ""
    real_llm_call: bool = False
    notes: list[str] = Field(default_factory=list)

    def to_provider_config(self) -> Optional[ProviderConfig]:
        if self.demo_mode or self.blocked or not self.provider:
            return None
        provider = "openai" if self.provider == "openai-compatible local" else self.provider
        if not self.model:
            return None
        return ProviderConfig(
            provider=provider,
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            base_url=self.base_url,
            max_completion_tokens=self.max_completion_tokens,
            strict=self.mode == "ai",
        )


def resolve_generation_config(
    *,
    mode: str,
    provider_choice: str = "openai",
    model: str = "",
    api_key: str = "",
    base_url: str = "",
    max_research_articles: int = 30,
    temperature: float = 0.3,
) -> GenerationConfig:
    normalized_mode = _normalize(mode) or "ai"
    notes: list[str] = []

    if normalized_mode not in GENERATION_MODES:
        notes.append(f"Invalid mode '{mode}' was selected; using Demo Mode instead.")
        normalized_mode = "demo"

    if normalized_mode == "demo":
        return GenerationConfig(
            mode="demo",
            provider=None,
            provider_label=None,
            model=None,
            api_key=None,
            api_key_source="none",
            base_url=None,
            max_research_articles=max_research_articles,
            temperature=temperature,
            demo_mode=True,
            blocked=False,
            blocked_reason=None,
            selection_source="demo",
            output_label="Demo draft generated from fallback/sample data.",
            real_llm_call=False,
            notes=notes,
        )

    if normalized_mode == "local":
        local_base_url = base_url.strip() or os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1")
        local_model = model.strip()
        if not _looks_like_local_base_url(local_base_url):
            notes.append(
                "Local Model Mode is intended for localhost or loopback OpenAI-compatible endpoints."
            )
        if not local_model:
            blocked_reason = "Local Model Mode requires an explicit model name. Discover or enter one manually."
            notes.append(blocked_reason)
            return GenerationConfig(
                mode="local",
                provider="openai-compatible local",
                provider_label=PROVIDER_LABELS["openai-compatible local"],
                model=None,
                api_key=None,
                api_key_source="none",
                base_url=local_base_url,
                max_completion_tokens=256,
                max_research_articles=max_research_articles,
                temperature=temperature,
                local_compact_prompt_mode=True,
                local_section_generation_mode=True,
                local_compact_evidence_chars=3000,
                local_safe_prompt_tokens=2400,
                demo_mode=False,
                blocked=True,
                blocked_reason=blocked_reason,
                selection_source="blocked",
                output_label="Local model draft generated using retrieved evidence package.",
                real_llm_call=False,
                notes=notes,
            )
        return GenerationConfig(
            mode="local",
            provider="openai-compatible local",
            provider_label=PROVIDER_LABELS["openai-compatible local"],
            model=local_model,
            api_key=None,
            api_key_source="none",
            base_url=local_base_url,
            max_completion_tokens=256,
            max_research_articles=max_research_articles,
            temperature=temperature,
            local_compact_prompt_mode=True,
            local_section_generation_mode=True,
            local_compact_evidence_chars=3000,
            local_safe_prompt_tokens=2400,
            demo_mode=False,
            blocked=False,
            blocked_reason=None,
            selection_source="explicit",
            output_label="Local model draft generated using retrieved evidence package.",
            real_llm_call=True,
            notes=notes,
        )

    provider = _normalize(provider_choice) or "openai"
    if provider not in AI_PROVIDER_CHOICES:
        notes.append(f"Invalid provider '{provider_choice}' was selected in AI Mode.")
        return GenerationConfig(
            mode="ai",
            provider=provider if provider else None,
            provider_label=PROVIDER_LABELS.get(provider, provider_choice or None),
            model=model or None,
            api_key=None,
            api_key_source="none",
            base_url=None,
            max_completion_tokens=None,
            max_research_articles=max_research_articles,
            temperature=temperature,
            demo_mode=False,
            blocked=True,
            blocked_reason=f"Unsupported provider '{provider_choice}' selected in AI Mode.",
            selection_source="blocked",
            output_label="AI-generated draft for expert review.",
            real_llm_call=False,
            notes=notes,
        )

    selected_model = model.strip()
    runtime_key = _runtime_key(provider, api_key or None)
    source = _api_key_source(provider, api_key or None)

    if not runtime_key:
        blocked_reason = (
            f"AI Mode requires an API key for {PROVIDER_LABELS[provider]}. "
            "Enter one in the sidebar or set the matching environment variable."
        )
        notes.append(blocked_reason)
        return GenerationConfig(
            mode="ai",
            provider=provider,
            provider_label=PROVIDER_LABELS[provider],
            model=selected_model,
            api_key=None,
            api_key_source="none",
            base_url=None,
            max_completion_tokens=None,
            max_research_articles=max_research_articles,
            temperature=temperature,
            demo_mode=False,
            blocked=True,
            blocked_reason=blocked_reason,
            selection_source="blocked",
            output_label="AI-generated draft for expert review.",
            real_llm_call=False,
            notes=notes,
        )

    if not selected_model:
        blocked_reason = (
            f"AI Mode requires an explicit model name for {PROVIDER_LABELS[provider]}. "
            "Use a discovered model or enter one manually."
        )
        notes.append(blocked_reason)
        return GenerationConfig(
            mode="ai",
            provider=provider,
            provider_label=PROVIDER_LABELS[provider],
            model=None,
            api_key=runtime_key,
            api_key_source=source,
            base_url=None,
            max_completion_tokens=None,
            max_research_articles=max_research_articles,
            temperature=temperature,
            demo_mode=False,
            blocked=True,
            blocked_reason=blocked_reason,
            selection_source="blocked",
            output_label="AI-generated draft for expert review.",
            real_llm_call=False,
            notes=notes,
        )

    return GenerationConfig(
        mode="ai",
        provider=provider,
        provider_label=PROVIDER_LABELS[provider],
        model=selected_model,
        api_key=runtime_key,
        api_key_source=source,
        base_url=None,
        max_completion_tokens=None,
        max_research_articles=max_research_articles,
        temperature=temperature,
        demo_mode=False,
        blocked=False,
        blocked_reason=None,
        selection_source="explicit" if source in {"manual", "environment"} else "explicit",
        output_label="AI-generated draft for expert review.",
        real_llm_call=True,
        notes=notes,
    )
