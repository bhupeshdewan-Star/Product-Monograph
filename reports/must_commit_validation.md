# Must Commit Validation

Source list validated from [repository_reconciliation.md](repository_reconciliation.md).

## Method

- Verified active-path references with targeted `rg` checks against the runtime callers already identified in the audit reports.
- Ran an import smoke test across every runtime module in the `Must Commit` set.
- Executed the dedicated regression test for `tests/test_monograph_generator.py`.
- Treated a successful import as evidence of no missing imports or broken references in the import graph for that module.

## Summary

- Runtime modules in `A. Must Commit`: confirmed imported or executed by the active production path, no import failures, no broken references observed in smoke tests.
- Test artifact in `A. Must Commit`: confirmed executable via `unittest`; not a runtime dependency, but safe to commit as regression coverage.

## File-by-File Validation

### App and Config

| File | Active path evidence | Import / execution result | Missing imports | Broken references | Safe to commit |
| --- | --- | --- | --- | --- | --- |
| `app.py` | Imported directly by the active Streamlit entrypoint and verified in production smoke tests. | `OK app` | None observed | None observed | Yes |
| `config.py` | Imported by active runtime modules, including the Streamlit app and generation configuration path. | `OK config` | None observed | None observed | Yes |

### Provider Layer

| File | Active path evidence | Import / execution result | Missing imports | Broken references | Safe to commit |
| --- | --- | --- | --- | --- | --- |
| `src/agents/providers/base.py` | Imported by `provider_factory` and the concrete providers used by the generator stack. | `OK src.agents.providers.base` | None observed | None observed | Yes |
| `src/agents/providers/anthropic_provider.py` | Imported by `src/agents/providers/provider_factory.py`. | `OK src.agents.providers.anthropic_provider` | None observed | None observed | Yes |
| `src/agents/providers/deepseek_provider.py` | Imported by `src/agents/providers/provider_factory.py`. | `OK src.agents.providers.deepseek_provider` | None observed | None observed | Yes |
| `src/agents/providers/google_provider.py` | Imported by `src/agents/providers/provider_factory.py`. | `OK src.agents.providers.google_provider` | None observed | None observed | Yes |
| `src/agents/providers/groq_provider.py` | Imported by `src/agents/providers/provider_factory.py`. | `OK src.agents.providers.groq_provider` | None observed | None observed | Yes |
| `src/agents/providers/openai_provider.py` | Imported by `src/agents/providers/provider_factory.py`. | `OK src.agents.providers.openai_provider` | None observed | None observed | Yes |
| `src/agents/providers/openrouter_provider.py` | Imported by `src/agents/providers/provider_factory.py`. | `OK src.agents.providers.openrouter_provider` | None observed | None observed | Yes |

### Monograph Path

| File | Active path evidence | Import / execution result | Missing imports | Broken references | Safe to commit |
| --- | --- | --- | --- | --- | --- |
| `src/monograph/executive_summary.py` | Imported by `app.py`; also covered by fallback-quality tests. | `OK src.monograph.executive_summary` | None observed | None observed | Yes |
| `src/monograph/fallback_content.py` | Imported by `app.py`, `src/monograph/generator.py`, and `src/monograph/executive_summary.py`. | `OK src.monograph.fallback_content` | None observed | None observed | Yes |
| `src/monograph/generation_config.py` | Imported by `app.py` and the verification suites. | `OK src.monograph.generation_config` | None observed | None observed | Yes |
| `src/monograph/generator.py` | Imported by `app.py` and exercised by multiple verification suites. | `OK src.monograph.generator` | None observed | None observed | Yes |
| `src/monograph/model_discovery.py` | Imported by `app.py` and exercised by model-discovery tests. | `OK src.monograph.model_discovery` | None observed | None observed | Yes |
| `src/monograph/prompts.py` | Imported by `src/monograph/generator.py` and `src/monograph/executive_summary.py`. | `OK src.monograph.prompts` | None observed | None observed | Yes |
| `src/monograph/sop_engine.py` | Imported by `app.py`, `src/monograph/generator.py`, and `src/monograph/validators.py`. | `OK src.monograph.sop_engine` | None observed | None observed | Yes |

### Audit / Accessibility

| File | Active path evidence | Import / execution result | Missing imports | Broken references | Safe to commit |
| --- | --- | --- | --- | --- | --- |
| `src/agents/a11y/rendered.py` | Imported by `app.py` and covered by `tests/test_rendered_a11y.py`. | `OK src.agents.a11y.rendered` | None observed | None observed | Yes |

### Export Framework

| File | Active path evidence | Import / execution result | Missing imports | Broken references | Safe to commit |
| --- | --- | --- | --- | --- | --- |
| `src/services/document_generators.py` | Imported by `src/services/export_service.py`. | `OK src.services.document_generators` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/__init__.py` | Imported by `app.py`; package entrypoint re-exports the active evidence stack. | `OK src.services.evidence_retrieval` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/cache.py` | Imported by the evidence-retrieval package entrypoint. | `OK src.services.evidence_retrieval.cache` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/clinicaltrials_client.py` | Imported by the evidence-retrieval package entrypoint and used in evidence tests. | `OK src.services.evidence_retrieval.clinicaltrials_client` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/ema_client.py` | Imported by the evidence-retrieval package entrypoint and used in evidence tests. | `OK src.services.evidence_retrieval.ema_client` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/fda_client.py` | Imported by the evidence-retrieval package entrypoint and used in evidence tests. | `OK src.services.evidence_retrieval.fda_client` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/local_vault.py` | Imported by the evidence-retrieval package entrypoint and used in local vault tests. | `OK src.services.evidence_retrieval.local_vault` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/normalizer.py` | Imported by the evidence-retrieval package entrypoint and used in evidence tests. | `OK src.services.evidence_retrieval.normalizer` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/orchestrator.py` | Imported by the evidence-retrieval package entrypoint and used by `app.py`. | `OK src.services.evidence_retrieval.orchestrator` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/pubmed_client.py` | Imported by the evidence-retrieval package entrypoint and used in evidence tests. | `OK src.services.evidence_retrieval.pubmed_client` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/schemas.py` | Imported by the evidence-retrieval package entrypoint and used in tests. | `OK src.services.evidence_retrieval.schemas` | None observed | None observed | Yes |
| `src/services/evidence_retrieval/traceability.py` | Imported by `app.py`, `src/monograph/generator.py`, and `src/monograph/prompts.py`. | `OK src.services.evidence_retrieval.traceability` | None observed | None observed | Yes |
| `src/services/export_service.py` | Imported by `app.py` and exercised by export tests. | `OK src.services.export_service` | None observed | None observed | Yes |
| `src/services/pdf_generator.py` | Imported by `src/services/export_service.py` and used in export tests. | `OK src.services.pdf_generator` | None observed | None observed | Yes |
| `src/services/render_helpers.py` | Imported by `src/services/export_service.py`, `src/services/document_generators.py`, and `src/services/pdf_generator.py`. | `OK src.services.render_helpers` | None observed | None observed | Yes |

### Regression Coverage

| File | Active path evidence | Import / execution result | Missing imports | Broken references | Safe to commit |
| --- | --- | --- | --- | --- | --- |
| `tests/test_monograph_generator.py` | Executed directly via `python -m unittest tests.test_monograph_generator -q` and passed. This is verification coverage, not runtime code. | `Ran 1 test ... OK` | None observed | None observed | Yes |

## Validation Notes

- `src/services/evidence_retrieval/__init__.py` imported cleanly, so the package re-exports are internally consistent.
- `src/services/render_helpers.py` imported cleanly through both export and PDF-generation callers, so the shared formatting helpers are intact.
- `src/agents/providers/provider_factory.py` is the live provider dispatch layer that binds the provider implementations listed above.
- `app.py` imports the active monograph, evidence, provider, and audit paths directly; all of those modules imported successfully in the smoke test.

## Conclusion

Every item listed under `A. Must Commit` is safe to commit.

- Runtime modules are imported or executed by the active production path and passed import smoke checks.
- The only test-only file in the set executed successfully and has no broken references.
- No missing imports or broken references were observed in the validated set.
