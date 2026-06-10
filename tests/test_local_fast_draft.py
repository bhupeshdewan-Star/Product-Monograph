from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import app
from src.agents.providers.base import ProviderConfig


class LocalFastDraftTest(unittest.TestCase):
    def test_effective_local_research_cap_clamps_to_small_fast_draft_window(self) -> None:
        self.assertEqual(app._effective_local_research_cap(30, True, 5), 5)
        self.assertEqual(app._effective_local_research_cap(4, True, 5), 4)
        self.assertEqual(app._effective_local_research_cap(30, False, 5), 30)

    def test_compact_evidence_package_limits_records_and_context(self) -> None:
        evidence_package = {
            "sources": {
                "pubmed": [{"identifier": "1"} for _ in range(4)],
                "fda": [{"identifier": "fda"} for _ in range(2)],
                "ema": [{"identifier": "ema"}],
                "clinicaltrials": [{"identifier": "nct"} for _ in range(3)],
            },
            "evidence_context": "x" * 4000,
            "evidence_references": "y" * 3500,
        }

        compact = app._compact_evidence_package_for_local_draft(evidence_package, context_chars=1800)

        self.assertEqual(len(compact["sources"]["pubmed"]), 2)
        self.assertEqual(len(compact["sources"]["fda"]), 1)
        self.assertEqual(len(compact["sources"]["ema"]), 1)
        self.assertEqual(len(compact["sources"]["clinicaltrials"]), 1)
        self.assertLessEqual(len(compact["evidence_context"]), 1855)
        self.assertLessEqual(len(compact["evidence_references"]), 2255)

    def test_warm_up_local_model_sends_ready_prompt_and_small_token_budget(self) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"choices": [{"message": {"content": "ready"}}]}

        with patch("src.agents.providers.base.requests.post", return_value=response) as mock_post:
            provider_config = ProviderConfig(
                provider="openai",
                model="gemma4:e4b",
                api_key=None,
                base_url="http://localhost:11434/v1",
                strict=True,
            )
            result = app._warm_up_local_model(provider_config, "gemma4:e4b")

        self.assertTrue(result["ok"])
        self.assertEqual(result["response"], "ready")
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["messages"][-1]["content"], "Reply with only: ready")
        self.assertEqual(payload["max_tokens"], 5)
        self.assertEqual(payload["max_completion_tokens"], 5)


if __name__ == "__main__":
    unittest.main()
