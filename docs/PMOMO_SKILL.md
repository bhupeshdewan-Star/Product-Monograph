---
name: pmomo-skill
description: Create, review, and refine pharmaceutical product monographs with SOP-driven structure, Vancouver-style references, draft placeholders for figures/tables/graphs, and clear medical-regulatory disclaimers. Use when working on monograph drafting, evidence structuring, citation formatting, section completeness, diagram/table placeholder handling, or SOP-based quality review.
---

# PMomo Skill

## Purpose
Use this skill to produce or review pharmaceutical product monographs for Product Monograph Champ.

## Core Rules
- Follow the active SOP and the project reference docs first.
- Keep the monograph molecule-centric unless specialty framing is explicitly requested.
- Do not fabricate citations, figures, charts, or study results.
- If evidence is limited, say so transparently.
- Always include the medical/regulatory disclaimer.
- Use Vancouver-style references for all source lists and bibliographies.

## Required Output Pattern
- Executive summary
- Indications / use
- Contraindications
- Dosage and administration
- Warnings and precautions
- Adverse reactions
- Drug interactions
- Clinical pharmacology
- Clinical studies / evidence summary
- Storage / supply information when applicable
- References in Vancouver style

## Tables and Visual Assets
When a figure, flow chart, diagram, graph, or table is needed but not directly available:
- insert a clearly labeled placeholder
- render it as a styled callout in the UI and exports
- keep the label explicit, for example:
  - `[Figure 1: Mechanism of Action Diagram Placeholder]`
  - `[Table 1: Key Clinical Evidence Summary]`
  - `[Graph 1: Comparative Efficacy Overview Placeholder]`

## References
Read the project SOP and reference documents under `docs/` before drafting or reviewing.
Use Vancouver formatting consistently and preserve traceability back to the source record.

## Quality Checks
- Verify section completeness
- Check minimum content depth per section
- Check disclaimer presence
- Check reference formatting
- Check that placeholders are clearly labeled
- Check that no raw debug JSON appears in user mode output
