# Product Monograph Champ

Clean Codex-based product monograph generator with provider-agnostic global audit agents.

## Purpose

This app generates draft pharmaceutical product monographs, validates them against SOP rules, exports them in multiple formats, and exposes universal audit agents for:

- accessibility checks
- checklist-to-schema conversion
- reusable audit runs

## Medical Disclaimer

This tool generates draft content only. It is not a substitute for medical judgment, regulatory review, or final approval by qualified professionals.

## Project Structure

- `app.py` - Streamlit app
- `config.py` - environment-driven settings
- `src/monograph/` - monograph generation, prompts, schemas, validation helpers
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
- The monograph generator includes deterministic fallback output when no provider is supplied.
- The audit agents are static-DOM and snapshot based unless the caller provides richer HTML.
- The project is optimized for modularity and portability, not for full enterprise workflow orchestration yet.
