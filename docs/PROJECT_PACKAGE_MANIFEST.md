# Product Monograph Champ Package Manifest

## 1. Core Application
- `app.py` - Streamlit UI and orchestration
- `config.py` - environment-driven settings
- `requirements.txt` - Python dependencies
- `src/monograph/` - generation, validation, prompt logic, fallback content, provider/model selection
- `src/agents/` - provider-agnostic A11Y and audit agents
- `src/services/` - exports, PDF/DOCX/HTML rendering, data sources, history
- `src/utils/` - text cleanup and shared utilities
- `tests/` - regression and QA coverage

## 2. Reference Docs
- `docs/BLUEPRINT_SOP_Integration_Skill_Learning.md`
- `docs/Guidance Document Product Monograph -Health Canada.pdf`
- `docs/Guidance document-Product Monograph Health canada.docx`
- `docs/PRD_Product_Monograph_Generator.md`
- `docs/Product monograph master template.docx`
- `docs/Product Monograph Project with Claud.docx`
- `docs/Product Monograph Project with Claud.rtf`
- `docs/ROADMAP_Strategic_Implementation_Plan.md`
- `docs/Skills Required to Write a Pharmaceutical Product Monograph.docx`
- `docs/Skills Required to Write a Pharmaceutical Product Monograph.pdf`
- `docs/SOP of Preparation of Product Monograph.docx`
- `docs/SOP of Preparation of Product Monograph.pdf`

## 3. Runtime Artifacts
These are generated during local use and should not be treated as source code:
- `data/monographs/*.json`
- `data/monographs/*.md`
- `data/monographs/*.pdf`
- `data/monographs/*.docx`
- `data/monographs/*.xlsx`
- `data/monographs/*print_ready.html`
- `data/monographs/*GoogleDocs_Import_*.txt`
- schema store files under `src/agents/auditor/saved_schemas/`
- audit history and cache state created by the runtime layer

## 4. Legacy Modules: Keep, Bridge, or Delete

### Keep as active bridges for compatibility
Use these only while the newer `src/` package remains the primary implementation:
- `global_a11y_checker.py`
- `global_audit_api.py`
- `global_auditor_builder.py`
- `audit_api_fastapi.py`
- `audit_api_flask.py`
- `ai_provider_manager.py`
- `vancouver_reference_formatter.py`
- `sop_engine.py`
- `sop_compliance_validator.py`
- `markdown_cleaner.py`
- `pdf_generator.py`
- `pdf_table_formatter.py`
- `document_generators.py`
- `data_sources.py`
- `executive_summary_generator.py`
- `output_history_tracker.py`
- `validator.py`

### Keep temporarily, then delete after parity checks
These are useful during migration or fallback testing, but should be removed once the `src/` package is the sole source of truth:
- `advanced_web_scraper.py`
- `data_sources_enhanced.py`
- `literature_review_generator.py`
- `free_ai_priority_manager.py`
- `free_model_fallback.py`
- `claude_synthesis.py`
- `subagent_orchestrator.py`
- `audit_api_client.py`
- `audit_cli.py`
- `audit_examples.py`
- `examples_a11y_usage.py`
- `auditor_agent_builder.py`
- `auditor_config_template.py`
- `indian_market_context.py`
- `cost_analytics.py`

### Delete or archive after migration
Once the modern package is stable, archive or remove redundant duplicates that no longer contribute unique behavior.

## Self-Learning Position
This application should not perform hidden model training. Instead, capture:
- user feedback on generated monographs
- validation results and section scores
- export diagnostics
- audit history and schema versions
- prompt/model selection outcomes

Store that runtime learning data in versioned local artifacts or a database-backed history layer. Use it to improve prompts, fallback content, validation, and skill revisions, not to silently retrain model weights.
