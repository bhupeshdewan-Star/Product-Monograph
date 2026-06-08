"""
Executive Summary Generator
Creates concise HCP-focused executive summaries highlighting key strengths
"""
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

class ExecutiveSummaryGenerator:
    """Generates professional executive summaries for healthcare professionals"""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def generate_executive_summary(self, molecule_name: str, sources: dict, hcp_specialty: str = "General Practitioner") -> str:
        """
        Generate executive summary tailored to HCP specialty

        Args:
            molecule_name: Drug name
            sources: Research sources dict
            hcp_specialty: Target HCP type (Cardiologist, Endocrinologist, etc.)
        """

        # Prepare source summary
        article_count = sources.get('total_articles', 0)
        fda_articles = len(sources.get('sources', {}).get('fda', []))
        pubmed_articles = len(sources.get('sources', {}).get('pubmed', []))

        prompt = f"""Generate a professional EXECUTIVE SUMMARY for {molecule_name} targeted to a {hcp_specialty}.

DRUG: {molecule_name}
TARGET SPECIALTY: {hcp_specialty}
EVIDENCE BASE: {pubmed_articles} PubMed articles, {fda_articles} FDA approvals, {article_count} total sources

Create a 3-4 paragraph executive summary with:

## EXECUTIVE SUMMARY: {molecule_name.upper()}

### Clinical Overview
Brief description of what {molecule_name} is and its primary mechanism.

### Key Strengths for {hcp_specialty}s
Highlight 3-4 main benefits specific to this HCP specialty:
- For Cardiologists: Cardiovascular benefits, heart failure use
- For Endocrinologists: Metabolic control, diabetes management
- For Rheumatologists: Inflammation control, joint protection
- For Neurologists: CNS effects, seizure control
- For General Practitioners: Safety, ease of use, cost-effectiveness

### Evidence Highlights
- Primary indication(s) supported by strongest evidence (cite evidence levels)
- Key clinical trial outcomes with effect sizes
- Safety profile summary
- Special populations or use cases

### Clinical Pearls for Practice
3-4 bullet points of practical guidance for this specialty

### Position in Treatment Paradigm
- First-line vs second-line therapy
- When to prefer over alternatives
- Contraindications in this specialty

Format as clear, scannable bullet points. Use professional medical language.
Include specific effect sizes and confidence intervals where known.
Avoid marketing language - focus on clinical evidence."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating executive summary: {str(e)}"

    def generate_hcp_specialty_summary(self, molecule_name: str, specialty: str) -> str:
        """
        Generate specialty-specific clinical pearls
        """

        specialty_prompts = {
            "Cardiologist": "Focus on cardiovascular effects, heart failure benefits, arrhythmia effects, and blood pressure management",
            "Endocrinologist": "Focus on metabolic effects, glucose control, lipid management, and endocrine system impacts",
            "Rheumatologist": "Focus on anti-inflammatory effects, joint protection, autoimmune modulation, and bone health",
            "Neurologist": "Focus on neurological effects, seizure management, neuroprotection, and CNS side effects",
            "Psychiatrist": "Focus on psychotropic effects, mood disorders, cognitive effects, and psychiatric safety",
            "Nephrologist": "Focus on renal function, kidney protection, electrolyte effects, and dose adjustments",
            "Pulmonologist": "Focus on respiratory effects, asthma/COPD impacts, and pulmonary safety",
            "General Practitioner": "Focus on safety in primary care, ease of use, monitoring requirements, and cost-effectiveness",
        }

        specialty_context = specialty_prompts.get(specialty, f"Focus on clinical use in {specialty} practice")

        prompt = f"""Create KEY CLINICAL PEARLS for {specialty}s prescribing {molecule_name}:

CONTEXT: {specialty_context}

Provide in this format:

## KEY CLINICAL PEARLS FOR {specialty.upper()}S

### When to Prescribe
- Ideal patient profile for this specialty
- Preferred indications
- Patient selection criteria

### Monitoring Required
- Lab tests needed
- Clinical assessment frequency
- Safety monitoring parameters specific to this specialty

### Drug Interactions of Concern (in {specialty} context)
- Key interactions with commonly co-prescribed drugs
- Specialty-specific concerns

### Special Populations
- Elderly patients
- Renal/hepatic impairment
- Pregnancy/lactation
- Pediatric (if applicable)

### Red Flags & Contraindications
- Absolute contraindications
- Cautions in this specialty
- When to consult other specialists

### Dosing Tips
- Standard dosing for this specialty
- Dose adjustments needed
- When to escalate/de-escalate

Use bullet points. Be concise and practical."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating specialty pearls: {str(e)}"

    def generate_quick_reference_box(self, molecule_name: str) -> str:
        """
        Generate a quick reference box for busy HCPs
        One-page summary of essentials
        """

        prompt = f"""Create a QUICK REFERENCE BOX for {molecule_name} on a single page.

Format as a structured reference card for busy clinicians:

## {molecule_name.upper()} - QUICK REFERENCE

**DRUG CLASS:** [Class]
**MECHANISM:** [One-line mechanism]
**INDICATION:** [Primary indication in India]
**DOSING:** [Standard dose]
**FREQUENCY:** [Dosing interval]

### QUICK FACTS
- Key benefit #1
- Key benefit #2
- Key side effect to watch
- Most common drug interaction

### START/STOP CHECKLIST
Before prescribing, verify:
- □ Indication appropriate
- □ No contraindications
- □ No major drug interactions
- □ Renal/hepatic function adequate
- □ Patient education provided

### MONITORING (First 3 months)
- Week 1-2: [What to monitor]
- Week 4: [Lab/clinical check]
- Week 12: [Efficacy assessment]

### RED FLAGS
[WARN]️ [Stop drug if...]
[WARN]️ [Reduce dose if...]
[WARN]️ [Seek specialist if...]

### INDIAN PRICING (Approximate)
Generic: ₹X-₹Y per dose
Branded: ₹X-₹Y per dose

### KEY REFERENCES
[Top 3 reference citations]

Make it scannable, practical, and concise."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating quick reference: {str(e)}"


# Initialize globally
executive_summary_generator = ExecutiveSummaryGenerator()
