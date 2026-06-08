"""
Validator: Auto-validation and compliance checking before delivery
"""
from typing import Dict, Tuple
from src.monograph.sop_engine import sop_engine

class MonographValidator:
    """Validates complete monographs against SOP requirements"""

    def __init__(self):
        self.sop = sop_engine

    def validate_and_score(self, monograph: Dict) -> Tuple[bool, Dict]:
        """
        Comprehensive validation and scoring
        Returns (is_valid, detailed_report)
        """
        report = self.sop.validate_complete_monograph(monograph)

        # Calculate detailed scoring
        report["detailed_scoring"] = {
            "structure_compliance": self._calculate_structure_score(report),
            "content_quality": self._calculate_content_score(report),
            "evidence_quality": self._calculate_evidence_score(report),
            "formatting_compliance": self._calculate_formatting_score(report),
            "overall_score": 0.0
        }

        # Calculate overall score
        scores = list(report["detailed_scoring"].values())[:-1]
        report["detailed_scoring"]["overall_score"] = sum(scores) / len(scores) if scores else 0

        # Determine if valid for delivery
        is_valid = (
            report["overall_compliance_score"] >= 90 and
            not report["critical_issues"] and
            len(report["mandatory_sections_missing"]) == 0
        )

        report["is_valid_for_delivery"] = is_valid
        report["recommendation"] = self._generate_recommendation(report)

        return is_valid, report

    def _calculate_structure_score(self, report: Dict) -> float:
        """Score based on section structure compliance"""
        validated = report.get("sections_validated", 0)
        compliant = report.get("sections_compliant", 0)

        if validated == 0:
            return 0.0

        return (compliant / validated) * 100

    def _calculate_content_quality(self, report: Dict) -> float:
        """Score based on content quality"""
        return report.get("overall_compliance_score", 0)

    def _calculate_content_score(self, report: Dict) -> float:
        """Score based on content checks"""
        return self._calculate_content_quality(report)

    def _calculate_evidence_score(self, report: Dict) -> float:
        """Score based on evidence quality in sections"""
        # Check if evidence checks passed in section details
        section_details = report.get("section_details", {})

        evidence_checks = 0
        total_checks = 0

        for section, details in section_details.items():
            if "evidence_grading" in details.get("checks", {}):
                total_checks += 1
                if details["checks"]["evidence_grading"]:
                    evidence_checks += 1

        if total_checks == 0:
            return 100.0  # No evidence checks needed

        return (evidence_checks / total_checks) * 100

    def _calculate_formatting_score(self, report: Dict) -> float:
        """Score based on formatting compliance"""
        # Check formatting-related validations
        return 85.0  # Placeholder - improve with actual formatting checks

    def _generate_recommendation(self, report: Dict) -> Dict:
        """Generate actionable recommendations"""
        recommendation = {
            "status": "READY FOR REVIEW" if report["is_valid_for_delivery"] else "NEEDS REVISION",
            "actions": [],
            "priority_fixes": []
        }

        # Critical issues
        if report.get("critical_issues"):
            recommendation["priority_fixes"] = report["critical_issues"]
            recommendation["actions"].append("Address all critical issues before delivery")

        # Missing sections
        if report.get("mandatory_sections_missing"):
            missing = ", ".join(report["mandatory_sections_missing"])
            recommendation["actions"].append(f"Generate missing mandatory sections: {missing}")

        # Low compliance sections
        for section, details in report.get("section_details", {}).items():
            if details.get("compliance_score", 0) < 80:
                recommendation["actions"].append(
                    f"Improve {section} compliance ({details['compliance_score']:.0f}%)"
                )

        # Positive notes
        if report["overall_compliance_score"] >= 95:
            recommendation["positive_notes"] = ["Excellent overall compliance"]
        elif report["overall_compliance_score"] >= 85:
            recommendation["positive_notes"] = ["Good compliance - minor refinements needed"]

        return recommendation

    def generate_validation_report(self, monograph: Dict) -> str:
        """Generate human-readable validation report"""
        is_valid, report = self.validate_and_score(monograph)

        report_text = f"""
═══════════════════════════════════════════════════════════════
MONOGRAPH VALIDATION REPORT
═══════════════════════════════════════════════════════════════

MOLECULE: {monograph.get('molecule_name', 'Unknown')}
GENERATED: {report.get('timestamp', 'N/A')}

COMPLIANCE SUMMARY:
─────────────────
Overall Compliance Score: {report['overall_compliance_score']:.1f}%
Sections Validated: {report['sections_validated']}/{report['sections_validated']}
Sections Compliant: {report['sections_compliant']}/{report['sections_validated']}
Status: {'[OK] VALID FOR DELIVERY' if is_valid else '[ERROR] NEEDS REVISION'}

DETAILED SCORING:
────────────────
Structure Compliance: {report['detailed_scoring']['structure_compliance']:.1f}%
Content Quality: {report['detailed_scoring']['content_quality']:.1f}%
Evidence Quality: {report['detailed_scoring']['evidence_quality']:.1f}%
Formatting Compliance: {report['detailed_scoring']['formatting_compliance']:.1f}%
OVERALL SCORE: {report['detailed_scoring']['overall_score']:.1f}%

CRITICAL ISSUES:
────────────────
"""
        if report.get("critical_issues"):
            for issue in report["critical_issues"]:
                report_text += f"• {issue}\n"
        else:
            report_text += "• None\n"

        report_text += f"""

RECOMMENDATIONS:
────────────────
Status: {report['recommendation']['status']}

Priority Fixes:
"""
        for fix in report['recommendation']['priority_fixes']:
            report_text += f"• {fix}\n"

        report_text += "\nNext Actions:\n"
        for action in report['recommendation']['actions']:
            report_text += f"• {action}\n"

        report_text += "\n" + "═" * 65 + "\n"

        return report_text


# Initialize globally
validator = MonographValidator()
