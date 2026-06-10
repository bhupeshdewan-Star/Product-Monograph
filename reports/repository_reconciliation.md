# Repository Reconciliation Audit

Source of truth used: the existing audit reports, especially `reports/production_verification.md`, `reports/release_readiness_assessment.md`, `reports/repo_inventory.txt`, `reports/duplicate_candidates.md`, and `reports/frontend_backend_wiring.md`.

## A. Must Commit

These files are required by the verified active production path or by the active verification surface.

- `app.py` - active Streamlit entrypoint and wiring hub.
- `config.py` - active config contract consumed by the runtime.
- `src/agents/providers/base.py` - provider base class used by active provider implementations.
- `src/agents/providers/anthropic_provider.py` - active provider implementation.
- `src/agents/providers/deepseek_provider.py` - active provider implementation.
- `src/agents/providers/google_provider.py` - active provider implementation.
- `src/agents/providers/groq_provider.py` - active provider implementation.
- `src/agents/providers/openai_provider.py` - active provider implementation.
- `src/agents/providers/openrouter_provider.py` - active provider implementation.
- `src/monograph/executive_summary.py` - active monograph generation path.
- `src/monograph/fallback_content.py` - active draft fallback path.
- `src/monograph/generation_config.py` - active provider/local-model configuration path.
- `src/monograph/generator.py` - active monograph synthesis engine.
- `src/monograph/model_discovery.py` - active local model discovery path.
- `src/monograph/prompts.py` - active prompt construction path.
- `src/monograph/sop_engine.py` - active validation/SOP enforcement path.
- `src/agents/a11y/rendered.py` - active rendered accessibility review path.
- `src/services/document_generators.py` - active export helper path.
- `src/services/evidence_retrieval/__init__.py` - active evidence retrieval package entrypoint.
- `src/services/evidence_retrieval/cache.py` - active evidence cache.
- `src/services/evidence_retrieval/clinicaltrials_client.py` - active evidence source.
- `src/services/evidence_retrieval/ema_client.py` - active evidence source.
- `src/services/evidence_retrieval/fda_client.py` - active evidence source.
- `src/services/evidence_retrieval/local_vault.py` - active local evidence merge path.
- `src/services/evidence_retrieval/normalizer.py` - active evidence normalization path.
- `src/services/evidence_retrieval/orchestrator.py` - active evidence retrieval orchestrator.
- `src/services/evidence_retrieval/pubmed_client.py` - active evidence source.
- `src/services/evidence_retrieval/schemas.py` - active evidence data model contract.
- `src/services/evidence_retrieval/traceability.py` - active traceability path.
- `src/services/export_service.py` - active export bundle path.
- `src/services/pdf_generator.py` - active PDF export path.
- `src/services/render_helpers.py` - active helper dependency imported by export/PDF generation.
- `tests/test_monograph_generator.py` - active regression coverage for the monograph engine.

## B. Should Commit

These files are not required for runtime, but they materially support release verification, regression coverage, or audit evidence preservation.

- `test_global_audit_api.py` - dedicated audit-API validation suite used in verification.
- `tests/fixtures/` - test data used by the verification suite.
- `tests/test_ai_mode_failures.py`
- `tests/test_app_import.py`
- `tests/test_app_smoke.py`
- `tests/test_auditor_builder.py`
- `tests/test_discovery_warning.py`
- `tests/test_evidence_retrieval.py`
- `tests/test_evidence_ui.py`
- `tests/test_exports.py`
- `tests/test_fallback_quality.py`
- `tests/test_generation_config.py`
- `tests/test_import_smoke.py`
- `tests/test_local_compact_prompt.py`
- `tests/test_local_diagnostics.py`
- `tests/test_local_fast_draft.py`
- `tests/test_local_vault.py`
- `tests/test_model_discovery.py`
- `tests/test_no_hardcoded_secrets.py`
- `tests/test_provider_timeout.py`
- `tests/test_rendered_a11y.py`
- `tests/test_traceability.py`
- `reports/production_verification.md`
- `reports/release_readiness_assessment.md`
- `reports/repository_reconciliation.md`

## C. Optional

These files are supportive or informational, but they are not required for the active production path.

- `.gitignore` - repository hygiene only.
- `README.md` - documentation only.
- `docs/` - reference material, guides, and templates.
- `reports/8516_smoke.png`
- `reports/blank_screen_8515.png`
- `reports/code_map.txt`
- `reports/duplicate_candidates.txt`
- `reports/duplicate_usage_check.txt`
- `reports/evidence_hits.txt`
- `reports/export_hits.txt`
- `reports/final_hardening_git_status_before.txt`
- `reports/final_release_candidate_report.md`
- `reports/git_diff_stat.txt`
- `reports/git_status_post_audit.txt`
- `reports/provider_hits.txt`
- `reports/repo_inventory.txt`
- `reports/src_tree.txt`
- `reports/ui_controls.txt`
- `reports/ui_controls_full.txt`
- `reports/validation_hits.txt`

## D. Legacy / Archive Candidates

These files are outside the verified active production path and should be treated as legacy or archival unless a separate owner still needs them.

- `advanced_web_scraper.py`
- `ai_provider_manager.py`
- `audit_api_client.py`
- `audit_api_fastapi.py`
- `audit_api_flask.py`
- `audit_cli.py`
- `audit_examples.py`
- `auditor_agent_builder.py`
- `auditor_config_template.py`
- `cost_analytics.py`
- `data_sources.py`
- `data_sources_enhanced.py`
- `document_generators.py`
- `examples_a11y_usage.py`
- `executive_summary_generator.py`
- `free_ai_priority_manager.py`
- `free_model_fallback.py`
- `global_a11y_checker.py`
- `global_audit_api.py`
- `global_auditor_builder.py`
- `indian_market_context.py`
- `literature_review_generator.py`
- `markdown_cleaner.py`
- `output_history_tracker.py`
- `pdf_generator.py`
- `pdf_table_formatter.py`
- `sop_compliance_validator.py`
- `sop_engine.py`
- `subagent_orchestrator.py`
- `validator.py`
- `vancouver_reference_formatter.py`
- `claude_synthesis.py`
- `src/monograph/provider_selector.py`
- `src/services/data_sources.py`

### Modified files that can be safely ignored for the active release

- `.gitignore`
- `README.md`
- `src/monograph/provider_selector.py`
- `src/services/data_sources.py`

## Reconciliation Summary

- Must commit: active runtime files that the verified production path imports or executes.
- Should commit: test and evidence assets that preserve the verification state.
- Optional: docs and generated reports/artifacts.
- Legacy/archive: standalone root-level duplicates and alternates that are not part of the active runtime path.
