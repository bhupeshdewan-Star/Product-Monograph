from __future__ import annotations

import unittest
from unittest.mock import patch

from src.agents.providers.base import ProviderError
from src.monograph.generation_config import resolve_generation_config
from src.monograph.generator import synthesis_engine


def _sample_sources(molecule: str) -> dict:
    return {
        "molecule": molecule,
        "sources": {
            "pubmed": [{"title": f"{molecule} clinical outcomes"}],
            "fda": [{"drug_name": molecule}],
            "google_scholar": [],
            "open_access": [],
        },
        "total_articles": 2,
        "formatted_text": f"Sample source summary for {molecule}",
    }


class FakeProvider:
    def generate(self, *args, **kwargs):
        raise ProviderError("401 Unauthorized: invalid API key")


class AiModeFailureTest(unittest.TestCase):
    def test_fake_api_key_failure_is_friendly(self) -> None:
        config = resolve_generation_config(
            mode="ai",
            provider_choice="openai",
            model="gpt-4o-mini",
            api_key="bogus-key",
            max_research_articles=10,
        )
        provider_config = config.to_provider_config()
        self.assertIsNotNone(provider_config)

        with patch("src.monograph.generator.create_provider", return_value=FakeProvider()):
            with self.assertRaises(ProviderError) as ctx:
                synthesis_engine.generate_monograph("Paracetamol", _sample_sources("Paracetamol"), provider_config)

        self.assertIn("invalid api key", str(ctx.exception).lower())
        self.assertIn("401", str(ctx.exception))

    def test_claude_uses_selected_model_without_substitution(self) -> None:
        selected_model = "claude-haiku-4.5"
        config = resolve_generation_config(
            mode="ai",
            provider_choice="anthropic",
            model=selected_model,
            api_key="runtime-key",
            max_research_articles=10,
        )
        provider_config = config.to_provider_config()
        self.assertIsNotNone(provider_config)
        self.assertEqual(provider_config.model, selected_model)

        class CapturingProvider:
            def __init__(self) -> None:
                self.calls = []

            def generate(self, *args, **kwargs):
                self.calls.append(kwargs)
                return "generated content"

        capturing = CapturingProvider()
        with patch("src.monograph.generator.create_provider", return_value=capturing):
            synthesis_engine.generate_monograph("Paracetamol", _sample_sources("Paracetamol"), provider_config)

        self.assertTrue(capturing.calls)
        self.assertEqual(capturing.calls[0]["model"], selected_model)


if __name__ == "__main__":
    unittest.main()
