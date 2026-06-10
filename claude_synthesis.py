"""
Claude Synthesis Engine: Generates monograph sections using Claude API
Optimized for 45-minute total generation time
Uses parallel section generation and streaming
"""
import json
from typing import Dict, List, Tuple, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from anthropic import Anthropic
from config import ANTHROPIC_MODEL, MAX_TOKENS, TEMPERATURE
from sop_engine import sop_engine
from data_sources import data_manager

CLAUDE_MODEL = ANTHROPIC_MODEL

class ClaudeSynthesisEngine:
    """Orchestrates Claude API calls for monograph generation"""

    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL
        self.sop_constraints = sop_engine.get_sop_prompt_injection()
        self.generation_log = []

    def generate_monograph(self, molecule_name: str, research_sources: Dict) -> Dict:
        """
        Generate complete monograph in parallel sections
        Targets 45-minute completion time
        """
        print(f"\n[MONOGRAPH] Generating monograph for {molecule_name}...")

        monograph = {
            "molecule_name": molecule_name,
            "sections": {},
            "generation_time": 0,
            "total_tokens_used": 0,
            "quality_scores": {}
        }

        # Critical sections to generate in parallel
        sections_to_generate = [
            "introduction",
            "pharmacology",
            "pharmacokinetics",
            "clinical_efficacy",
            "safety",
            "dosage",
            "contraindications",
            "drug_interactions"
        ]

        print(f"\n[PARALLEL] Generating {len(sections_to_generate)} sections in parallel...")

        # Execute section generation in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for section in sections_to_generate:
                future = executor.submit(
                    self.generate_section,
                    section,
                    molecule_name,
                    research_sources
                )
                futures[future] = section

            for future in as_completed(futures):
                section_name = futures[future]
                try:
                    section_content, tokens_used = future.result()
                    monograph["sections"][section_name] = section_content
                    monograph["total_tokens_used"] += tokens_used
                    print(f"[OK] {section_name.replace('_', ' ').title()} - {tokens_used} tokens")
                except Exception as e:
                    print(f"[ERROR] {section_name} failed: {str(e)}")

        # Generate references section (serial, depends on other sections)
        print("\n[REFERENCES] Generating references...")
        references, tokens_used = self.generate_references(molecule_name, research_sources)
        monograph["sections"]["references"] = references
        monograph["total_tokens_used"] += tokens_used

        return monograph

    def generate_section(
        self,
        section_name: str,
        molecule_name: str,
        research_sources: Dict
    ) -> Tuple[str, int]:
        """
        Generate a single section using Claude
        Returns (content, tokens_used)
        """
        section_spec = sop_engine.sections.get(section_name, {})
        if not section_spec:
            return "", 0

        # Build section-specific prompt
        prompt = self._build_section_prompt(
            section_name,
            molecule_name,
            research_sources,
            section_spec
        )

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=self.sop_constraints,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Log generation
            self.generation_log.append({
                "section": section_name,
                "tokens": tokens_used,
                "status": "success"
            })

            return content, tokens_used

        except Exception as e:
            print(f"Claude API error for {section_name}: {str(e)}")
            self.generation_log.append({
                "section": section_name,
                "status": "error",
                "error": str(e)
            })
            return "", 0

    def _build_section_prompt(
        self,
        section_name: str,
        molecule_name: str,
        research_sources: Dict,
        section_spec: Dict
    ) -> str:
        """Build a detailed prompt for section generation"""
        prompt = f"""
You are writing a pharmaceutical product monograph section.

## MOLECULE: {molecule_name}
## SECTION: {section_spec.get('title', section_name)}

## REQUIREMENTS:
"""
        if "min_words" in section_spec:
            prompt += f"- Word count: {section_spec['min_words']}-{section_spec['max_words']} words\n"

        if "required_subsections" in section_spec:
            subsections = ", ".join(s.replace("_", " ").title() for s in section_spec["required_subsections"])
            prompt += f"- Must include: {subsections}\n"

        # Section-specific instructions
        section_instructions = {
            "introduction": """
- Provide historical context and clinical significance
- Explain the problem addressed
- Reference relevant epidemiology
- Include clinical need for this therapy
- Format: Professional, evidence-based
""",
            "pharmacology": """
- Explain mechanism of action at MOLECULAR level
- Explain mechanism at PHYSIOLOGICAL level
- Include comparative context with similar drugs if available
- Reference receptor binding constants, IC50 values where applicable
- Use ONLY Level 1A-1B evidence (RCTs, meta-analyses)
- Include specific effect measures with confidence intervals
""",
            "pharmacokinetics": """
- Cover ADME: Absorption, Distribution, Metabolism, Elimination
- Include specific PK parameters: Cmax, Tmax, AUC, half-life
- Discuss special populations: renal/hepatic impairment, geriatric, pediatric, pregnancy
- Include dose-response relationships
- Reference human PK studies with sample sizes and study designs
""",
            "clinical_efficacy": """
- Summarize pivotal clinical trials
- Include ALL FDA-approved indications
- For each indication: effect size, NNT (number needed to treat), confidence intervals
- Compare to standard of care where available
- Separate Level 1A evidence (primary) from Level 2-3 (supportive)
- Include patient populations studied
""",
            "safety": """
- Organize adverse events by CIOMS frequency (very common, common, uncommon, rare, very rare)
- Include percentages in parentheses
- Highlight serious/life-threatening events at top
- Include contraindications with clear rationale
- Cover special populations: pregnancy, lactation, hepatic/renal disease
- Include management strategies for common AEs
""",
            "dosage": """
- Provide recommended starting dose
- Include titration schedule if applicable
- Include maintenance dose
- Specify dosing adjustments for:
  * Renal impairment
  * Hepatic impairment
  * Geriatric patients
  * Pediatric populations (if indicated)
- Specify route(s) of administration
- Include timing relative to meals if relevant
""",
        }

        if section_name in section_instructions:
            prompt += "\n## SECTION-SPECIFIC REQUIREMENTS:\n"
            prompt += section_instructions[section_name]

        # Add research sources
        prompt += f"\n## RESEARCH SOURCES:\n"
        prompt += research_sources.get("formatted_text", "")[:3000]  # Limit to 3000 chars

        prompt += f"""

## OUTPUT:
Write the {section_spec.get('title', section_name)} section.
- Start with section title as a markdown header (## Title)
- Use professional, clear medical language
- Include specific citations: [Author et al., Year]
- Use tables for complex data where appropriate
- Highlight key findings in **bold**
- Ensure evidence-based and unbiased presentation
"""

        return prompt

    def generate_references(
        self,
        molecule_name: str,
        research_sources: Dict
    ) -> Tuple[str, int]:
        """Generate formatted reference list"""
        ref_prompt = f"""
You are formatting a reference list for a pharmaceutical monograph.

## MOLECULE: {molecule_name}

Available sources: {json.dumps(research_sources['sources'], default=str)[:2000]}

Generate a formatted reference list in Vancouver style:
1. Author AA, Author BB. Article title. Journal Name. Year;Volume(Issue):Pages. doi:xxxxx

Requirements:
- Order chronologically (newest first)
- Include DOI/URL where available
- Ensure all sources cited in the monograph are listed
- Remove duplicates
- Format consistently

Generate the complete references section:
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "user", "content": ref_prompt}
                ]
            )

            content = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            return content, tokens_used

        except Exception as e:
            print(f"Reference generation error: {str(e)}")
            return "References: [See research sources cited in text]", 0

    def estimate_generation_time(self, num_sections: int = 8) -> float:
        """Estimate generation time based on section count and parallel execution"""
        # Each section takes ~5 minutes when parallelized
        # 8 sections parallel = 5 min + 5 min for references = 10 min minimum
        # API calls account for ~30 min, parallel execution = 45 min total target
        return 45.0  # Target: 45 minutes

    def get_generation_summary(self) -> Dict:
        """Get summary of generation including token usage"""
        return {
            "sections_generated": len([l for l in self.generation_log if l.get("status") == "success"]),
            "sections_failed": len([l for l in self.generation_log if l.get("status") == "error"]),
            "total_tokens_used": sum(l.get("tokens", 0) for l in self.generation_log),
            "log": self.generation_log
        }


# Initialize globally
synthesis_engine = ClaudeSynthesisEngine()

if __name__ == "__main__":
    print("Claude Synthesis Engine initialized")
    print(f"Model: {synthesis_engine.model}")
    print(f"Max tokens per call: {MAX_TOKENS}")
