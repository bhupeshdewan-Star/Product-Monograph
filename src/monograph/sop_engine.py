"""
SOP Engine: Template structure, validation, and compliance checking
Ensures 100% adherence to your Standard Operating Procedures
"""
from typing import Dict, List, Tuple
from config import SOP_SECTIONS, EVIDENCE_LEVELS, AE_FREQUENCY
import json
import re


TRACEABILITY_MARKER_RE = re.compile(r"(PMID:\d+|FDA:[^\]\n]+|NCT\d{8,}|EMA:[^\]\n]+)")

class SOPEngine:
    """Manages SOP template, validation, and compliance"""

    def __init__(self):
        self.sections = SOP_SECTIONS
        self.evidence_levels = EVIDENCE_LEVELS
        self.ae_frequency = AE_FREQUENCY
        self.validation_results = {}

    def get_template_structure(self) -> Dict:
        """Returns the complete SOP template structure"""
        return {
            "monograph_structure": list(self.sections.keys()),
            "sections": self.sections,
            "mandatory_sections": [k for k, v in self.sections.items() if v.get("priority") == "critical"],
            "evidence_standards": self.evidence_levels,
            "adverse_event_standards": self.ae_frequency
        }

    def validate_section(self, section_name: str, content: str) -> Tuple[bool, Dict]:
        """
        Validate a generated section against SOP requirements
        Returns (is_compliant, validation_details)
        """
        if section_name not in self.sections:
            return False, {"error": f"Unknown section: {section_name}"}

        section_spec = self.sections[section_name]
        validation = {
            "section": section_name,
            "checks": {},
            "compliance_score": 0.0,
            "issues": []
        }

        # Word count check (if applicable)
        if "min_words" in section_spec:
            word_count = len(content.split())
            min_words = section_spec["min_words"]
            max_words = section_spec["max_words"]

            if word_count < min_words:
                validation["issues"].append(
                    f"Word count ({word_count}) below minimum ({min_words})"
                )
                validation["checks"]["word_count"] = False
            elif word_count > max_words:
                validation["issues"].append(
                    f"Word count ({word_count}) exceeds maximum ({max_words})"
                )
                validation["checks"]["word_count"] = False
            else:
                validation["checks"]["word_count"] = True

        # Required subsections check (for critical sections)
        if "required_subsections" in section_spec:
            required = section_spec["required_subsections"]
            content_lower = content.lower()

            for subsection in required:
                subsection_keyword = subsection.replace("_", " ")
                if subsection_keyword.lower() in content_lower:
                    validation["checks"][f"subsection_{subsection}"] = True
                else:
                    validation["issues"].append(f"Missing subsection: {subsection}")
                    validation["checks"][f"subsection_{subsection}"] = False

        # Evidence quality check (for clinical sections)
        if section_name in ["clinical_efficacy", "safety"]:
            validation.update(self._check_evidence_quality(content))

        # Source traceability check (for evidence-backed sections)
        if section_name in [
            "introduction",
            "rationale",
            "pharmacology",
            "pharmacokinetics",
            "clinical_efficacy",
            "safety",
            "dosage",
            "contraindications",
            "drug_interactions",
        ]:
            validation.update(self._check_source_traceability(content))

        # Adverse event format check (for safety section)
        if section_name == "safety":
            validation.update(self._check_ae_format(content))

        # Calculate compliance score
        if validation["checks"]:
            passed = sum(1 for v in validation["checks"].values() if v)
            total = len(validation["checks"])
            validation["compliance_score"] = (passed / total) * 100

        # Determine if compliant (all critical checks must pass)
        is_compliant = len(validation["issues"]) == 0
        validation["status"] = "PASS" if is_compliant else "FAIL"

        return is_compliant, validation

    def _check_evidence_quality(self, content: str) -> Dict:
        """Check for proper evidence grading in clinical sections"""
        checks = {}
        issues = []

        evidence_markers = ["level 1a", "level 1b", "level 2", "level 3", "level 4",
                          "rct", "meta-analysis", "randomized controlled trial"]

        found_evidence = any(marker in content.lower() for marker in evidence_markers)

        if not found_evidence:
            issues.append("No evidence grading found. Include Level 1A-1B evidence.")
            checks["evidence_grading"] = False
        else:
            checks["evidence_grading"] = True

        # Check for numeric findings with confidence intervals
        if "(" in content and "%" in content:
            checks["numeric_specificity"] = True
        else:
            issues.append("Include specific effect sizes with confidence intervals")
            checks["numeric_specificity"] = False

        return {
            "checks": checks,
            "issues": issues
        }

    def _check_source_traceability(self, content: str) -> Dict:
        """Ensure scientific claims include evidence source markers."""
        checks = {}
        issues = []

        scientific_sentences = 0
        cited_sentences = 0
        for sentence in re.split(r"(?<=[.!?])\s+", content or ""):
            sentence = sentence.strip()
            if not sentence or sentence.startswith("#"):
                continue
            if sentence.startswith("- "):
                sentence = sentence[2:].strip()
            if not sentence:
                continue
            if self._looks_scientific(sentence):
                scientific_sentences += 1
                if TRACEABILITY_MARKER_RE.search(sentence):
                    cited_sentences += 1

        if scientific_sentences == 0:
            checks["source_traceability"] = True
            return {"checks": checks, "issues": issues}

        if cited_sentences < scientific_sentences:
            issues.append("Scientific claims must include source identifiers (PMID, FDA section, or NCT).")
            checks["source_traceability"] = False
        else:
            checks["source_traceability"] = True

        return {
            "checks": checks,
            "issues": issues
        }

    @staticmethod
    def _looks_scientific(sentence: str) -> bool:
        lowered = sentence.lower()
        if any(term in lowered for term in (
            "trial",
            "study",
            "evidence",
            "efficacy",
            "safety",
            "dose",
            "dosage",
            "contraindication",
            "interaction",
            "pharmac",
            "fracture",
            "glyc",
            "pain",
            "renal",
            "hepatic",
            "calcium",
            "bioavailability",
            "randomized",
            "meta-analysis",
            "confidence",
            "adverse",
            "monitoring",
        )):
            return True
        return bool(re.search(r"\d", sentence))

    def _check_ae_format(self, content: str) -> Dict:
        """Check for proper adverse event frequency classification (CIOMS)"""
        checks = {}
        issues = []

        cioms_terms = ["very common", "common", "uncommon", "rare", "very rare"]
        found_cioms = any(term in content.lower() for term in cioms_terms)

        if not found_cioms:
            issues.append("Use CIOMS frequency classification for adverse events")
            checks["cioms_classification"] = False
        else:
            checks["cioms_classification"] = True

        # Check for contraindications section
        if "contraindication" in content.lower():
            checks["contraindications"] = True
        else:
            issues.append("Include contraindications section")
            checks["contraindications"] = False

        # Check for drug interactions
        if "interaction" in content.lower() or "concomitant" in content.lower():
            checks["drug_interactions"] = True
        else:
            issues.append("Include drug interactions information")
            checks["drug_interactions"] = False

        return {
            "checks": checks,
            "issues": issues
        }

    def validate_complete_monograph(self, sections: Dict[str, str]) -> Dict:
        """Validate entire monograph against SOP requirements"""
        validation_report = {
            "molecule": sections.get("molecule_name", "Unknown"),
            "sections_validated": 0,
            "sections_compliant": 0,
            "overall_compliance_score": 0.0,
            "section_details": {},
            "mandatory_sections_missing": [],
            "critical_issues": []
        }

        total_compliance = 0
        section_scores = []

        # Validate each section
        for section_name in self.sections.keys():
            if section_name in sections:
                is_compliant, validation = self.validate_section(
                    section_name,
                    sections[section_name]
                )
                validation_report["section_details"][section_name] = validation
                validation_report["sections_validated"] += 1

                if is_compliant:
                    validation_report["sections_compliant"] += 1

                section_scores.append(validation["compliance_score"])

                # Track critical issues
                if self.sections[section_name].get("priority") == "critical" and not is_compliant:
                    validation_report["critical_issues"].extend(validation["issues"])

            else:
                # Check if mandatory
                if self.sections[section_name].get("priority") == "critical":
                    validation_report["mandatory_sections_missing"].append(section_name)

        traceability_appendix = sections.get("traceability_appendix", "") or sections.get("evidence_traceability_appendix", "")
        has_scientific_sections = any(
            section in sections
            for section in ("introduction", "pharmacology", "pharmacokinetics", "clinical_efficacy", "safety", "dosage", "contraindications", "drug_interactions")
        )
        if has_scientific_sections and not traceability_appendix.strip():
            validation_report["critical_issues"].append("Missing evidence traceability appendix.")
        elif traceability_appendix and "Claim | Source | Database | Retrieval date" not in traceability_appendix:
            validation_report["critical_issues"].append("Traceability appendix is malformed or incomplete.")

        # Calculate overall compliance
        if section_scores:
            validation_report["overall_compliance_score"] = sum(section_scores) / len(section_scores)

        # Final status
        validation_report["status"] = "PASS" if (
            validation_report["sections_compliant"] == validation_report["sections_validated"]
            and not validation_report["mandatory_sections_missing"]
            and not validation_report["critical_issues"]
        ) else "FAIL"

        return validation_report

    def get_sop_prompt_injection(self) -> str:
        """Generate SOP constraints for prompt injection"""
        prompt = """
## YOUR SOP CONSTRAINTS (MUST FOLLOW EXACTLY):

### MANDATORY SECTIONS (all required):
"""
        for section_name, spec in self.sections.items():
            if spec.get("priority") == "critical":
                prompt += f"\n- **{spec['title']}**"
                if "min_words" in spec:
                    prompt += f" ({spec['min_words']}-{spec['max_words']} words)"
                if "required_subsections" in spec:
                    subsections = ", ".join(s.replace("_", " ").title() for s in spec["required_subsections"])
                    prompt += f"\n  Must include: {subsections}"

        prompt += "\n\n### EVIDENCE STANDARDS:\n"
        prompt += "- Level 1A/1B evidence (RCTs, meta-analyses) required for efficacy claims\n"
        prompt += "- Include effect sizes, confidence intervals, sample sizes\n"
        prompt += "- Assign evidence levels to all clinical claims\n"

        prompt += "\n### ADVERSE EVENT CLASSIFICATION (CIOMS):\n"
        for freq_name, (freq_range, percentage) in self.ae_frequency.items():
            prompt += f"- {freq_name.replace('_', ' ').title()}: {percentage} {freq_range}\n"

        prompt += "\n### FORMATTING REQUIREMENTS:\n"
        prompt += "- Use Vancouver referencing style for citations\n"
        prompt += "- Include tables for complex data\n"
        prompt += "- Highlight key findings in insets/boxes\n"
        prompt += "- Target audience: Medical professionals (PGY-2 level)\n"

        return prompt

    def get_validation_checklist(self) -> Dict:
        """Get a checklist for manual review"""
        checklist = {}
        for section_name, spec in self.sections.items():
            checklist[section_name] = {
                "title": spec["title"],
                "priority": spec.get("priority", "normal"),
                "checks": []
            }

            if "min_words" in spec:
                checklist[section_name]["checks"].append(
                    f"Word count between {spec['min_words']}-{spec['max_words']}"
                )
            if "required_subsections" in spec:
                checklist[section_name]["checks"].append(
                    f"Includes: {', '.join(spec['required_subsections'])}"
                )

        return checklist


# Initialize globally
sop_engine = SOPEngine()

if __name__ == "__main__":
    # Test validation
    template = sop_engine.get_template_structure()
    print(f"Mandatory sections: {template['mandatory_sections']}")
    print(f"SOP constraints preview:\n{sop_engine.get_sop_prompt_injection()[:500]}...")
