from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.agents.providers.openai_provider import OpenAIProvider
from src.monograph.generation_config import resolve_generation_config
import app as pmc_app


class _DummyResponse:
    status_code = 200
    text = '{"choices":[{"message":{"content":"ready"}}]}'

    def json(self):
        return {"choices": [{"message": {"content": "ready"}}]}


class LocalDiagnosticsTests(unittest.TestCase):
    @patch("src.agents.providers.base.requests.post", return_value=_DummyResponse())
    def test_local_provider_captures_payload_and_timeout(self, mock_post):
        provider = OpenAIProvider(base_url="http://localhost:11434/v1", timeout=60.0)
        result = provider.generate(
            prompt="Line one.\nLine two.",
            system_prompt="Return only the requested content.",
            model="gemma4:e4b",
            api_key=None,
            temperature=0.2,
            max_completion_tokens=120,
        )

        self.assertEqual(result, "ready")
        diagnostics = provider.last_request_diagnostics
        self.assertEqual(diagnostics["provider_name"], "openai-compatible local")
        self.assertTrue(diagnostics["request_sent"])
        self.assertTrue(diagnostics["response_received"])
        self.assertEqual(diagnostics["timeout_seconds"], 300.0)
        self.assertEqual(diagnostics["payload"]["model"], "gemma4:e4b")
        self.assertEqual(diagnostics["payload"]["max_tokens"], 120)
        self.assertEqual(diagnostics["payload"]["max_completion_tokens"], 120)
        self.assertEqual(diagnostics["temperature"], 0.2)
        self.assertEqual(diagnostics["max_tokens"], 120)
        self.assertGreater(diagnostics["payload_characters"], 0)
        self.assertGreater(diagnostics["estimated_prompt_tokens"], 0)
        mock_post.assert_called_once()

    def test_tiny_local_test_helper_uses_tiny_prompt_and_no_evidence(self):
        class DummyProvider:
            def __init__(self):
                self.calls = []
                self.last_request_diagnostics = {
                    "request_sent": True,
                    "response_received": True,
                    "payload": {},
                }

            def generate(self, **kwargs):
                self.calls.append(kwargs)
                return "ready"

        dummy = DummyProvider()
        provider_cfg = resolve_generation_config(
            mode="local",
            provider_choice="openai-compatible local",
            model="gemma4:e4b",
            api_key="",
            base_url="http://localhost:11434/v1",
            temperature=0.2,
        ).to_provider_config()

        with patch("app.create_provider", return_value=dummy):
            result = pmc_app._run_tiny_local_test(provider_cfg, "gemma4:e4b")

        self.assertTrue(result["ok"])
        self.assertEqual(result["prompt"], "Write a 3-line monograph for Paracetamol.")
        self.assertEqual(dummy.calls[0]["max_completion_tokens"], 120)
        self.assertEqual(dummy.calls[0]["prompt"], "Write a 3-line monograph for Paracetamol.")
        self.assertEqual(dummy.calls[0]["system_prompt"], "Write a 3-line monograph for Paracetamol. Return only the monograph.")
        self.assertNotIn("evidence_package", dummy.calls[0])

    def test_local_model_sidebar_rendering_uses_updated_prompt_estimate_signature(self):
        class FakeSidebar:
            def __init__(self) -> None:
                self.calls = []

            def subheader(self, *args, **kwargs):
                self.calls.append(("subheader", args, kwargs))

            def selectbox(self, *args, **kwargs):
                label = args[0] if args else kwargs.get("label", "")
                self.calls.append(("selectbox", label, kwargs))
                if label == "Provider":
                    return "Local Model"
                if label == "Available models":
                    return "gemma4:e4b"
                return ""

            def text_input(self, *args, **kwargs):
                label = args[0] if args else kwargs.get("label", "")
                self.calls.append(("text_input", label, kwargs))
                if label == "Base URL":
                    return "http://localhost:11434/v1"
                if label == "Manual model override":
                    return ""
                return ""

            def caption(self, *args, **kwargs):
                self.calls.append(("caption", args, kwargs))

            def checkbox(self, *args, **kwargs):
                label = args[0] if args else kwargs.get("label", "")
                self.calls.append(("checkbox", label, kwargs))
                defaults = {
                    "Fast local draft": True,
                    "Local Compact Prompt Mode": True,
                    "Section-by-section local generation": True,
                }
                return defaults.get(label, False)

            def slider(self, *args, **kwargs):
                self.calls.append(("slider", args, kwargs))
                return 5

            def button(self, *args, **kwargs):
                label = args[0] if args else kwargs.get("label", "")
                self.calls.append(("button", label, kwargs))
                return False

            def warning(self, *args, **kwargs):
                self.calls.append(("warning", args, kwargs))

            def success(self, *args, **kwargs):
                self.calls.append(("success", args, kwargs))

            def info(self, *args, **kwargs):
                self.calls.append(("info", args, kwargs))

        fake_st = SimpleNamespace(
            sidebar=FakeSidebar(),
            session_state={
                "molecule_name_input": "Paracetamol",
                "local_evidence_summary": {"files_loaded": 2, "word_count": 500},
            },
            warning=lambda *args, **kwargs: None,
            info=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
            caption=lambda *args, **kwargs: None,
            markdown=lambda *args, **kwargs: None,
            json=lambda *args, **kwargs: None,
            rerun=lambda *args, **kwargs: None,
        )

        with patch.object(pmc_app, "st", fake_st), patch.object(
            pmc_app,
            "_resolve_model_selection",
            return_value={
                "provider": "openai-compatible local",
                "provider_label": "Local Model",
                "env_key_detected": False,
                "manual_key_supplied": False,
                "api_key": "",
                "base_url": "http://localhost:11434/v1",
                "discovery": SimpleNamespace(warning="", models=["gemma4:e4b"], source="live"),
                "model_options": ["gemma4:e4b"],
                "selected_model": "gemma4:e4b",
                "selected_model_source": "live",
                "warning": "",
            },
        ), patch.object(pmc_app, "_render_temperature_controls", return_value=0.3):
            ui = pmc_app._render_provider_mode_controls("local", "local_test")

        self.assertEqual(ui["model"], "gemma4:e4b")
        self.assertIn("local_compact_prompt_mode", ui)
        self.assertIn("local_section_generation_mode", ui)
        self.assertIn("prompt_estimate", ui)
        self.assertIn("estimated_prompt_tokens", ui["prompt_estimate"])
        self.assertGreater(ui["prompt_estimate"]["estimated_prompt_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
