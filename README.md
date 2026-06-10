# Product Monograph Champ

Product Monograph Champ is a provider-agnostic product monograph generator with integrated audit agents.

## Purpose

The app generates draft pharmaceutical product monographs, validates them against SOP rules, exports them in multiple formats, and exposes universal audit agents for:

- accessibility checks
- checklist-to-schema conversion
- reusable audit runs

The monograph workflow has three explicit modes:

- `AI Mode` - professional provider-backed generation with a required API key
- `Demo Mode` - deterministic fallback/sample-data generation for UI and workflow testing
- `Local Model Mode` - OpenAI-compatible localhost or proxy endpoints with no commercial API key

The interface also has two presentation modes:

- `User Mode` - clean, clinician-friendly view with scorecards and readable summaries
- `Developer Mode` - diagnostics, preflight payloads, discovery details, and raw JSON internals

The interface also includes a theme selector and two information tabs:

- `About` - product, build, legal, and technology details
- `Help` - quick start, workflow walkthrough, mode guidance, and export guidance

## Medical Disclaimer

This tool generates draft content only. It is not a substitute for medical judgment, regulatory review, or final approval by qualified professionals.

## Project Structure

- `app.py` - Streamlit app
- `config.py` - environment-driven settings
- `src/monograph/` - monograph generation, prompts, schemas, validation helpers, fallback content, model discovery
- `src/agents/` - provider-agnostic audit agents
- `src/services/` - data sources, exports, history
- `tests/` - unit tests

## Setup

```bash
python -m pip install -r requirements.txt
```

## Environment Variables

Optional runtime configuration:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `DEEPSEEK_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_MODEL`
- `ANTHROPIC_MODEL`
- `GOOGLE_MODEL`
- `DEEPSEEK_MODEL`
- `GROQ_MODEL`
- `OPENROUTER_MODEL`
- `LOCAL_MODEL`
- `DEFAULT_PROVIDER`
- `GLOBAL_AGENTS_SCHEMA_DIR`
- `APP_NAME`
- `APP_TAGLINE`
- `MEDICAL_DISCLAIMER`

AI Mode requires a provider API key either from the sidebar or the matching environment variable. Demo Mode never requires a key. Local Model Mode uses an OpenAI-compatible base URL and does not require a commercial API key.

## Run the App

```bash
streamlit run app.py
```

## Run the Audit API

```bash
python -m uvicorn src.agents.api.server:app --reload --port 8010
```

## Run Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Exports

The app can generate:

- JSON
- Markdown
- PDF
- DOCX
- XLSX
- Print-ready HTML
- Google Docs import template

Draft placeholders are included for tables, diagrams, images, and graphs. They are clearly labeled as placeholders and must be replaced with verified content before publication.
PDF, DOCX, and HTML exports render real tables from markdown-style table blocks when present.

## Accessibility Review

The Audit Agents area includes both heuristic accessibility checks and an optional rendered-page accessibility review path. When Playwright is available, the app can inspect the rendered DOM; when an Axe-core script is available, it can layer in Axe-based findings as well. If those tools are not installed, the app falls back gracefully to the existing heuristic accessibility checker.

## Agent Usage

### A11Y Checker

```python
from src.agents.a11y.checker import check_accessibility

result = check_accessibility("https://example.com")
```

### Audit Builder

```python
from src.agents.auditor.builder import build_audit_schema

schema = build_audit_schema("https://istapage.com/blog/landing-page-audit-checklist")
```

### Audit Runner

```python
from src.agents.auditor.runner import run_audit

result = run_audit("https://example.com", "landing_page_audit_v1")
```

### Provider Configuration

Pass runtime provider config only. The adapters support OpenAI, Anthropic, Gemini, DeepSeek, Groq, OpenRouter-compatible, and local API-compatible models.

## Limitations

- External source fetching can fail in restricted network environments.
- Demo Mode includes deterministic fallback output and is intended for UI testing and draft review.
- The audit agents are static-DOM and snapshot based unless the caller provides richer HTML.
- The project is optimized for modularity and portability, not for full enterprise workflow orchestration yet.
