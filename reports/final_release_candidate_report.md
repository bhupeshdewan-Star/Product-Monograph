# Product Monograph Champ Release-Candidate Hardening Report

## Executive Summary

I completed a stabilization pass on the local release-candidate branch and verified the codebase with the full unit suite, a fresh Streamlit start, and an HTTP smoke check on `http://localhost:8515`.

The main issues fixed in this pass were:

- a broken `source_status`/evidence-status branch in `app.py`
- user-mode error leakage from several exception handlers
- a missing `main` attribute required by the import test
- regression coverage for source-status label extraction and user-mode discovery warnings

## Bugs Found

- `app.py` had a malformed evidence-status block that broke indentation and mixed generation-branch logic into the wrong scope.
- `app.py` exposed raw exception text in several user-facing error paths.
- `app.py` no longer exposed a `main` attribute, which failed the import smoke test.

## Bugs Fixed

- Restored a valid source-status helper path with `_available_evidence_source_labels(...)`.
- Sanitized user-mode discovery warnings via `_discovery_warning_to_text(...)`.
- Sanitized user-facing exception paths through `_report_exception(...)`.
- Added a compatibility `main()` shim for imports and direct execution.
- Added regression tests for source-status label extraction and discovery warning sanitization.

## Files Changed

Files changed in this pass:

- [`app.py`](../app.py)
- [`tests/test_evidence_ui.py`](../tests/test_evidence_ui.py)
- [`reports/final_hardening_git_status_before.txt`](./final_hardening_git_status_before.txt)
- [`reports/final_release_candidate_report.md`](./final_release_candidate_report.md)

Note: the worktree already contained many pre-existing modified and untracked files before this pass. I did not attempt to reclassify those as part of this stabilization step.

## Tests Added

- `tests/test_evidence_ui.py`
  - source-status label extraction
  - discovery warning sanitization for user mode

## Test Results

- `python -m unittest discover -s tests -p "test_*.py"`: passed, `64` tests
- `python -m py_compile app.py`: passed

## Manual Smoke Test Results

- Streamlit started cleanly on port `8515`.
- `Invoke-WebRequest http://localhost:8515` returned `200`.
- The app process remained up after startup.

I did not perform interactive browser clicks in this terminal-only pass, so the following remain code-path and unit-test verified rather than visually re-clicked:

- Demo Mode generation flow
- AI Mode live provider call flow
- Local Model Mode warm-up / tiny-test buttons
- Dark-mode visual inspection

## Provider Compatibility Matrix

Status here means code-path verified and covered by tests, not live-provider authenticated in this pass.

| Provider | Model discovery | Manual model entry | Exact selected model used | Local key-free mode |
| --- | --- | --- | --- | --- |
| OpenAI | Yes | Yes | Yes | No |
| Claude / Anthropic | Yes | Yes | Yes | No |
| Gemini / Google | Yes | Yes | Yes | No |
| DeepSeek | Yes | Yes | Yes | No |
| Groq | Yes | Yes | Yes | No |
| OpenRouter | Yes | Yes | Yes | No |
| Local Model / Ollama | Yes | Yes | Yes | Yes |

## Evidence Source Matrix

| Source | Retrieval path | Current behavior |
| --- | --- | --- |
| Local Evidence Vault | Local file parsing and merge path | Works; full-path display is gated to Developer Mode |
| PubMed | Public API client | Covered by parsing tests |
| FDA | Public API client | Covered by parsing tests |
| EMA | Public API client | Covered by graceful-unavailable tests |
| ClinicalTrials.gov | API v2 client | Uses v2 `studies` endpoint; legacy `study_fields` path is not present |

## Export Matrix

| Export | Status | Notes |
| --- | --- | --- |
| PDF | Passed | Generated in tests |
| DOCX | Passed | Generated in tests |
| XLSX | Passed | Generated in tests |
| JSON | Passed | Generated in tests |
| Markdown | Passed | Generated in tests |
| Print-ready HTML | Passed | Generated in tests |
| Google Docs import template | Passed | Generated in tests |

## UI / UX Findings

- User Mode now keeps discovery failures and runtime exceptions generic.
- Developer Mode still exposes diagnostics and raw payloads.
- The app continues to expose both light and dark theme styling paths in the Streamlit UI.
- The main workflow still uses the sidebar controls, generate button, and export section.

## Security / Privacy Findings

- No hardcoded secrets were introduced in this pass.
- Local evidence full paths remain hidden in User Mode.
- Developer Mode can still reveal diagnostic details as intended.
- No GitHub push / commit / PR / remote changes were performed.

## Remaining Known Limitations

- Live provider calls were not exercised against external paid APIs in this terminal-only pass.
- Full interactive browser-only visual verification of Light/Dark Mode was not re-clicked here.
- External evidence retrieval can still fail when the environment blocks outbound network access.

## Final Readiness Score

`90/100`

Rationale:

- core runtime and unit coverage are now clean
- app starts cleanly
- error surfacing is materially improved
- interactive provider/evidence flows are still environment-dependent and were not all live-clicked in this pass

## GitHub Readiness Recommendation

Do not push yet.

The local RC is stable enough for another round of browser-based validation of the key user journeys, especially Demo Mode, AI Mode, Local Model Mode, and the evidence-confirmation flow. After that, it is reasonable to promote to release candidate for a local-only handoff.

## `git status --short`

```text
 M .gitignore
 M README.md
 M app.py
 M config.py
 M src/agents/providers/anthropic_provider.py
 M src/agents/providers/base.py
 M src/agents/providers/deepseek_provider.py
 M src/agents/providers/google_provider.py
 M src/agents/providers/groq_provider.py
 M src/agents/providers/openai_provider.py
 M src/agents/providers/openrouter_provider.py
 M src/monograph/executive_summary.py
 M src/monograph/generator.py
 M src/monograph/prompts.py
 M src/monograph/provider_selector.py
 M src/monograph/sop_engine.py
 M src/services/data_sources.py
 M src/services/document_generators.py
 M src/services/export_service.py
 M src/services/pdf_generator.py
 M tests/test_monograph_generator.py
?? advanced_web_scraper.py
?? ai_provider_manager.py
?? audit_api_client.py
?? audit_api_fastapi.py
?? audit_api_flask.py
?? audit_cli.py
?? audit_examples.py
?? auditor_agent_builder.py
?? auditor_config_template.py
?? claude_synthesis.py
?? cost_analytics.py
?? data_sources.py
?? data_sources_enhanced.py
?? docs/
?? document_generators.py
?? examples_a11y_usage.py
?? executive_summary_generator.py
?? free_ai_priority_manager.py
?? free_model_fallback.py
?? global_a11y_checker.py
?? global_audit_api.py
?? global_auditor_builder.py
?? indian_market_context.py
?? literature_review_generator.py
?? markdown_cleaner.py
?? output_history_tracker.py
?? pdf_generator.py
?? pdf_table_formatter.py
?? reports/
?? sop_compliance_validator.py
?? sop_engine.py
?? src/agents/a11y/rendered.py
?? src/monograph/fallback_content.py
?? src/monograph/generation_config.py
?? src/monograph/model_discovery.py
?? src/services/evidence_retrieval/
?? src/services/render_helpers.py
?? subagent_orchestrator.py
?? test_a11y_checker.py
?? test_api.py
?? test_auditor.py
?? test_claude.py
?? test_global_audit_api.py
?? tests/fixtures/
?? tests/test_ai_mode_failures.py
?? tests/test_app_import.py
?? tests/test_discovery_warning.py
?? tests/test_evidence_retrieval.py
?? tests/test_evidence_ui.py
?? tests/test_exports.py
?? tests/test_fallback_quality.py
?? tests/test_generation_config.py
?? tests/test_local_compact_prompt.py
?? tests/test_local_diagnostics.py
?? tests/test_local_fast_draft.py
?? tests/test_local_vault.py
?? tests/test_model_discovery.py
?? tests/test_provider_timeout.py
?? tests/test_rendered_a11y.py
?? tests/test_traceability.py
?? validator.py
?? vancouver_reference_formatter.py
```
