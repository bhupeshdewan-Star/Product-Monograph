from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.monograph.generation_config import resolve_generation_config


class GenerationConfigTest(unittest.TestCase):
    def test_ai_mode_without_key_is_blocked(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            config = resolve_generation_config(
                mode="ai",
                provider_choice="openai",
                model="",
                api_key="",
                max_research_articles=25,
            )
        self.assertFalse(config.demo_mode)
        self.assertTrue(config.blocked)
        self.assertIsNone(config.api_key)
        self.assertIn("API key", config.blocked_reason or "")

    def test_ai_mode_uses_environment_key_when_available(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-openai-key"}, clear=False):
            config = resolve_generation_config(
                mode="ai",
                provider_choice="openai",
                model="operator-selected-model",
                api_key="",
                max_research_articles=25,
            )
        self.assertFalse(config.demo_mode)
        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.api_key, "env-openai-key")
        self.assertEqual(config.api_key_source, "environment")
        self.assertFalse(config.blocked)

    def test_demo_mode_is_explicit(self) -> None:
        config = resolve_generation_config(
            mode="demo",
            provider_choice="openai",
            model="",
            api_key="",
            max_research_articles=12,
        )
        self.assertTrue(config.demo_mode)
        self.assertIsNone(config.provider)
        self.assertEqual(config.max_research_articles, 12)
        self.assertEqual(config.output_label, "Demo draft generated from fallback/sample data.")

    def test_ai_mode_with_custom_api_key_resolves_explicit_provider(self) -> None:
        config = resolve_generation_config(
            mode="ai",
            provider_choice="anthropic",
            model="claude-haiku-4.5",
            api_key="runtime-key",
            max_research_articles=10,
        )
        self.assertFalse(config.demo_mode)
        self.assertEqual(config.provider, "anthropic")
        self.assertEqual(config.api_key, "runtime-key")
        self.assertEqual(config.api_key_source, "manual")
        self.assertEqual(config.output_label, "AI-generated draft for expert review.")

    def test_ai_mode_without_model_is_blocked_even_with_key(self) -> None:
        config = resolve_generation_config(
            mode="ai",
            provider_choice="anthropic",
            model="",
            api_key="runtime-key",
            max_research_articles=10,
        )
        self.assertTrue(config.blocked)
        self.assertIsNone(config.model)
        self.assertIn("explicit model name", config.blocked_reason or "")

    def test_all_ai_provider_dropdown_options_resolve(self) -> None:
        provider_envs = {
            "openai": {"OPENAI_API_KEY": "key-openai"},
            "anthropic": {"ANTHROPIC_API_KEY": "key-anthropic"},
            "google": {"GOOGLE_API_KEY": "key-google"},
            "deepseek": {"DEEPSEEK_API_KEY": "key-deepseek"},
            "groq": {"GROQ_API_KEY": "key-groq"},
            "openrouter": {"OPENROUTER_API_KEY": "key-openrouter"},
        }
        for provider, env in provider_envs.items():
            with self.subTest(provider=provider):
                with patch.dict(os.environ, env, clear=False):
                    config = resolve_generation_config(
                        mode="ai",
                        provider_choice=provider,
                        model=f"operator-selected-{provider}",
                        api_key="",
                        max_research_articles=10,
                    )
                self.assertFalse(config.blocked)
                self.assertEqual(config.provider, provider)
                self.assertEqual(config.api_key_source, "environment")

    def test_invalid_ai_provider_is_blocked(self) -> None:
        config = resolve_generation_config(
            mode="ai",
            provider_choice="bogus",
            model="ignored",
            api_key="",
            max_research_articles=10,
        )
        self.assertFalse(config.demo_mode)
        self.assertTrue(config.blocked)
        self.assertTrue(any("Invalid provider" in note for note in config.notes))

    def test_local_provider_without_key_is_allowed(self) -> None:
        config = resolve_generation_config(
            mode="local",
            model="llama3.1",
            api_key="",
            base_url="http://localhost:11434/v1",
            max_research_articles=10,
        )
        self.assertFalse(config.demo_mode)
        self.assertEqual(config.provider, "openai-compatible local")
        provider_cfg = config.to_provider_config()
        self.assertIsNotNone(provider_cfg)
        self.assertEqual(provider_cfg.provider, "openai")
        self.assertEqual(provider_cfg.base_url, "http://localhost:11434/v1")
        self.assertFalse(provider_cfg.strict)


if __name__ == "__main__":
    unittest.main()
