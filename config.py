from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
MONOGRAPHS_DIR = DATA_DIR / "monographs"
SKILL_FILES_DIR = DATA_DIR / "skill_files"
FEEDBACK_DIR = DATA_DIR / "feedback"
GENERATION_HISTORY_DIR = DATA_DIR / "generation_history"
EVIDENCE_CACHE_DIR = DATA_DIR / "evidence_cache"

for directory in [DATA_DIR, MONOGRAPHS_DIR, SKILL_FILES_DIR, FEEDBACK_DIR, GENERATION_HISTORY_DIR, EVIDENCE_CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

PUBMED_TIMEOUT = int(os.getenv("PUBMED_TIMEOUT", "10"))
FDA_TIMEOUT = int(os.getenv("FDA_TIMEOUT", "10"))
GOOGLE_SCHOLAR_TIMEOUT = int(os.getenv("GOOGLE_SCHOLAR_TIMEOUT", "15"))
GENERATION_TIMEOUT = int(os.getenv("GENERATION_TIMEOUT", "60"))

PUBMED_API = os.getenv("PUBMED_API", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
FDA_API = os.getenv("FDA_API", "https://api.fda.gov/drug")

SOP_SECTIONS = {
    "introduction": {"title": "Introduction & Background", "min_words": 200, "max_words": 400, "priority": "high"},
    "rationale": {"title": "Rationale for Product", "min_words": 150, "max_words": 300, "priority": "high"},
    "pharmacology": {
        "title": "Pharmacology",
        "min_words": 500,
        "max_words": 800,
        "priority": "critical",
        "required_subsections": ["mechanism", "pharmacodynamics", "comparative"],
    },
    "pharmacokinetics": {
        "title": "Pharmacokinetics",
        "min_words": 400,
        "max_words": 1200,
        "priority": "critical",
        "required_subsections": ["absorption", "distribution", "metabolism", "elimination"],
    },
    "clinical_efficacy": {
        "title": "Clinical Efficacy",
        "min_words": 600,
        "max_words": 1200,
        "priority": "critical",
        "required_subsections": ["indications", "clinical_trials", "comparative"],
    },
    "safety": {
        "title": "Safety & Tolerability",
        "min_words": 400,
        "max_words": 800,
        "priority": "critical",
        "required_subsections": ["adverse_events", "contraindications", "drug_interactions"],
    },
    "dosage": {
        "title": "Dosage & Administration",
        "min_words": 300,
        "max_words": 600,
        "priority": "critical",
        "required_subsections": ["recommended_dose", "dosage_adjustments", "administration"],
    },
    "contraindications": {"title": "Contraindications", "min_words": 100, "max_words": 300, "priority": "high"},
    "drug_interactions": {"title": "Drug Interactions", "min_words": 200, "max_words": 500, "priority": "high"},
    "references": {"title": "References", "min_items": 15, "priority": "critical"},
}

EVIDENCE_LEVELS = {
    "1A": "RCTs, Meta-analyses (Highest)",
    "1B": "Large RCTs, Non-inferiority studies",
    "2": "Cohort studies, Case-control studies",
    "3": "Case reports, Mechanistic studies",
    "4": "Expert opinion (Lowest)",
}

AE_FREQUENCY = {
    "very_common": ("≥1/10", "≥10%"),
    "common": ("≥1/100, <1/10", "≥1%, <10%"),
    "uncommon": ("≥1/1,000, <1/100", "≥0.1%, <1%"),
    "rare": ("≥1/10,000, <1/1,000", "≥0.01%, <0.1%"),
    "very_rare": ("<1/10,000", "<0.01%"),
}

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openrouter")

APP_NAME = os.getenv("APP_NAME", "Product Monograph Champ")
APP_TAGLINE = os.getenv(
    "APP_TAGLINE",
    "Provider-Agnostic AI Monograph Generator",
)
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_BUILD = os.getenv("APP_BUILD", "local-dev")
APP_THEME = os.getenv("APP_THEME", "System Default")
APP_OWNER = os.getenv("APP_OWNER", "Dr. Bhupesh Jagdevraj Dewan")
APP_OWNER_LOCATION = os.getenv("APP_OWNER_LOCATION", "Mumbai, India")
APP_COPYRIGHT = os.getenv(
    "APP_COPYRIGHT",
    f"Copyright © 2026 {APP_OWNER}. All Rights Reserved.",
)
APP_RELEASE_DATE = os.getenv("APP_RELEASE_DATE", "2026-06-09")
MEDICAL_DISCLAIMER = os.getenv(
    "MEDICAL_DISCLAIMER",
    (
        "This application generates draft medical content for review only. "
        "It is not a substitute for medical judgment, regulatory review, "
        "or final approval by qualified professionals."
    ),
)
