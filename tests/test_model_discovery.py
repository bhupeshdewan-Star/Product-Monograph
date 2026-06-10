from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from src.monograph.model_discovery import model_discovery_service


class ModelDiscoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        model_discovery_service.clear()

    def test_openai_like_live_discovery_returns_models(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {"id": "gpt-4o-mini"},
                {"id": "gpt-4.1"},
            ]
        }
        with patch("src.monograph.model_discovery.requests.get", return_value=response) as mock_get:
            result = model_discovery_service.discover_models(
                provider="openai",
                api_key="runtime-key",
                base_url="https://api.openai.com/v1",
                force_refresh=True,
            )

        self.assertEqual(result.source, "live")
        self.assertEqual(result.models, ["gpt-4.1", "gpt-4o-mini"])
        mock_get.assert_called_once()

    def test_local_discovery_tries_multiple_endpoints(self) -> None:
        first = Mock()
        first.status_code = 404
        first.text = "not found"
        second = Mock()
        second.status_code = 200
        second.json.return_value = {"data": [{"id": "llama3.1"}]}

        with patch("src.monograph.model_discovery.requests.get", side_effect=[first, second]) as mock_get:
            result = model_discovery_service.discover_models(
                provider="openai-compatible local",
                base_url="http://localhost:11434/v1",
                force_refresh=True,
            )

        self.assertEqual(result.source, "live")
        self.assertEqual(result.models, ["llama3.1"])
        self.assertEqual(mock_get.call_count, 2)

    def test_cached_discovery_is_reused(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": "gpt-4o-mini"}]}
        with patch("src.monograph.model_discovery.requests.get", return_value=response):
            first = model_discovery_service.discover_models(
                provider="openai",
                api_key="runtime-key",
                base_url="https://api.openai.com/v1",
                force_refresh=True,
            )

        with patch("src.monograph.model_discovery.requests.get") as mock_get:
            second = model_discovery_service.discover_models(
                provider="openai",
                api_key="runtime-key",
                base_url="https://api.openai.com/v1",
                force_refresh=False,
            )

        self.assertEqual(first.models, second.models)
        self.assertEqual(second.source, "cached")
        mock_get.assert_not_called()

    def test_missing_local_endpoint_returns_warning(self) -> None:
        with patch("src.monograph.model_discovery.requests.get", side_effect=ConnectionError("network down")):
            result = model_discovery_service.discover_models(
                provider="openai-compatible local",
                base_url="http://localhost:11434/v1",
                force_refresh=True,
            )

        self.assertEqual(result.source, "manual")
        self.assertEqual(result.models, [])
        self.assertIn("network down", result.warning or "")


if __name__ == "__main__":
    unittest.main()
