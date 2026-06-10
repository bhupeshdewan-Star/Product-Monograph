# TECHNICAL BLUEPRINT: SOP Integration & Skill Learning
## AI-Powered Product Monograph Generator

**Document Purpose:** Define HOW your digitized SOPs and natural language skill files become executable rules within the AI generation system.

---

## PART 1: SOP TEMPLATE PARSING & INTEGRATION

### 1.1 Understanding Your Current SOP Format

**Your Current State:** SOPs are digitized as templates/documents

**Likely Format Examples:**
```
Format A: Word Document with Table Structure
┌─────────────────────────────────────────┐
│ PRODUCT MONOGRAPH TEMPLATE              │
├─────────────────────────────────────────┤
│ Section # │ Section Name │ Requirements  │
│ 1         │ Pharmacology │ 500-800 words │
│           │              │ Min 3 sources │
│           │              │ MoA required  │
└─────────────────────────────────────────┘

Format B: Checklist Format
□ Pharmacology (pharmacodynamics, mechanism)
□ Pharmacokinetics (absorption, metabolism)
  ├─ SUBHEADING: Renal Impairment Section (required)
  ├─ Must cite ≥2 kinetic studies
  └─ Dose adjustments table (mandatory)
□ [etc.]

Format C: Narrative SOP
"Product monographs are structured to provide healthcare professionals 
with comprehensive information. The pharmacology section should explain 
the mechanism of action at both the molecular and physiological level, 
supported by peer-reviewed literature. A minimum of 5 high-quality sources 
should be cited..."
```

### 1.2 SOP to Executable Rules Conversion

**Step 1: Extract Narrative SOP**
```
Your SOP Document (Raw):
"Pharmacology sections must provide both molecular mechanism 
and physiological context. Minimum word count is 500; maximum 800. 
Assume audience is a medical resident (PGY2 level). Cite at least 
5 peer-reviewed studies. Comparative efficacy with similar drugs 
should be mentioned if data exists."
```

**Step 2: Parse to Structured Rules**
```yaml
# SOP Rule Object for "Pharmacology Section"

section_id: "pharmacology"
section_name: "Pharmacology"

content_requirements:
  word_count:
    min: 500
    max: 800
    validation_rule: "length_check"
    
  required_subsections:
    - mechanism_of_action
      * molecular_level: "Receptor/enzyme interaction specifics"
      * physiological_level: "Downstream effects in organism"
    - comparative_efficacy:
      * required_if: "competitor_molecules_exist"
      * example: "Unlike Drug A (inhibits X), Drug X inhibits both X and Y"

tone_and_clarity:
  target_audience: "Medical resident (PGY-2)"
  readability_level: "Flesch-Kincaid 12-14 grade"
  max_jargon_percentage: 15%

evidence_requirements:
  min_sources: 5
  source_types:
    - peer_reviewed_journals: {weight: 1.0, min_count: 4}
    - conference_abstracts: {weight: 0.5, min_count: 1}
  recency:
    preference: "Last 10 years"
    exceptions: "Foundational studies can be older"

validation_checklist:
  - [ ] word_count_within_range(500, 800)
  - [ ] subsection_mechanism_present()
  - [ ] molecular_level_explanation()
  - [ ] physiological_level_explanation()
  - [ ] peer_reviewed_count >= 4
  - [ ] readability_grade_12_to_14()
  - [ ] comparative_efficacy_if_applicable()
  - [ ] no_unsupported_claims()

quality_metrics:
  acceptable_thresholds:
    word_count_adherence: 100%  # Must be in range
    subsection_completeness: 100%  # All subsections present
    source_quality_score: >=85%  # Average quality of sources
    readability_match: ±1 grade level

auto_improvement_rules:
  if_too_technical:
    action: "Reduce jargon, add functional explanations"
    feedback_trigger: "User complaint: 'too technical'"
  if_too_short:
    action: "Expand with additional mechanism detail or add evidence"
    min_addition: 100_words
  if_sources_weak:
    action: "Recommend higher-quality sources"
    escalation: "Flag for human review"
```

**Step 3: Inject into Generation Pipeline**
```python
# Pseudo-code: How SOP rules become generation instructions

def generate_pharmacology_section(molecule_data, sources):
    
    # Load SOP rules for this section
    sop_rules = load_sop_rules("pharmacology")
    
    # Build Claude prompt with SOP constraints
    prompt = f"""
    You are generating a Pharmacology section for a product monograph.
    
    CONSTRAINTS (from our SOP):
    - Word count: {sop_rules.word_count.min}-{sop_rules.word_count.max} words
    - Target audience: {sop_rules.tone.target_audience}
    - Readability level: Grade {sop_rules.tone.readability_level}
    - Jargon limit: {sop_rules.tone.max_jargon_percentage}%
    
    REQUIRED SUBSECTIONS:
    {format_requirements(sop_rules.required_subsections)}
    
    AVAILABLE SOURCES:
    {format_sources(sources)}
    
    Generate the Pharmacology section now:
    """
    
    # Call Claude API
    draft_section = call_claude_api(prompt)
    
    # Validate output against SOP rules
    validation_results = validate_against_sop(draft_section, sop_rules)
    
    if validation_results.is_compliant:
        return draft_section  # Ready to use
    else:
        # Apply auto-improvement rules
        improved_section = auto_improve(draft_section, validation_results)
        return improved_section
```

---

### 1.3 Real-World Example: Mapping Your SOP

**Example Scenario:** You provide this SOP excerpt:

```
SOP Section: PHARMACOKINETICS
═════════════════════════════════════

1. STRUCTURE & CONTENT
The Pharmacokinetics section must cover:
   a) Absorption (route, rate, factors affecting)
   b) Distribution (volume of distribution, protein binding, CNS penetration)
   c) Metabolism (metabolic pathways, enzymes involved, major metabolites)
   d) Elimination (renal/hepatic clearance, half-life)

2. SPECIAL POPULATIONS (REQUIRED SUBSECTIONS)
Must include separate subsections for:
   - Renal impairment (any hint of renal involvement → must include)
   - Hepatic impairment (if metabolized by liver)
   - Geriatric population (if age-related concerns exist)
   - Pediatric population (only if pediatric indication applies)
   - Pregnancy & Lactation (required for all molecules)

3. DOSING IMPACT
For each special population with impairment:
   - Statement if dose adjustment is needed
   - Specific recommended adjustment (if available)
   - Link to Dosing section

4. EVIDENCE STANDARDS
   - Minimum 2 pharmacokinetic studies per major route/population
   - Preference for human PK studies (animal data acceptable if human unavailable)
   - Clinical context: always relate PK changes to clinical outcome

5. TECHNICAL REQUIREMENTS
   - Must NOT exceed 1200 words total
   - Each subsection: 150-300 words
   - Tables for numeric data (half-life, Cmax, renal clearance %, etc.)
   - Footnotes explaining clinical relevance of numeric values
```

**System Conversion:**

```json
{
  "section_id": "pharmacokinetics",
  "section_name": "Pharmacokinetics",
  "word_count": {
    "total_max": 1200,
    "subsection_range": [150, 300]
  },
  "required_subsections": {
    "absorption": {
      "description": "Route, rate, factors affecting",
      "word_count_target": 200,
      "min_sources": 2
    },
    "distribution": {
      "description": "Vd, protein binding, CNS penetration",
      "word_count_target": 200,
      "min_sources": 2
    },
    "metabolism": {
      "description": "Pathways, enzymes, metabolites",
      "word_count_target": 200,
      "min_sources": 2
    },
    "elimination": {
      "description": "Renal/hepatic clearance, half-life",
      "word_count_target": 200,
      "min_sources": 2
    }
  },
  "special_populations_required": [
    {
      "population": "renal_impairment",
      "conditional": "included_if_any_renal_involvement",
      "content": "severity stages, dose adjustment needed Y/N, specific adjustment if yes",
      "data_format": "descriptive + table"
    },
    {
      "population": "hepatic_impairment",
      "conditional": "included_if_hepatic_metabolism_involved",
      "content": "severity stages, dose adjustment needed Y/N, specific adjustment if yes",
      "data_format": "descriptive + table"
    },
    {
      "population": "geriatric",
      "conditional": "included_if_age_related_pk_changes_exist",
      "content": "age-related PK changes, clinical significance, dosing impact",
      "data_format": "descriptive"
    },
    {
      "population": "pediatric",
      "conditional": "included_if_pediatric_indication_applies",
      "content": "age-specific PK, dose calculations (mg/kg if applicable)",
      "data_format": "descriptive + table"
    },
    {
      "population": "pregnancy_and_lactation",
      "conditional": "always_required",
      "content": "pregnancy category, fetal risk assessment, lactation data, clinical recommendation",
      "data_format": "descriptive"
    }
  ],
  "data_presentation": {
    "tables_required_for": ["half_life", "clearance_percentages", "dose_adjustments"],
    "footnotes_required": true,
    "footnote_purpose": "Explain clinical relevance of numeric values"
  },
  "evidence_requirements": {
    "human_studies_preferred": true,
    "animal_data_acceptable_if": "human_data_unavailable",
    "min_studies_per_category": 2
  },
  "validation_checklist": [
    "total_word_count <= 1200",
    "subsection_word_counts_within_range",
    "all_required_subsections_present",
    "all_applicable_special_populations_included",
    "dose_adjustment_statements_linked_to_dosing_section",
    "pregnancy_always_included",
    "tables_present_for_numeric_data",
    "footnotes_explain_clinical_impact",
    "min_evidence_sources_per_category_met"
  ]
}
```

**During Generation, System Does This:**
```
1. DETECTION PHASE
   Analyze molecule data:
   - "Does this molecule involve renal clearance?" YES
     → Mark "renal_impairment" as REQUIRED
   - "Is this drug hepatically metabolized?" YES
     → Mark "hepatic_impairment" as REQUIRED
   - "Are there pediatric indications?" NO
     → Mark "pediatric" as OPTIONAL (can skip)

2. SOURCE IDENTIFICATION PHASE
   For each required subsection & population:
   - Search literature for human PK studies
   - If insufficient human data → allow animal studies
   - Score sources by relevance & quality
   - Curate top 3-5 per subsection

3. GENERATION PHASE
   For each subsection:
   ```
   Prompt Claude:
   "Generate Absorption section for [Molecule].
    Word count: 150-300 words
    Available studies: [list of 4 papers]
    Must explain: route, rate, factors affecting
    Clinical context: [relevant to therapeutic use]
    Output format: paragraph with embedded citations"
   ```

4. VALIDATION PHASE
   Check output:
   - Word count within 150-300? YES/NO
   - All key points covered? YES/NO
   - Clinical relevance explained? YES/NO
   - If all YES → accept; if any NO → auto-improve or flag

5. SPECIAL POPULATION HANDLING
   For each special population section:
   - Is dose adjustment needed? (Search literature)
   - If YES: "Dose adjustment recommended: reduce by X% or use absolute dose Y"
   - If NO: "No dose adjustment required"
   - Link back to Dosing section: "See Dosing section for specific recommendations"

6. ASSEMBLY
   Combine all subsections in order:
   - ABSORPTION
   - DISTRIBUTION
   - METABOLISM
   - ELIMINATION
   - [RENAL IMPAIRMENT] (if applicable)
   - [HEPATIC IMPAIRMENT] (if applicable)
   - [GERIATRIC CONSIDERATIONS] (if applicable)
   - PREGNANCY & LACTATION
```

---

## PART 2: SKILL FILE INTEGRATION & LEARNING

### 2.1 What Makes a Good Skill File?

**Skill File = Reusable Quality Rules + Learning Feedback**

**Bad Skill File (Too Vague):**
```markdown
# Skill: Evidence Quality

Always use high-quality evidence. Prefer published studies. Avoid unreliable sources.
```
❌ Why bad: No actionable rules, can't be automated, inconsistent interpretation

---

**Good Skill File (Specific, Measurable, Actionable):**
```markdown
# Skill: Evidence Quality for Clinical Efficacy Sections

## When to Apply
Every generated Clinical Efficacy section.

## The Problem This Solves
Generic drug efficacy claims without proper grading lead to:
- Regulatory criticism (insufficient evidence for claims)
- HCP skepticism (unsupported statements)
- Legal exposure (overstated benefits)

This skill ensures all efficacy claims are evidence-graded.

## Rules with Examples

### Rule 1: Evidence Grading Hierarchy
For EVERY efficacy claim, assign one of these grades:

**Level 1A - Highest Quality** (Randomized Controlled Trials, Meta-analyses)
```
Example GOOD claim:
"A meta-analysis of 12 RCTs (N=3,400) showed efficacy in reducing 
HbA1c by 1.2% (95% CI: 1.0-1.4%) compared to placebo [Grade 1A]."

Example BAD claim:
"Highly effective in controlling blood sugar."  ← No grade, no numbers
```

**Level 1B** (Large RCTs, non-inferiority studies)
```
Example GOOD:
"In the landmark PIONEER trial (N=1,200 RCT), patients achieved 
HbA1c reduction of 1.5% [Grade 1B]."
```

**Level 2** (Observational, cohort studies)
```
Example GOOD:
"Observational data (N=500 patients over 5 years) showed sustained 
blood glucose control [Grade 2]."

Example BAD:
Using Level 2 evidence for PRIMARY efficacy claim (must be Level 1)
```

**Level 3** (Case reports, mechanistic studies, expert opinion)
```
Example GOOD:
"In case reports, patients with renal impairment showed enhanced efficacy [Grade 3]."
```

### Rule 2: Numeric Specificity
EVERY efficacy claim must include specific numbers or percentage changes:

```
BAD:
"The drug is effective in treating diabetes."

GOOD:
"In a 12-week RCT, HbA1c reduction was 1.2 ± 0.3% (p<0.001)."
```

Metrics to extract from each study:
- Effect size (absolute % change or relative risk reduction)
- Confidence intervals (95% CI)
- P-value or statistical significance
- Sample size & duration
- Population characteristics (age, baseline disease severity)

### Rule 3: Primary vs. Supportive Claims
```
PRIMARY CLAIMS (must be Level 1A-1B evidence):
- Indications (FDA-approved uses)
- Efficacy in patient population studied in registration trials
- Standard dosing recommendations

SUPPORTIVE CLAIMS (can be Level 2-3 evidence):
- Efficacy in subpopulations (age groups, disease subtypes) not in registration
- Off-label efficacy (with clear disclaimer)
- Mechanistic advantages vs. competitors
```

### Rule 4: Consistency Across Sections
Clinical Efficacy claims must align with:
- Pharmacology section (mechanism must support efficacy claim)
- Safety section (if frequency of adverse effect increases with dose, must mention in efficacy)
- Dosing section (doses claimed effective must match dosing table)

Example conflict (BAD):
```
Efficacy section: "Doses of 500mg show best efficacy"
Dosing section: "Recommended dose: 250mg"
→ CONFLICT: System flags this; human review required
```

### Rule 5: Real-World Evidence Handling
```
For drugs with extensive real-world data, include:
- Sample size & heterogeneity of real-world population
- Comparison to RCT populations (are they similar?)
- Caveat: "Real-world outcomes may differ from RCT conditions"
```

## Quality Metrics (How to Measure Skill Success)

✓ METRIC 1: Evidence Grade Distribution
```
For efficacy section, require:
- ≥70% of claims supported by Level 1A-1B evidence
- ≤30% of claims supported by Level 2 evidence
- ≤10% of claims supported by Level 3 evidence

MEASURE IT:
Count total efficacy claims: [N]
Count Level 1A-1B claims: [X]
% = X/N
If % < 70% → Skill not fully applied → FLAG
```

✓ METRIC 2: Numeric Completeness
```
For each efficacy claim, check:
- Effect size stated? YES/NO
- Confidence interval? YES/NO
- P-value? YES/NO
- Sample size? YES/NO
- Study duration? YES/NO

Target: ≥80% of claims include ALL 5 elements
```

✓ METRIC 3: Consistency Check
```
Cross-check with:
- Pharmacology section claims
- Safety section (any conflicts?)
- Dosing section (efficacy doses match?)

Target: 100% consistency (zero conflicts)
```

✓ METRIC 4: Indication Coverage
```
For approved indications:
- Does efficacy section cover all FDA-approved indications? YES/NO
- Are off-label uses clearly marked? YES/NO

Target: 100% of approved indications covered
```

## Feedback Triggers (When to Update This Skill)

**Trigger 1: Regulatory Feedback**
IF: "Insufficient evidence for this claim"
THEN: Increase evidence level requirement for this indication
EXAMPLE: "Claim X was criticized for using Level 2 evidence. Next generation: require Level 1."

**Trigger 2: HCP Feedback**
IF: Multiple HCPs comment "Need more specific numbers"
THEN: Increase numeric specificity requirement

**Trigger 3: Competitive Intelligence**
IF: Competitor monograph includes evidence we missed
THEN: Revise search strategy in this skill to capture additional evidence types

**Trigger 4: New Publication**
IF: Major new study published (RCT with contrary findings)
THEN: Update skill to incorporate new evidence, assess impact on prior claims

## Skill File Version History
```
v1.0 - Original skill file (2024-01-01)
       Basic evidence grading rules

v1.1 - Added numeric specificity requirement (2024-02-15)
       After feedback: "Need more specific effect sizes"
       Result: Monograph quality scores increased by 8%

v1.2 - Added consistency check rules (2024-03-10)
       After issue: Found conflicts between Efficacy and Dosing sections
       Result: Zero consistency conflicts in v1.2-generated monographs

[CURRENT: v1.2]
```

## How This Skill Improves Over Time

**Month 1 - Baseline:**
```
Generated monographs using v1.0 of this skill
Feedback: "Claims need more evidence support"
Regulatory review: "3 claims require upgrade to Level 1A"
HCP feedback: "Unclear how numbers translate to clinical benefit"
Revision Score: 78% (need significant post-generation edits)
```

**Month 2 - After v1.1 Update:**
```
Updated skill with numeric specificity rules
Generated monographs using v1.1
Feedback: "Numbers clearer, but still some vagueness"
Regulatory review: "2 claims still weak"
HCP feedback: "Much better specificity"
Revision Score: 85% (fewer post-generation edits)
```

**Month 3 - After v1.2 Update:**
```
Added consistency checking across sections
Generated monographs using v1.2
Feedback: "Now internally consistent, stronger evidence"
Regulatory review: "Claims well-supported, no issues"
HCP feedback: "Professional, evidence-based"
Revision Score: 92% (minimal post-generation edits)
```

**Observed Pattern:**
- v1.0 → v1.1: +7 point improvement
- v1.1 → v1.2: +7 point improvement
- Trend: Each refinement reduces downstream editing work
```

## Who Maintains This Skill?
- **Primary Owner:** Medical Director
- **Contributors:** Regulatory Affairs, Clinical Trial Reviewers
- **Review Cycle:** Quarterly, or as triggered by feedback
- **Approval:** Medical Director sign-off required before deployment

```
✅ This is a GOOD skill file: specific, measurable, actionable, and self-improving
```

---

### 2.2 Skill Learning Architecture: The Complete Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    SKILL LEARNING CYCLE                          │
└──────────────────────────────────────────────────────────────────┘

PHASE 1: CREATION & VERSION CONTROL
═════════════════════════════════════════════════════════════════
Medical Director writes skill file in natural language

Example:
  Skill Name: "Evidence Quality for Clinical Efficacy"
  Format: Markdown document
  Content: Rules, examples, metrics, feedback triggers
  
  ↓
  
Upload to System:
  • System parses NL skill file (using NLP)
  • Extracts: Rules, examples, validation metrics, triggers
  • Stores in skill database
  • Assigns version 1.0
  • Creates audit trail (who, when, what)

Storage Structure:
  /skills/evidence_quality_for_clinical_efficacy/
  ├── v1.0/
  │   ├── source.md (original NL file)
  │   ├── parsed_rules.json (extracted rules)
  │   ├── validation_metrics.json (how to measure success)
  │   ├── examples.json (examples from skill file)
  │   └── creation_metadata.json (date, author, version notes)
  ├── v1.1/
  │   └── [same structure]
  └── CURRENT → v1.1 (pointer to latest active version)


PHASE 2: SKILL APPLICATION DURING MONOGRAPH GENERATION
═════════════════════════════════════════════════════════════════

When user requests monograph for molecule "Metformin":

Step 2a: Load Applicable Skills
  System identifies sections to generate:
  - Pharmacology
  - Pharmacokinetics
  - Clinical Efficacy
  - Safety
  - [etc.]
  
  For each section, load applicable skills:
  - Clinical Efficacy section → Load "Evidence Quality for Clinical Efficacy" skill
  - Safety section → Load "Safety Section Completeness" skill
  - [etc.]

Step 2b: Inject Skill Rules into Generation Prompt
  For Clinical Efficacy section:
  
  Prompt to Claude:
  """
  Generate the Clinical Efficacy section for Metformin.
  
  SKILL RULES TO FOLLOW (from "Evidence Quality for Clinical Efficacy" v1.1):
  
  Rule 1: Evidence Grading
  - Every efficacy claim MUST be assigned a grade (Level 1A, 1B, 2, or 3)
  - Level 1A = RCTs, meta-analyses
  - Primary claims (FDA indications) require Level 1A-1B
  - Supporting claims can use Level 2-3
  
  Rule 2: Numeric Specificity
  - EVERY claim must include: effect size, CI, p-value, N, duration
  Example: "HbA1c reduction of 1.2% (95% CI: 1.0-1.4%, p<0.001, N=500, 12 weeks)"
  
  Rule 3: Consistency Checking
  - Verify claims align with Pharmacology section
  - Verify claims align with Dosing section
  
  Rule 4: Coverage Requirement
  - Must cover ALL FDA-approved indications
  
  AVAILABLE SOURCES:
  [list 15 PubMed papers with abstracts]
  
  Generate now:
  """
  
  Claude generates output respecting these rules

Step 2c: Validate Output Against Skill Metrics
  After Claude generates Clinical Efficacy section:
  
  Auto-validation checklist:
  
  □ Evidence Grade Distribution
    Count claims by grade:
    - Level 1A-1B: 10 claims (70%) ✓ [meets ≥70% requirement]
    - Level 2: 3 claims (20%) ✓ [below 30% cap]
    - Level 3: 1 claim (10%) ✗ [exceeds 10% limit]
    
    ACTION: FAIL - Level 3 claim needs upgrade or removal
    
  □ Numeric Completeness
    Review each claim for: effect size, CI, p-value, N, duration
    
    Claim 1: "HbA1c reduction 1.2% (95% CI 1.0-1.4%, p<0.001, N=500, 12-week)"
    ✓ All elements present
    
    Claim 2: "Improved glycemic control"
    ✗ MISSING: effect size, CI, p-value, N, duration
    
    Claim 3: "Reduced cardiovascular mortality by 18% (p=0.04, N=1,200)"
    ✗ MISSING: CI, study duration
    
    ACTION: FAIL - Claims 2 and 3 need more specificity
    
  □ Consistency Check
    Pharmacology says: "Mechanism: Increases GLP-1 sensitivity"
    Efficacy claims: "Improves blood sugar via GLP-1 pathway"
    ✓ Consistent
    
    Dosing section says: "100mg twice daily for diabetes"
    Efficacy says: "Tested at doses 100-200mg"
    ✓ Consistent
    
  OVERALL VALIDATION RESULT: FAIL (2 rules not met)
  
  ACTION OPTIONS:
  a) Auto-improve: Send back to Claude with failure details
  b) Manual review: Flag for human editor
  c) Mix: Auto-improve for Rule 3, flag others for review

Step 2d: Auto-Improvement (Optional)
  System sends failure details back to Claude:
  
  """
  Your Clinical Efficacy section didn't meet our quality rules:
  
  ISSUE 1: Claim 2 ("Improved glycemic control") lacks specificity
  FIX: Add effect size and statistics from source #3 (Holman et al., 2023)
  
  ISSUE 2: Claims 1 & 2 reference Level 3 evidence, but require Level 1A-1B
  FIX: Replace with Level 1A evidence (meta-analyses available)
  
  Rewrite now with these fixes:
  """
  
  Claude regenerates with improvements
  System re-validates
  If PASS: Proceed to next section
  If FAIL again: Escalate to human review

Step 2e: Logging & Tracking
  Record in database:
  {
    "monograph_id": "metformin_v2.1",
    "generation_date": "2024-06-08",
    "section": "clinical_efficacy",
    "skill_applied": "Evidence Quality for Clinical Efficacy",
    "skill_version": "1.1",
    "validation_result": "PASS_AFTER_IMPROVEMENT",
    "auto_improvements": 2,
    "final_compliance_score": 0.95,
    "timestamp": "2024-06-08T14:32:00Z"
  }


PHASE 3: FEEDBACK COLLECTION
═════════════════════════════════════════════════════════════════

After monograph delivered to HCP:

Step 3a: Feedback Survey
  HCP sees popup after reviewing monograph:
  
  """
  How would you rate the Clinical Efficacy section?
  - [ ] 5 stars - Excellent
  - [ ] 4 stars - Good
  - [ ] 3 stars - Acceptable
  - [ ] 2 stars - Needs improvement
  - [ ] 1 star - Poor
  
  Any specific feedback?
  [ Text field ]
  """

Step 3b: Feedback Collection Examples
  
  Feedback 1:
  Rating: 4 stars
  Comment: "Well-evidenced, but wish it included more recent 2024 studies"
  
  Feedback 2:
  Rating: 2 stars
  Comment: "Efficacy claims are too statistical; don't translate to practice"
  
  Feedback 3:
  Rating: 5 stars
  Comment: "Evidence-based, clinically relevant, well-organized"

Step 3c: Feedback Analysis
  System aggregates feedback across all monographs using this skill:
  
  "Evidence Quality for Clinical Efficacy" skill (v1.1):
  - Total monographs using this skill: 23
  - Feedback responses: 15 (65% response rate)
  - Average rating: 3.7 / 5.0
  
  Common themes in feedback:
  1. "Too statistical" (4 comments)
  2. "Missing recent studies" (3 comments)
  3. "Excellent evidence base" (5 positive comments)
  4. "Clinical relevance unclear" (2 comments)
  
  Issues identified:
  - Rule 2 (Numeric Specificity) may be overwhelming HCPs
  - Coverage of recent literature incomplete


PHASE 4: SKILL LEARNING & REFINEMENT
═════════════════════════════════════════════════════════════════

Step 4a: System-Generated Recommendations
  Medical Director receives report:
  
  """
  SKILL IMPROVEMENT RECOMMENDATIONS
  
  Skill: Evidence Quality for Clinical Efficacy v1.1
  Analysis Period: Last 30 days
  Feedback Score: 3.7/5.0 (target ≥4.0)
  
  ISSUE 1: "Too statistical, clinical translation unclear"
  → Recommendation: Add section "Clinical Interpretation of Numbers"
  → Suggested addition:
     "For each numeric claim, follow with 1-2 sentences explaining 
     clinical significance. Example: '1.2% HbA1c reduction is clinically 
     meaningful, equivalent to ~0.3 medication class addition.'"
  
  ISSUE 2: "Missing recent 2024 studies"
  → Recommendation: Include last 18 months (not 10 years)
  → Impact: Requires updated literature search strategy
  
  RECOMMENDATION SUMMARY:
  1. Minor edit: Add "Clinical Interpretation" rule (estimated effort: 1 hour)
  2. Configuration change: Update source recency filter (estimated effort: 30 min)
  
  Ready to implement? [YES] [NO] [REVIEW FIRST]
  """

Step 4b: Medical Director Review & Decision
  Medical Director reviews recommendation:
  - Agrees with Issue 1 (clinical translation unclear)
  - Disagrees with Issue 2 (10-year window is intentional for background context)
  
  Medical Director clicks: "IMPLEMENT Issue 1 only"
  
  Proposes new version v1.2:
  
  ```markdown
  # Evidence Quality for Clinical Efficacy (v1.2)
  
  [All previous rules from v1.1...]
  
  ### NEW RULE 5: Clinical Translation (ADDED in v1.2)
  For every numeric claim, include a sentence translating the statistic 
  to clinical practice:
  
  Example:
  "HbA1c reduction of 1.2% (95% CI: 1.0-1.4%, p<0.001, N=500, 12 weeks)
   is clinically meaningful, equivalent to the expected benefit of adding 
   one additional diabetes medication class."
   
  This rule was added based on HCP feedback indicating numbers need 
  clearer clinical context.
  ```

Step 4c: Version Control & Rollout
  New version stored:
  /skills/evidence_quality_for_clinical_efficacy/
  ├── v1.1/
  │   └── [previous version archived]
  └── v1.2/ [NEW]
      ├── source.md (updated NL file)
      ├── parsed_rules.json (including new Rule 5)
      ├── change_log.md
      │   Entry: "v1.1 → v1.2: Added Rule 5 (Clinical Translation)
      │           Reason: HCP feedback on statistical clarity
      │           Impact: Expected to improve comprehension"
      └── creation_metadata.json
  
  CURRENT pointer updated: v1.2
  
  All future monograph generations use v1.2

Step 4d: A/B Testing (Optional but Recommended)
  To validate that v1.2 is actually better:
  
  Generate same molecule (e.g., "Insulin Glargine") with:
  - Version A: Skill v1.1
  - Version B: Skill v1.2
  
  Request feedback from independent medical reviewers:
  - Which monograph is clearer on clinical significance?
  - Which would you recommend to HCPs?
  
  If v1.2 wins decisively: Roll out to all generations
  If results mixed: Keep both versions, allow choice per molecule type


PHASE 5: CONTINUOUS LEARNING CYCLE
═════════════════════════════════════════════════════════════════

Monthly Review Process:

Month 1:
- v1.0 deployed
- Feedback score: 3.2/5.0
- Issues: Evidence grades unclear, numeric claims need clinical context
- Recommendation: Revise evidence grading rules + add clinical translation
- Action: Create v1.1 plan

Month 2:
- v1.1 deployed (updated rules)
- Feedback score: 3.7/5.0 (improvement +0.5 points)
- Issues: Recent literature, clinical translation still imperfect
- Recommendation: Add Rule 5 (better clinical translation), update literature search
- Action: Create v1.2 plan

Month 3:
- v1.2 deployed (clinical translation rule added, search updated)
- Feedback score: 4.1/5.0 (improvement +0.4 points)
- Issues: Minimal (one request for drug interaction info)
- Recommendation: Performance plateau reached; consider archiving old versions
- Action: Monitor ongoing

Month 4:
- v1.2 continues in use
- Feedback score: 4.2/5.0 (slight continued improvement)
- Issues: Specific to certain molecule types (biologics harder than small molecules)
- Recommendation: Create separate skill for biological products
- Action: Plan v2.0 for biologics

LEARNING CURVE VISUALIZATION:
┌─────────────────────────────────────────────────────┐
│ Skill Maturity & HCP Feedback Score Over Time       │
├─────────────────────────────────────────────────────┤
│                                      ▲              │
│ Feedback   5.0 ───────────────────────┐             │
│ Score      4.2 ──────────────────────   ╲           │
│ (1-5)      4.1 ──────────────────              │
│            3.7 ──────                          │
│            3.2 ──                              │
│            2.0 ─                               │
│               │      │      │      │           │
│            v1.0    v1.1   v1.2    v2.0?       │
│               │      │      │      │           │
│             (Month 1)(M2)  (M3)  (Future)     │
│                                                 │
└─────────────────────────────────────────────────────┘
```

---

### 2.3 Skill File Parser: How NL Docs Become Executable Rules

**Raw Skill File Input (Markdown):**
```markdown
# Skill: Safety Section Data Presentation

## When to Apply
Every Safety & Tolerability section

## Rules

### Rule 1: Adverse Event Frequency Thresholds
Classify adverse events by frequency:
- Very Common (≥10%)
- Common (1-10%)
- Uncommon (0.1-1%)
- Rare (0.01-0.1%)
- Very Rare (<0.01%)

Present in descending frequency order within each category.

### Rule 2: Special Populations
Always include subsections:
- Contraindications (absolute)
- Drug-Drug Interactions (major only)
- Pregnancy & Lactation

### Rule 3: Severity Grading
Grade adverse events by severity:
- Grade 1: Mild, no intervention
- Grade 2: Moderate, intervention needed
- Grade 3: Severe, potentially life-threatening
- Grade 4: Life-threatening

Include Grade 3-4 events prominently; Grade 1 events can be listed.
```

**Parsing Process:**

```python
def parse_skill_file(markdown_text):
    """
    Convert natural language skill file to executable rules.
    """
    
    # Step 1: Extract metadata
    metadata = {
        "skill_name": extract_header(markdown_text),
        "when_to_apply": extract_section(markdown_text, "When to Apply"),
        "version": extract_version(markdown_text),
        "last_updated": extract_date(markdown_text)
    }
    
    # Step 2: Extract rules (each ### Rule is one rule)
    rules = []
    for rule_section in split_by_heading(markdown_text, level=3):
        rule_name = extract_title(rule_section)
        
        # Sub-parse: Extract conditions and actions
        rule_obj = {
            "name": rule_name,
            "conditions": extract_list_items(rule_section),
            "actions": extract_instructions(rule_section),
            "examples": extract_code_blocks(rule_section)
        }
        
        rules.append(rule_obj)
    
    # Step 3: Extract metrics (how to measure success)
    metrics = []
    if "Quality Metrics" in markdown_text:
        metrics_section = extract_section(markdown_text, "Quality Metrics")
        metrics = extract_list_items(metrics_section)
    
    # Step 4: Extract feedback triggers (when to revise this skill)
    feedback_triggers = []
    if "Feedback Triggers" in markdown_text:
        triggers_section = extract_section(markdown_text, "Feedback Triggers")
        for trigger in split_by_pattern(triggers_section, "IF:"):
            trigger_obj = {
                "condition": extract_between_tags(trigger, "IF:", "THEN:"),
                "action": extract_after_tag(trigger, "THEN:")
            }
            feedback_triggers.append(trigger_obj)
    
    # Step 5: Return structured skill object
    return SkillObject(
        metadata=metadata,
        rules=rules,
        metrics=metrics,
        feedback_triggers=feedback_triggers
    )


class SkillObject:
    """Executable skill representation."""
    
    def __init__(self, metadata, rules, metrics, feedback_triggers):
        self.metadata = metadata
        self.rules = rules
        self.metrics = metrics
        self.feedback_triggers = feedback_triggers
    
    def apply_to_generation(self, section_draft, generation_context):
        """
        Apply this skill to a generated monograph section.
        
        Returns:
        - validation_results: Pass/Fail + detailed feedback
        - improved_section: Auto-corrected section (if needed)
        """
        
        # For each rule, check compliance
        validation_results = {
            "overall_pass": True,
            "rule_results": [],
            "suggestions": []
        }
        
        for rule in self.rules:
            # Check if rule applies (e.g., "only for adverse events >5%")
            if self._rule_applies(rule, section_draft):
                compliance = self._check_rule_compliance(
                    rule, 
                    section_draft, 
                    generation_context
                )
                
                validation_results["rule_results"].append({
                    "rule_name": rule["name"],
                    "compliant": compliance["passed"],
                    "details": compliance["details"],
                    "suggestion": compliance.get("suggestion")
                })
                
                if not compliance["passed"]:
                    validation_results["overall_pass"] = False
        
        return validation_results
    
    def _check_rule_compliance(self, rule, section, context):
        """
        Evaluate if section follows a specific rule.
        
        This is where NL instructions get enforced.
        """
        
        rule_name = rule["name"]
        
        if rule_name == "Adverse Event Frequency Thresholds":
            # Check: Are AEs grouped by frequency category?
            ae_categories_present = [
                "Very Common" in section,
                "Common" in section,
                "Uncommon" in section,
                "Rare" in section,
                "Very Rare" in section
            ]
            
            is_compliant = all(ae_categories_present)
            
            return {
                "passed": is_compliant,
                "details": f"Found {sum(ae_categories_present)}/5 frequency categories",
                "suggestion": "Organize adverse events by frequency category" if not is_compliant else None
            }
        
        elif rule_name == "Special Populations":
            # Check: Are required subsections present?
            required_subsections = [
                "Contraindications",
                "Drug-Drug Interactions",
                "Pregnancy & Lactation"
            ]
            
            subsections_present = [
                subsection in section for subsection in required_subsections
            ]
            
            is_compliant = all(subsections_present)
            
            missing = [req for req, present in zip(required_subsections, subsections_present) if not present]
            
            return {
                "passed": is_compliant,
                "details": f"Found {sum(subsections_present)}/3 required subsections",
                "suggestion": f"Add missing sections: {', '.join(missing)}" if missing else None
            }
        
        elif rule_name == "Severity Grading":
            # Check: Are Grade 3-4 events prominent (appear near top)?
            grade_3_4_position = self._find_severity_position(section, ["Grade 3", "Grade 4"])
            grade_1_2_position = self._find_severity_position(section, ["Grade 1", "Grade 2"])
            
            is_compliant = grade_3_4_position < grade_1_2_position if grade_3_4_position else True
            
            return {
                "passed": is_compliant,
                "details": f"Grade 3-4 events at position {grade_3_4_position}, Grade 1-2 at {grade_1_2_position}",
                "suggestion": "Move Grade 3-4 events to earlier in section" if not is_compliant else None
            }
        
        # Add more rules as needed...
        
        return {"passed": True, "details": "Rule not yet implemented", "suggestion": None}
```

---

## PART 3: INTEGRATION WORKFLOW - SOP + SKILLS + AI

### 3.1 End-to-End Generation with SOP + Skills

```
USER INPUT: "Generate monograph for Metformin"
            │
            ▼
┌─────────────────────────────────────────┐
│ 1. LOAD SOP TEMPLATE                    │
├─────────────────────────────────────────┤
│ Pharmacology                            │
│ ├─ 500-800 words                        │
│ ├─ Required: Molecular + Phys. MoA      │
│ ├─ Min 5 sources                        │
│ └─ Skill: "Evidence Quality"            │
│                                         │
│ Pharmacokinetics                        │
│ ├─ 1200 words max                       │
│ ├─ Required: ADME + Special Pops        │
│ ├─ Special Pops: Renal, Hepatic         │
│ └─ Skill: "PK Clarity"                  │
│                                         │
│ Clinical Efficacy                       │
│ ├─ 800-1200 words                       │
│ ├─ Required: All FDA indications        │
│ ├─ Evidence levels for all claims       │
│ └─ Skill: "Evidence Quality"            │
│                                         │
│ Safety                                  │
│ ├─ 600-800 words                        │
│ ├─ Required: AE freq classes, DDI       │
│ ├─ Contraindications & Drug-Drug        │
│ └─ Skill: "Safety Completeness"         │
│                                         │
│ [... other sections ...]                │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 2. SCRAPE SOURCES                       │
├─────────────────────────────────────────┤
│ Search: "Metformin pharmacology"        │
│ Results: 247 PubMed articles            │
│ ├─ Filter: >0.7 relevance, English      │
│ ├─ Top 50 selected                      │
│ └─ Organize by section                  │
│                                         │
│ Search: "Metformin adverse events"      │
│ Results: FDA FAERS data + EMA           │
│ ├─ Parse AE frequencies                 │
│ └─ Map to severity grades               │
│                                         │
│ Search: "Metformin clinical trials"     │
│ Results: 12 RCTs, 34 observational      │
│ ├─ Extract efficacy data                │
│ ├─ Calculate effect sizes               │
│ └─ Grade evidence level                 │
│                                         │
│ Total: 315 sources collected            │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 3. GENERATE SECTION: PHARMACOLOGY       │
├─────────────────────────────────────────┤
│ PROMPT TO CLAUDE:                       │
│                                         │
│ "Generate Pharmacology section for      │
│  Metformin following these constraints: │
│                                         │
│  SOP Requirements:                      │
│  - 500-800 words                        │
│  - Must explain mechanism at 2 levels:  │
│    * Molecular (AMPK inhibition)        │
│    * Physiological (glucose uptake)     │
│  - Minimum 5 peer-reviewed sources      │
│  - Target audience: PGY-2 level         │
│                                         │
│  Skill Rules ('Evidence Quality' v1.2): │
│  - Every claim requires evidence grade  │
│  - If similar drugs exist, compare them │
│  - Include effect strength (binding     │
│    constants if available)              │
│                                         │
│  Available Sources: [15 papers]         │
│                                         │
│  Generate now:"                         │
│                                         │
│ CLAUDE OUTPUT:                          │
│ "Metformin's mechanism of action        │
│  involves activation of AMP-kinase      │
│  (AMPK), a key cellular energy sensor   │
│  [Grade 1A: Multiple RCTs and           │
│  biochemical studies, binding IC50      │
│  = 150 μM]. This molecular             │
│  interaction triggers downstream...     │
│  [continues with full section]"         │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 4. VALIDATE AGAINST SOP + SKILLS        │
├─────────────────────────────────────────┤
│ Validation Checks:                      │
│                                         │
│ SOP Check:                              │
│ ✓ Word count: 650/800 [in range]       │
│ ✓ 2-level mechanism: Molecular +        │
│   Physiological [present]               │
│ ✓ Source count: 6/5 minimum [adequate]  │
│ ✓ Readability: Grade 13 [target 12-14]  │
│                                         │
│ Skill Check ('Evidence Quality'):       │
│ ✓ All claims evidence-graded [present]  │
│ ✓ Comparative context vs. Sulfonylurea  │
│   [present: "Unlike sulfonylureas..."]  │
│ ✓ Binding constants specified           │
│   [present: IC50 = 150 μM]              │
│                                         │
│ Overall: PASS                           │
│ Compliance Score: 0.96/1.0              │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 5. REPEAT FOR ALL SECTIONS              │
├─────────────────────────────────────────┤
│ Generate & Validate:                    │
│ ✓ Pharmacokinetics (PASS, 0.94)        │
│ ✓ Clinical Efficacy (PASS, 0.98)       │
│ ⚠ Safety (FLAG, 0.85)                  │
│   Reason: Missing pregnancy category    │
│   Skill: "Safety Completeness" flagged  │
│   Action: Auto-improve...               │
│   [Claude rewrites Safety section]      │
│ ✓ Safety [re-validation] (PASS, 0.96)  │
│ ✓ Dosing (PASS, 0.99)                  │
│ [... other sections ...]                │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 6. ASSEMBLE FINAL MONOGRAPH             │
├─────────────────────────────────────────┤
│ Structure:                              │
│ - Table of Contents                     │
│ - Executive Summary                     │
│ - All sections (in SOP order)           │
│ - References (formatted per SOP)        │
│ - Appendices (clinical trial tables)    │
│ - Page numbers, headers, footers        │
│                                         │
│ Format: PDF (professional layout)       │
│ Compliance Report Attached:             │
│ "Monograph generated [DATE]             │
│  All sections PASS SOP requirements     │
│  All sections PASS skill requirements   │
│  Overall Compliance: 96%                │
│  Ready for HCP distribution"            │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 7. OPTIONAL: MEDICAL REVIEW             │
├─────────────────────────────────────────┤
│ Flag for Review?                        │
│ └─ Compliance Score >95%: NO            │
│ └─ Can proceed directly to HCP          │
│                                         │
│ If score <95% or High-Risk Drug:        │
│ └─ Route to Medical Director            │
│ └─ They review, approve, or request     │
│    revisions                            │
│ └─ Once approved: Can proceed           │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 8. DELIVERY TO HCP                      │
├─────────────────────────────────────────┤
│ HCP clicks: "Download Monograph"        │
│ └─ Receives PDF: "Metformin_v2.1.pdf"   │
│ └─ Professional, evidence-based,        │
│    SOP-compliant document               │
│ └─ Ready for clinical use               │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ 9. FEEDBACK COLLECTION & LEARNING       │
├─────────────────────────────────────────┤
│ HCP Rating: 4.5 / 5.0 stars            │
│ Comment: "Excellent evidence base,      │
│  but more clinical context on dosing    │
│  would help"                            │
│                                         │
│ System Log:                             │
│ - Feedback recorded                     │
│ - Linked to skill: "Evidence Quality"   │
│ - Issue category: "Clinical context"    │
│                                         │
│ Monthly Analysis:                       │
│ - 40 monographs generated with skills   │
│ - Avg rating: 4.2 / 5.0                │
│ - Common feedback: "Dosing context      │
│   needs clinical clarity"               │
│ - Recommendation: Update Skill Rule     │
│ - Create v1.3 with dosing context rule  │
│                                         │
│ Result: Continuous improvement cycle   │
│ v1.0 → v1.1 → v1.2 → v1.3 ...          │
└─────────────────────────────────────────┘
```

---

## PART 4: PRACTICAL IMPLEMENTATION - YOUR IMMEDIATE NEXT STEPS

### 4.1 Week 1 Actions: Audit Your Current SOPs

**Task 1: Export Your SOP Templates**
```
Action: Send me 1-2 example SOP templates (anonymized if needed)
Format: Word, PDF, or text
What I need:
  - Structure (sections, subsections)
  - Content requirements (word counts, mandatory elements)
  - Quality standards (evidence levels, tone, compliance rules)
  - Approval workflows (review steps before distribution)

Timeline: By end of Week 1
```

**Task 2: Identify Current Pain Points**
```
Questions to Answer:
1. Currently, monograph generation takes _____ weeks (you said 4-8)
2. The biggest bottlenecks are:
   - Literature review ____%
   - Compliance checking ____%
   - Medical review ____%
   - Formatting/assembly ____%
3. How many molecules do you generate monographs for per year?
4. Who currently reviews/approves monographs (job title)?
5. Do you have any automated checks in place? (Y/N, describe)

Timeline: By end of Week 1
```

**Task 3: Define Initial Skill Files (Content Planning)**
```
Brainstorm: What are your top 3 quality issues in monographs?

Example answers:
1. "Claims lack proper evidence grading"
   → Skill File: "Evidence Grading Standards"
2. "Safety section often incomplete (missing DDI info)"
   → Skill File: "Safety Completeness Checklist"
3. "Dosing tables inconsistent with efficacy text"
   → Skill File: "Dosing-Efficacy Alignment"

Your top 3: [?]

Timeline: By end of Week 1
```

---

### 4.2 Week 2 Actions: Design Skill Files

**Task 1: Write 1st Skill File (Template)**
```
Using the format from Section 2.1 "Good Skill File" template:
Write a natural language skill file for ONE of your top pain points

Format:
  # Skill: [Name]
  
  ## When to Apply
  [Which sections/scenarios]
  
  ## The Problem This Solves
  [Current issue your team faces]
  
  ## Rules
  ### Rule 1: [specific actionable rule]
  [examples of good/bad]
  
  ### Rule 2: [next rule]
  [examples]
  
  ## Quality Metrics
  [How to measure if rule is working]
  
  ## Feedback Triggers
  [When/how to update this skill]

Effort: ~4-8 hours for one comprehensive skill file
Timeline: By end of Week 2, deliver 1 skill file (Medical Director to write)
```

**Task 2: Map SOP to Structured Rules**
```
For your SOP template (from Week 1 Task 1):
- Extract 5-10 key rules
- Convert each to structured rule objects
- Example output:
  {
    "rule_id": "ph_01",
    "rule_name": "Pharmacology Mechanism Depth",
    "applies_to": "Pharmacology section",
    "requirement": "Explain at 2 levels: molecular AND physiological",
    "validation": "Both present? YES/NO",
    "example_pass": "...",
    "example_fail": "..."
  }

Timeline: By end of Week 2, deliver SOP mapping document
```

---

### 4.3 Week 3: Architecture Planning Session

**Prepare for meeting with software architect:**

```
Bring to session:
1. Digitized SOP templates (from Week 1)
2. First skill file draft (from Week 2)
3. SOP mapping document (from Week 2)
4. List of current data sources you use:
   - PubMed? Frequency?
   - FDA databases? Which ones?
   - EMA? ClinicalTrials.gov?
   - Internal databases?
5. Current monograph approval workflow:
   - Who reviews? (roles)
   - How long does it take?
   - What's the decision criteria?
   - How many iterations/revisions typical?
6. Team composition:
   - How many people involved in monograph creation?
   - What are their roles?
   - Availability for testing/feedback?

Agenda (4-hour session):
  1. Review current state & pain points (30 min)
  2. Design LLM integration architecture (60 min)
  3. Design SOP rule engine (60 min)
  4. Design skill file learning system (60 min)
  5. Database & API design (30 min)
  6. Timeline & resource estimation (20 min)
```

---

## SUMMARY: What You Now Have

**Documents Created Today:**
1. ✅ **PRD (Product Requirements Document)** - Complete 13-section specification
2. ✅ **Technical Blueprint: SOP Integration & Skill Learning** - This document

**Your Action Items (Next 3 Weeks):**
- Week 1: Audit SOPs, identify pain points, plan initial skills
- Week 2: Write first skill file, map SOP to executable rules
- Week 3: Architecture planning meeting with engineering team

**By End of Week 3, You'll Have:**
- Technical blueprint finalized
- Estimated development timeline
- Resource requirements identified
- Risk assessment & mitigation plan
- MVP definition (scope & timeline)

---

## APPENDIX: Glossary of Key Concepts

| Term | Definition | Example |
|------|-----------|---------|
| **SOP Rule** | Executable constraint from your SOP | "Pharmacology section must be 500-800 words" |
| **Skill File** | Natural language instruction document that encodes quality standards | "Evidence Quality for Clinical Efficacy" |
| **Skill Parser** | System that converts NL skill file → executable rules | Reads "Rule 1: Evidence Grading..." → Creates validation function |
| **Validation** | Check if generated content meets SOP + skill requirements | "Is word count between 500-800?" |
| **Auto-Improvement** | System re-generates section to fix validation failures | Claude rewrites section to meet word count |
| **Feedback Loop** | HCP provides rating/comments → system learns → improves future generations | "Too technical" feedback → Update skill file → Better output |
| **Evidence Grading** | Ranking studies by quality (Level 1A = RCT, Level 3 = case report) | Level 1A evidence is strongest |
| **Monograph Compliance Score** | Percentage of SOP + skill requirements met by generated document | 96% compliance = excellent |

---

**Document Status:** COMPLETE & READY FOR IMPLEMENTATION  
**Next Meeting:** Schedule 4-hour architecture planning session (Week 3)  
**Questions?** Contact Medical Director, Head of Medical Services, or Development Lead
