from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from src.agents.providers.openai_provider import OpenAIProvider
from src.agents.providers.base import ProviderError


class ProviderTimeoutTest(unittest.TestCase):
    def test_local_loopback_timeout_is_extended_to_300_seconds(self) -> None:
        provider = OpenAIProvider(base_url="http://localhost:11434/v1", timeout=60)
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        observed_timeouts: list[float] = []

        def fake_post(url, headers=None, json=None, timeout=None):
            observed_timeouts.append(timeout)
            return response

        with patch("src.agents.providers.base.requests.post", side_effect=fake_post):
            output = provider.generate(
                prompt="test prompt",
                system_prompt="system",
                model="gemma4:e4b-it-qat",
                api_key="",
                temperature=0.2,
            )

        self.assertEqual(output, "ok")
        self.assertEqual(observed_timeouts, [300.0])

    def test_cloud_timeout_keeps_default_provider_timeout(self) -> None:
        provider = OpenAIProvider(base_url="https://api.openai.com/v1", timeout=60)
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        observed_timeouts: list[float] = []

        def fake_post(url, headers=None, json=None, timeout=None):
            observed_timeouts.append(timeout)
            return response

        with patch("src.agents.providers.base.requests.post", side_effect=fake_post):
            output = provider.generate(
                prompt="test prompt",
                system_prompt="system",
                model="gpt-4o-mini",
                api_key="runtime-key",
                temperature=0.2,
            )

        self.assertEqual(output, "ok")
        self.assertEqual(observed_timeouts, [60])

    def test_local_timeout_raises_friendly_message(self) -> None:
        provider = OpenAIProvider(base_url="http://localhost:11434/v1", timeout=60)

        with patch("src.agents.providers.base.requests.post", side_effect=requests.exceptions.Timeout("read timed out")):
            with self.assertRaises(ProviderError) as ctx:
                provider.generate(
                    prompt="test prompt",
                    system_prompt="system",
                    model="gemma4:e4b-it-qat",
                    api_key="",
                    temperature=0.2,
                )

        message = str(ctx.exception)
        self.assertIn("Local model timed out", message)
        self.assertIn("openai", message)
        self.assertIn("Max research results", message)


if __name__ == "__main__":
    unittest.main()
