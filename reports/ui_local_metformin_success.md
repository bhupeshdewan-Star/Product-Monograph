# Local Model Mode Success Proof

## Scenario
- Molecule: `Metformin`
- Mode: `Local Model Mode`
- Local endpoint: `http://localhost:1234/v1`
- Model: `google/gemma-4-e4b`

## Result
- `synthesis_engine.generate_monograph("Metformin", sample_sources("Metformin"), provider_config)` completed successfully.
- Monograph mode: `local`
- Sections generated: `11`
- Validation result: `valid = True`
- Validation sections: `10`
- Compliance score: `90.0`
- Export bundle keys: `google_docs`, `json`, `markdown`, `pdf`, `print_ready`, `word`, `xlsx`

## Evidence
- LM Studio returned a valid chat response from `/v1/chat/completions`.
- The UI runtime now resumes generation from a durable pending request instead of stalling after evidence warnings.

