# UI Runtime State Machine Fix Report

## Root Cause
The generation UI was relying on ephemeral rerun flags, but it did not have a durable pending-generation payload to resume after the evidence-warning branch.

Specific issues:
- `Continue without evidence` and `Proceed with available evidence` only set transient flags and immediately reran, but did not persist the exact generation context.
- Old generation results and errors could survive mode switches, so Demo and AI modes could inherit stale Local state.
- There was no explicit runtime reset button for generation-only state, so users had to clear browser state manually.
- Validation and export rendering were sometimes driven by stale or empty monograph state rather than the fresh synthesis result.

## Session State Keys Changed
Added or now managed as part of the generation state machine:
- `pending_generation_request`
- `resume_generation_requested`
- `no_evidence_confirmation_pending`
- `proceed_limited_evidence`
- `evidence_refresh_requested`
- `generated_monograph`
- `generated_sources`
- `evidence_package`
- `last_generation_error`
- `generation_stage`
- `active_generation_mode`

## Buttons Fixed
- `Generate monograph`
- `Continue without evidence`
- `Proceed with available evidence`
- `Retry failed sources`
- `Cancel generation`
- `Reset generation state`

## Files Changed
- `app.py`
- `tests/test_frontend_render_state.py`

## Verification Results
Command results:
- `python -m py_compile app.py` - PASS
- `python -m unittest tests.test_app_smoke -q` - PASS
- `python -m unittest tests.test_frontend_render_state -q` - PASS
- `python -m unittest tests.test_evidence_ui -q` - PASS
- `python -m unittest tests.test_fallback_quality -q` - PASS
- `python -m unittest tests.test_local_diagnostics -q` - PASS
- `python -m unittest tests.test_ai_mode_failures -q` - PASS

Manual proof:
- Demo Mode:
  - Molecule: `Paracetamol`
  - Mode: `demo`
  - Sections: `11`
  - Validation sections: `10`
  - Compliance score: `90.0`
  - Export bundle keys present
- Local Model Mode:
  - Molecule: `Metformin`
  - Mode: `local`
  - Endpoint: `http://localhost:1234/v1`
  - Model: `google/gemma-4-e4b`
  - Sections: `11`
  - Validation sections: `10`
  - Compliance score: `90.0`
  - Export bundle keys present

## AI Mode Checked
- Checked at the code/test level via `tests.test_ai_mode_failures -q`, which passed.
- No live Claude credential test was required for this runtime fix.

## Remaining Limitations
- Live provider failures are still possible if external API keys are missing or invalid.
- Rendered accessibility review still depends on Playwright being installed and on a valid `http(s)` URL or inline HTML.
- Audit runs still depend on network availability for real external targets, although they now fall back to local HTML instead of aborting on DNS failures.

## Notes
- The generation UI now resumes from a durable pending request after evidence warnings instead of depending on browser cache state.
- Mode switches now clear stale generation runtime state so Demo and AI do not inherit Local leftovers.
- A visible sidebar status placeholder now tracks generation progress.

