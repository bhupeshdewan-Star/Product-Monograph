"""
Configuration and constants for Monograph Generator
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Model Configuration
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2000
TEMPERATURE = 0.3

# Timeouts and Rate Limiting
PUBMED_TIMEOUT = 10
FDA_TIMEOUT = 10
GOOGLE_SCHOLAR_TIMEOUT = 15
CLAUDE_TIMEOUT = 60

# Data Sources
PUBMED_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
FDA_API = "https://api.fda.gov/drug"

# SOP Template Structure (Mandatory Sections)
SOP_SECTIONS = {
    "introduction": {
        "title": "Introduction & Background",
        "min_words": 200,
        "max_words": 400,
        "priority": "high"
    },
    "rationale": {
        "title": "Rationale for Product",
        "min_words": 150,
        "max_words": 300,
        "priority": "high"
    },
    "pharmacology": {
        "title": "Pharmacology",
        "min_words": 500,
        "max_words": 800,
        "priority": "critical",
        "required_subsections": ["mechanism", "pharmacodynamics", "comparative"]
    },
    "pharmacokinetics": {
        "title": "Pharmacokinetics",
        "min_words": 400,
        "max_words": 1200,
        "priority": "critical",
        "required_subsections": ["absorption", "distribution", "metabolism", "elimination"]
    },
    "clinical_efficacy": {
        "title": "Clinical Efficacy",
        "min_words": 600,
        "max_words": 1200,
        "priority": "critical",
        "required_subsections": ["indications", "clinical_trials", "comparative"]
    },
    "safety": {
        "title": "Safety & Tolerability",
        "min_words": 400,
        "max_words": 800,
        "priority": "critical",
        "required_subsections": ["adverse_events", "contraindications", "drug_interactions"]
    },
    "dosage": {
        "title": "Dosage & Administration",
        "min_words": 300,
        "max_words": 600,
        "priority": "critical",
        "required_subsections": ["recommended_dose", "dosage_adjustments", "administration"]
    },
    "contraindications": {
        "title": "Contraindications",
        "min_words": 100,
        "max_words": 300,
        "priority": "high"
    },
    "drug_interactions": {
        "title": "Drug Interactions",
        "min_words": 200,
        "max_words": 500,
        "priority": "high"
    },
    "references": {
        "title": "References",
        "min_items": 15,
        "priority": "critical"
    }
}

# Evidence Quality Levels (CIOMS Standard)
EVIDENCE_LEVELS = {
    "1A": "RCTs, Meta-analyses (Highest)",
    "1B": "Large RCTs, Non-inferiority studies",
    "2": "Cohort studies, Case-control studies",
    "3": "Case reports, Mechanistic studies",
    "4": "Expert opinion (Lowest)"
}

# Adverse Event Frequency (CIOMS Standard)
AE_FREQUENCY = {
    "very_common": ("≥1/10", "≥10%"),
    "common": ("≥1/100, <1/10", "≥1%, <10%"),
    "uncommon": ("≥1/1,000, <1/100", "≥0.1%, <1%"),
    "rare": ("≥1/10,000, <1/1,000", "≥0.01%, <0.1%"),
    "very_rare": ("<1/10,000", "<0.01%")
}

# File Paths
DATA_DIR = "data"
MONOGRAPHS_DIR = os.path.join(DATA_DIR, "monographs")
SKILL_FILES_DIR = os.path.join(DATA_DIR, "skill_files")
FEEDBACK_DIR = os.path.join(DATA_DIR, "feedback")

# Create directories if they don't exist
for dir_path in [DATA_DIR, MONOGRAPHS_DIR, SKILL_FILES_DIR, FEEDBACK_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Skill Files (Self-Learning Framework)
DEFAULT_SKILLS = {
    "evidence_quality": {
        "version": "1.0",
        "rules": [
            "All clinical claims must be supported by Level 1A-1B evidence",
            "Minimum 70% of claims should be from RCTs or meta-analyses",
            "Each claim must include effect size, confidence interval, sample size",
            "Evidence levels must be assigned (1A, 1B, 2, 3, 4)"
        ]
    },
    "safety_completeness": {
        "version": "1.0",
        "rules": [
            "Adverse events must be organized by CIOMS frequency categories",
            "Must include contraindications, drug interactions, special populations",
            "Serious warnings must be highlighted in a dedicated section",
            "Pregnancy/lactation information is mandatory"
        ]
    },
    "clinical_clarity": {
        "version": "1.0",
        "rules": [
            "Explain medical terms in plain language",
            "For numeric findings, add clinical significance explanation",
            "Target audience: Medical residents (PGY-2 level)",
            "Maximum jargon: 15% of total content"
        ]
    }
}

# Token Budget
TOKEN_BUDGET = {
    "development": 80000,
    "per_monograph_input": 19000,
    "per_monograph_output": 8100,
    "per_monograph_total": 27100,
    "cost_per_monograph": 0.154  # USD
}

# Generation Timeline Target
GENERATION_TARGET_MINUTES = 45
