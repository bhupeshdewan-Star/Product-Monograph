from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
from types import SimpleNamespace

try:
    import streamlit as st
except ImportError:  # pragma: no cover - handled at runtime
    st = None

import config as app_config
from src.agents.a11y.checker import check_accessibility
from src.agents.a11y.rendered import run_rendered_accessibility_review
from src.agents.auditor.builder import build_audit_schema
from src.agents.auditor.runner import run_audit
from src.agents.providers.provider_factory import create_provider
from src.services.evidence_retrieval import (
    EvidencePackage,
    collect_local_evidence,
    evidence_orchestrator,
    merge_local_evidence_package,
    EvidenceSourceResult,
)
from src.monograph.executive_summary import executive_summary_generator
from src.monograph.fallback_content import build_draft_placeholders
from src.monograph.model_discovery import model_discovery_service
from src.monograph.generation_config import (
    GenerationConfig,
    PROVIDER_LABELS,
    resolve_generation_config,
)
from src.monograph.generator import synthesis_engine
from src.monograph.validators import validator
from src.services.export_service import export_service
from src.services.history_tracker import output_history
from src.utils.markdown_cleaner import markdown_cleaner


MODE_LABELS = {
    "AI Mode": "ai",
    "Demo Mode": "demo",
    "Local Model Mode": "local",
}

AI_PROVIDER_LABELS = {
    "OpenAI": "openai",
    "Claude": "anthropic",
    "Gemini": "google",
    "DeepSeek": "deepseek",
    "Groq": "groq",
    "OpenRouter": "openrouter",
}

AUDIT_PROVIDER_OPTIONS = ["none", "openai", "anthropic", "google", "deepseek", "groq", "openrouter"]
LOCAL_PROVIDER_KEY = "openai-compatible local"
LOCAL_MODEL_BASE_URL = os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1")
WRITING_STYLE_PRESETS = {
    "Regulatory Writing": 0.10,
    "Medical Affairs": 0.20,
    "Scientific Review": 0.30,
    "Educational": 0.40,
    "Marketing": 0.50,
    "Creative": 0.80,
}
MODE_TEMPERATURE_RECOMMENDATIONS = {
    "ai": ("Medical Affairs", 0.20),
    "local": ("Scientific Review", 0.30),
    "demo": ("Demo Mode uses deterministic fallback content, so temperature has minimal impact.", None),
}

EVIDENCE_SOURCE_LABELS = {
    "local": "Local Evidence Vault",
    "pubmed": "PubMed",
    "fda": "FDA",
    "ema": "EMA",
    "clinicaltrials": "ClinicalTrials.gov",
}

PROVIDER_ENV_KEYS = {
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
}


def _config_value(name: str, default: str) -> str:
    value = getattr(app_config, name, default)
    return value if isinstance(value, str) else str(value)


APP_NAME = _config_value("APP_NAME", "Product Monograph Champ")
APP_TAGLINE = _config_value("APP_TAGLINE", "Provider-Agnostic AI Monograph Generator")
APP_VERSION = _config_value("APP_VERSION", "")
APP_BUILD = _config_value("APP_BUILD", "local-dev")
APP_THEME = _config_value("APP_THEME", "System Default")
APP_OWNER = _config_value("APP_OWNER", "Dr. Bhupesh Jagdevraj Dewan")
APP_OWNER_LOCATION = _config_value("APP_OWNER_LOCATION", "Mumbai, India")
APP_COPYRIGHT = _config_value(
    "APP_COPYRIGHT",
    f"Copyright © 2026 {APP_OWNER}. All Rights Reserved.",
)
APP_RELEASE_DATE = _config_value("APP_RELEASE_DATE", "")
MEDICAL_DISCLAIMER = _config_value(
    "MEDICAL_DISCLAIMER",
    (
        "This application generates draft medical content for review only. "
        "It is not a substitute for medical judgment, regulatory review, "
        "or final approval by qualified professionals."
    ),
)


def sample_sources(molecule_name: str) -> dict:
    return {
        "molecule": molecule_name,
        "sources": {
            "pubmed": [
                {
                    "title": f"Sample PubMed evidence for {molecule_name}",
                    "authors": ["Sample Author"],
                    "journal": "Sample Journal",
                    "publication_date": "2026",
                    "doi": "10.0000/sample",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/",
                }
            ],
            "fda": [
                {
                    "drug_name": molecule_name,
                    "indications": f"Sample regulatory indication for {molecule_name}.",
                    "url": "https://www.fda.gov/",
                }
            ],
            "google_scholar": [],
            "open_access": [],
        },
        "total_articles": 2,
        "formatted_text": f"Sample research data for {molecule_name}",
    }


def sample_evidence_package(molecule_name: str) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    package = {
        "molecule": molecule_name,
        "retrieved_at": timestamp,
        "sources": {
            "pubmed": [
                {
                    "source": "pubmed",
                    "title": f"Sample PubMed evidence for {molecule_name}",
                    "abstract": f"Sample abstract for {molecule_name}.",
                    "journal": "Sample Journal",
                    "year": "2026",
                    "identifier": "00000000",
                    "doi": "10.0000/sample",
                    "authors": ["Sample Author"],
                    "url": "https://pubmed.ncbi.nlm.nih.gov/00000000/",
                }
            ],
            "fda": [
                {
                    "source": "fda",
                    "title": f"FDA label for {molecule_name}",
                    "indications": f"Sample label evidence for {molecule_name}.",
                    "warnings": f"Sample safety warning for {molecule_name}.",
                    "contraindications": f"Sample contraindication summary for {molecule_name}.",
                    "dosage": f"Sample dosage summary for {molecule_name}.",
                    "adverse_reactions": f"Sample adverse reaction summary for {molecule_name}.",
                    "url": "https://www.accessdata.fda.gov/scripts/cder/daf/",
                }
            ],
            "ema": [],
            "clinicaltrials": [
                {
                    "source": "clinicaltrials",
                    "title": f"Sample clinical trial evidence for {molecule_name}",
                    "identifier": "NCT00000000",
                    "status": "Completed",
                    "phase": "Phase 3",
                    "conditions": [molecule_name],
                    "interventions": [molecule_name],
                    "outcomes": ["Sample outcome"],
                    "sponsor": "Sample Sponsor",
                    "enrollment": "100",
                    "start_date": "2025",
                    "completion_date": "2026",
                    "url": "https://clinicaltrials.gov/study/NCT00000000",
                }
            ],
        },
        "summary": {
            "total_records": 3,
            "pubmed_count": 1,
            "fda_count": 1,
            "ema_count": 0,
            "clinicaltrials_count": 1,
        },
        "total_articles": 3,
        "limitations": ["Sample evidence only. Replace with live evidence before release."],
        "source_errors": [],
        "source_status": {
            "pubmed": {"source": "pubmed", "status": "found", "count": 1, "records": [], "error": "", "elapsed_ms": 0, "cached": True, "request_url": ""},
            "fda": {"source": "fda", "status": "found", "count": 1, "records": [], "error": "", "elapsed_ms": 0, "cached": True, "request_url": ""},
            "ema": {"source": "ema", "status": "empty", "count": 0, "records": [], "error": "Sample evidence only.", "elapsed_ms": 0, "cached": True, "request_url": ""},
            "clinicaltrials": {"source": "clinicaltrials", "status": "found", "count": 1, "records": [], "error": "", "elapsed_ms": 0, "cached": True, "request_url": ""},
        },
        "cache_status": {"hit": True, "key": "sample", "cache_dir": "sample"},
        "evidence_context": (
            f"STRUCTURED EVIDENCE PACKAGE\nMolecule: {molecule_name}\n"
            "Sample evidence package for demo mode only."
        ),
        "evidence_references": (
            f"1. Sample PubMed evidence for {molecule_name}. Sample Journal. 2026. doi:10.0000/sample. PMID:00000000.\n"
            f"2. U.S. Food and Drug Administration. FDA label for {molecule_name} label. Available from: https://www.accessdata.fda.gov/scripts/cder/daf/.\n"
            f"3. ClinicalTrials.gov. Sample clinical trial evidence for {molecule_name}. NCT00000000. Available from: https://clinicaltrials.gov/study/NCT00000000."
        ),
        "retrieved_with": {
            "molecule": molecule_name,
            "mode": "demo",
            "max_results": 1,
        },
    }
    return package


def inline_fetcher(html: str, final_url: str = "inline://content"):
    def _fetcher(_: str):
        return SimpleNamespace(html=html, final_url=final_url)

    return _fetcher


def _env_key(provider: str) -> str | None:
    for env_name in PROVIDER_ENV_KEYS.get(provider, []):
        if os.getenv(env_name):
            return env_name
    return None


def _env_key_present(provider: str) -> bool:
    return _env_key(provider) is not None


def _current_model_key(prefix: str, provider: str) -> str:
    return f"{prefix}_{provider}_model_choice"


def _manual_model_key(prefix: str, provider: str) -> str:
    return f"{prefix}_{provider}_manual_model"


def _base_url_key(prefix: str) -> str:
    return f"{prefix}_base_url"


def _provider_api_key_key(prefix: str) -> str:
    return f"{prefix}_api_key"


def _temperature_preset_key(prefix: str) -> str:
    return f"{prefix}_temperature_preset"


def _temperature_slider_key(prefix: str) -> str:
    return f"{prefix}_temperature"


def _discovery_warning_to_text(warning: str | None, developer_mode: bool = False) -> str:
    if not warning:
        return ""
    if developer_mode:
        return warning
    return "Model discovery is temporarily unavailable. Enter a model manually or switch providers."


def _apply_temperature_preset(prefix: str) -> None:
    preset = st.session_state.get(_temperature_preset_key(prefix), "Medical Affairs")
    value = WRITING_STYLE_PRESETS.get(preset)
    if value is not None:
        st.session_state[_temperature_slider_key(prefix)] = value


def _temperature_guidance_html(mode: str) -> str:
    rec = MODE_TEMPERATURE_RECOMMENDATIONS.get(mode, ("Medical Affairs", 0.2))
    if mode == "demo":
        return """
        <div class="pmono-callout">
            <strong>Demo Mode note:</strong> Temperature has minimal impact because deterministic fallback content is used.
        </div>
        """
    preset_name, preset_value = rec
    return f"""
    <div class="pmono-callout">
        <strong>Temperature controls how creative or deterministic the AI is when writing.</strong>
        <ul class="pmono-bullets">
            <li>Lower values: more factual, more consistent, more repeatable, lower hallucination risk.</li>
            <li>Higher values: more varied wording, more creative phrasing, more exploratory content, higher variability.</li>
        </ul>
        <p><strong>Recommended setting for medical and regulatory content:</strong> 0.2-0.3</p>
        <p><strong>Current recommendation:</strong> {preset_name} ({preset_value:.1f})</p>
    </div>
    """


def _render_temperature_controls(prefix: str, mode: str) -> float:
    preset_key = _temperature_preset_key(prefix)
    slider_key = _temperature_slider_key(prefix)
    if preset_key not in st.session_state:
        st.session_state[preset_key] = "Medical Affairs" if mode == "ai" else ("Scientific Review" if mode == "local" else "Medical Affairs")
    if slider_key not in st.session_state:
        default_temp = 0.2 if mode == "ai" else (0.3 if mode == "local" else 0.3)
        st.session_state[slider_key] = default_temp
    preset_options = ["Custom"] + list(WRITING_STYLE_PRESETS.keys())
    if st.session_state[preset_key] not in preset_options:
        st.session_state[preset_key] = "Medical Affairs" if mode == "ai" else ("Scientific Review" if mode == "local" else "Medical Affairs")

    preset = st.sidebar.selectbox(
        "Writing style preset",
        preset_options,
        index=preset_options.index(st.session_state[preset_key]),
        key=preset_key,
        help="Choose a preset to quickly set the temperature for this writing style.",
        on_change=_apply_temperature_preset,
        args=(prefix,),
    )
    if preset in WRITING_STYLE_PRESETS and st.session_state[slider_key] == 0.3:
        # If a preset is selected for the first time, align the slider immediately.
        st.session_state[slider_key] = WRITING_STYLE_PRESETS[preset]

    temperature = st.sidebar.slider(
        "Temperature",
        0.0,
        1.0,
        float(st.session_state[slider_key]),
        0.05,
        key=slider_key,
        help=(
            "Temperature determines the randomness of AI output. Low temperature = predictable and factual. "
            "High temperature = creative and varied. Medical monographs generally perform best at 0.2-0.3."
        ),
    )
    st.sidebar.caption(
        "Temperature controls how creative or deterministic the AI is when writing. Lower values are more factual and repeatable. "
        "Higher values are more varied and exploratory. Recommended for medical and regulatory content: 0.2-0.3."
    )
    st.sidebar.caption(_temperature_mode_recommendation(mode))
    return float(temperature)


def _temperature_mode_recommendation(mode: str) -> str:
    rec = MODE_TEMPERATURE_RECOMMENDATIONS.get(mode, MODE_TEMPERATURE_RECOMMENDATIONS["ai"])
    if mode == "demo":
        return rec[0]
    return f"Recommended: {rec[0]} ({rec[1]:.1f})"


def _discovery_get(discovery, key: str, default=None):
    if discovery is None:
        return default
    if isinstance(discovery, dict):
        return discovery.get(key, default)
    return getattr(discovery, key, default)


def _evidence_source_issue_items(evidence_package: dict | None) -> list[dict]:
    if not evidence_package:
        return []
    source_status = evidence_package.get("source_status", {}) or {}
    issues: list[dict] = []
    for source_name in ("local", "pubmed", "fda", "ema", "clinicaltrials"):
        source_result = source_status.get(source_name) or {}
        status = _discovery_get(source_result, "status", "unknown")
        error = (_discovery_get(source_result, "error", "") or "").strip()
        count = int(_discovery_get(source_result, "count", 0) or 0)
        if status in {"failed", "unavailable"}:
            issues.append(
                {
                    "source": source_name,
                    "label": EVIDENCE_SOURCE_LABELS[source_name],
                    "status": status,
                    "message": error or f"{EVIDENCE_SOURCE_LABELS[source_name]} evidence unavailable.",
                    "count": count,
                }
            )
        elif status == "empty":
            issues.append(
                {
                    "source": source_name,
                    "label": EVIDENCE_SOURCE_LABELS[source_name],
                    "status": status,
                    "message": "No matching records were found.",
                    "count": count,
                }
            )
    return issues


def _available_evidence_source_labels(evidence_package: dict | None) -> list[str]:
    if not evidence_package:
        return []
    source_status = evidence_package.get("source_status", {}) or {}
    labels: list[str] = []
    for source_name in ("local", "pubmed", "fda", "ema", "clinicaltrials"):
        source_result = source_status.get(source_name) or {}
        count = int(_discovery_get(source_result, "count", 0) or 0)
        if count > 0:
            labels.append(f"✓ {EVIDENCE_SOURCE_LABELS[source_name]}")
    return labels


def _evidence_all_sources_failed(evidence_package: dict | None) -> bool:
    if not evidence_package:
        return False
    summary = evidence_package.get("summary", {}) or {}
    return int(summary.get("total_records", 0) or 0) == 0


def _set_session_flag(flag_name: str, value: bool = True) -> None:
    st.session_state[flag_name] = value


def _report_exception(
    context: str,
    exc: Exception,
    developer_mode: bool,
    *,
    severity: str = "error",
) -> None:
    if developer_mode:
        message = f"{context}: {exc}"
    else:
        message = f"{context}. Open Developer Mode for details."
    getattr(st, severity)(message)


def _friendly_evidence_issue_message(source_name: str, status: str, raw_message: str = "") -> str:
    source_label = EVIDENCE_SOURCE_LABELS.get(source_name, source_name.title())
    status = (status or "").lower()
    if status == "empty":
        if source_name == "clinicaltrials":
            return "No ClinicalTrials.gov studies found."
        if source_name == "ema":
            return "No structured EMA results were found."
        if source_name == "pubmed":
            return "No PubMed records matched the current molecule."
        if source_name == "fda":
            return "No FDA label records were found."
        if source_name == "local":
            return "No local evidence files were available."
        return f"No matching {source_label} records were found."
    if source_name == "clinicaltrials":
        return "ClinicalTrials.gov temporarily unavailable."
    if source_name == "ema":
        return "EMA temporarily unavailable."
    if source_name == "pubmed":
        return "PubMed temporarily unavailable."
    if source_name == "fda":
        return "FDA temporarily unavailable."
    if source_name == "local":
        return "Local Evidence Vault temporarily unavailable."
    return f"{source_label} temporarily unavailable."


def _display_evidence_issue(issue: dict, developer_mode: bool) -> None:
    status = (issue.get("status") or "unknown").lower()
    label = issue.get("label") or issue.get("source", "Evidence")
    if developer_mode:
        message = issue.get("message") or ""
    else:
        message = _friendly_evidence_issue_message(issue.get("source", ""), status, issue.get("message") or "")
    if status == "empty":
        st.info(f"⚠ {label}: {message}")
    else:
        st.error(f"⚠ {label}: {message}")


def _build_pending_generation_request(
    *,
    molecule_name: str,
    specialty: str,
    generation_config: GenerationConfig,
    generation_sources: dict,
    evidence_package,
    local_evidence_result,
    local_evidence_summary: dict,
    source_issues: list[dict],
) -> dict:
    return {
        "molecule_name": molecule_name,
        "specialty": specialty,
        "generation_config": generation_config.model_dump(),
        "generation_sources": deepcopy(generation_sources),
        "evidence_package": evidence_package.model_dump() if evidence_package else {},
        "local_evidence_result": deepcopy(local_evidence_result),
        "local_evidence_summary": deepcopy(local_evidence_summary),
        "source_issues": deepcopy(source_issues),
    }


def _restore_pending_generation_request(pending_request: dict | None) -> dict:
    if not pending_request:
        return {}
    restored = deepcopy(pending_request)
    if restored.get("generation_config"):
        restored["generation_config"] = GenerationConfig.model_validate(restored["generation_config"])
    return restored


def _clear_generation_flow_state() -> None:
    for key in (
        "pending_generation_request",
        "resume_generation_requested",
        "no_evidence_confirmation_pending",
        "proceed_limited_evidence",
        "evidence_refresh_requested",
    ):
        st.session_state.pop(key, None)


def _clear_generation_runtime_state() -> None:
    for key in (
        "generated_monograph",
        "generated_sources",
        "evidence_package",
        "last_generation_error",
        "pending_generation_request",
        "resume_generation_requested",
        "no_evidence_confirmation_pending",
        "proceed_limited_evidence",
        "evidence_refresh_requested",
        "generation_stage",
    ):
        st.session_state.pop(key, None)


def _generated_monograph_state(
    monograph: dict,
    generation_sources: dict,
    evidence_package,
) -> dict:
    if hasattr(evidence_package, "model_dump"):
        evidence_payload = evidence_package.model_dump()
    else:
        evidence_payload = evidence_package or {}
    return {
        "generated_monograph": monograph,
        "generated_sources": generation_sources,
        "evidence_package": evidence_payload,
        "last_generation_error": None,
    }


def _has_renderable_monograph(monograph: dict | None) -> bool:
    return bool(monograph and monograph.get("molecule_name") and monograph.get("sections"))


def _has_export_downloads(exports: dict | None) -> bool:
    if not exports:
        return False
    for key in ("json", "markdown", "pdf", "word", "xlsx", "print_ready", "google_docs"):
        if exports.get(key):
            return True
    return False


def _local_evidence_summary(local_package: dict | None) -> dict:
    if not local_package:
        return {
            "files_loaded": 0,
            "file_names": [],
            "word_count": 0,
            "source_errors": [],
            "extraction_details": [],
        }
    records = local_package.get("records", []) or []
    summary = local_package.get("summary", {}) or {}
    return {
        "files_loaded": len(records),
        "file_names": [record.get("source_name") or record.get("title") for record in records],
        "word_count": sum(int((record.get("metadata", {}) or {}).get("word_count", 0) or 0) for record in records),
        "source_errors": summary.get("source_errors", []),
        "extraction_details": summary.get("extraction_details", []),
        "include_full_paths": summary.get("include_full_paths", False),
    }


def _local_evidence_record_view(local_package: dict | None) -> list[dict]:
    if not local_package:
        return []
    return list(local_package.get("records", []) or [])


def _compact_text(text: str, max_chars: int) -> str:
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 80)].rstrip() + "\n[Evidence context truncated for fast local draft.]"


def _effective_local_research_cap(max_results: int, fast_local_draft: bool, local_cap: int = 5) -> int:
    if not fast_local_draft:
        return max_results
    return max(3, min(max_results, local_cap))


def _estimate_local_prompt_tokens(
    molecule_name: str,
    local_summary: dict | None,
    compact_prompt_mode: bool,
    compact_evidence_chars: int,
    compact_records: int,
    section_generation_mode: bool,
) -> dict:
    local_summary = local_summary or {}
    files_loaded = int(local_summary.get("files_loaded", 0) or 0)
    word_count = int(local_summary.get("word_count", 0) or 0)
    local_tokens = max(1, int(word_count * 1.25))
    base_tokens = 180 if compact_prompt_mode else 360
    evidence_tokens = min(local_tokens, max(120, compact_evidence_chars // 4))
    record_tokens = compact_records * 180
    section_tokens = 140 if section_generation_mode else 0
    estimated = base_tokens + evidence_tokens + record_tokens + section_tokens + max(40, len(molecule_name) * 2)
    return {
        "estimated_prompt_tokens": estimated,
        "estimated_prompt_characters": int(estimated * 4),
        "files_loaded": files_loaded,
        "word_count": word_count,
        "compact_prompt_mode": compact_prompt_mode,
        "compact_evidence_chars": compact_evidence_chars,
        "compact_records": compact_records,
        "section_generation_mode": section_generation_mode,
    }


def _compact_evidence_package_for_local_draft(
    evidence_package: dict,
    *,
    context_chars: int = 1800,
    total_records: int | None = None,
    prioritize_local: bool = False,
) -> dict:
    compact = deepcopy(evidence_package or {})
    sources = deepcopy(compact.get("sources", {}) or {})
    if prioritize_local and total_records:
        selected_sources = {}
        remaining = max(1, total_records)
        for source_name in ("local", "pubmed", "fda", "ema", "clinicaltrials"):
            source_records = list(sources.get(source_name, []) or [])
            if remaining <= 0:
                selected_sources[source_name] = []
                continue
            keep = min(len(source_records), remaining)
            selected_sources[source_name] = source_records[:keep]
            remaining -= keep
        sources = selected_sources
    else:
        caps = {"pubmed": 2, "fda": 1, "ema": 1, "clinicaltrials": 1}
        for source_name, cap in caps.items():
            source_records = list(sources.get(source_name, []) or [])
            sources[source_name] = source_records[:cap]
    compact["sources"] = sources
    compact_context = _compact_text(
        compact.get("evidence_context") or compact.get("formatted_text", ""),
        context_chars,
    )
    compact["evidence_context"] = compact_context
    compact["formatted_text"] = compact_context
    if compact.get("evidence_references"):
        compact["evidence_references"] = _compact_text(compact["evidence_references"], 2200)
    return compact


def _prepare_local_compact_sources(
    evidence_package: dict,
    *,
    compact_prompt_mode: bool,
    compact_evidence_chars: int,
    compact_records: int,
    section_generation_mode: bool,
) -> dict:
    compact = _compact_evidence_package_for_local_draft(
        evidence_package,
        context_chars=compact_evidence_chars,
        total_records=compact_records,
        prioritize_local=True,
    )
    retrieved_with = deepcopy(compact.get("retrieved_with", {}) or {})
    retrieved_with.update(
        {
            "local_compact_prompt_mode": compact_prompt_mode,
            "local_section_generation_mode": section_generation_mode,
            "local_compact_evidence_chars": compact_evidence_chars,
            "local_compact_evidence_records": compact_records,
            "local_compact_prompt_applied": True,
        }
    )
    compact["retrieved_with"] = retrieved_with
    compact["local_compact_prompt_mode"] = compact_prompt_mode
    compact["local_section_generation_mode"] = section_generation_mode
    compact["local_compact_evidence_chars"] = compact_evidence_chars
    compact["local_compact_evidence_records"] = compact_records
    return compact


def _warm_up_local_model(provider_config, model: str) -> dict:
    provider = create_provider(provider_config)
    response = provider.generate(
        prompt="Reply with only: ready",
        system_prompt="Reply with only: ready",
        model=model,
        api_key=None,
        temperature=0.0,
        max_completion_tokens=5,
    )
    return {
        "ok": response.strip().lower() == "ready",
        "response": response.strip(),
    }


def _run_tiny_local_test(provider_config, model: str) -> dict:
    provider = create_provider(provider_config)
    prompt = "Write a 3-line monograph for Paracetamol."
    response = provider.generate(
        prompt=prompt,
        system_prompt="Write a 3-line monograph for Paracetamol. Return only the monograph.",
        model=model,
        api_key=None,
        temperature=0.2,
        max_completion_tokens=120,
    )
    diagnostics = getattr(provider, "last_request_diagnostics", {}) or {}
    return {
        "ok": bool(response.strip()),
        "response": response.strip(),
        "prompt": prompt,
        "diagnostics": diagnostics,
    }


def _resolve_model_selection(
    *,
    prefix: str,
    provider: str,
    base_url: str | None,
    api_key: str | None,
    force_refresh: bool = False,
) -> dict:
    manual_key = api_key or ""
    env_name = _env_key(provider)
    env_detected = env_name is not None
    manual_key_supplied = bool(manual_key.strip())
    discovery_key = manual_key.strip() or (os.getenv(env_name) if env_name else None)
    discovered = None
    warning = None
    model_options: list[str] = []
    model_source = "manual"
    if provider in {"openai", "anthropic", "google", "deepseek", "groq", "openrouter", LOCAL_PROVIDER_KEY}:
        try:
            discovered = model_discovery_service.discover_models(
                provider=provider,
                api_key=discovery_key,
                base_url=base_url,
                force_refresh=force_refresh,
            )
            model_options = list(discovered.models)
            warning = discovered.warning
            model_source = discovered.source
        except Exception as exc:
            warning = str(exc)
            discovered = None

    select_key = _current_model_key(prefix, provider)
    manual_model_key_name = _manual_model_key(prefix, provider)
    current_choice = st.session_state.get(select_key, "")
    manual_value = st.session_state.get(manual_model_key_name, "")

    if model_options:
        select_options = ["Use manual entry"] + model_options
        if current_choice not in select_options:
            current_choice = select_options[1]
        selected_choice = st.sidebar.selectbox(
            "Available models",
            options=select_options,
            index=select_options.index(current_choice),
            key=select_key,
        )
    else:
        selected_choice = st.sidebar.selectbox(
            "Available models",
            options=["No live models found"],
            index=0,
            disabled=True,
            key=select_key,
        )

    manual_model = st.sidebar.text_input(
        "Manual model override",
        value=manual_value,
        key=manual_model_key_name,
        placeholder="Leave blank to use a discovered model or provider default.",
    )

    if manual_model.strip():
        final_model = manual_model.strip()
        model_source = "manual"
    elif model_options and selected_choice not in {"Use manual entry"}:
        final_model = selected_choice
        model_source = discovered.source if discovered else "live"
    else:
        final_model = ""
        model_source = "none"

    return {
        "provider": provider,
        "provider_label": PROVIDER_LABELS.get(provider, provider),
        "env_key_detected": env_detected,
        "manual_key_supplied": manual_key_supplied,
        "api_key": manual_key,
        "base_url": base_url,
        "discovery": discovered,
        "model_options": model_options,
        "selected_model": final_model,
        "selected_model_source": model_source,
        "warning": warning,
    }


def _render_provider_mode_controls(mode: str, prefix: str, developer_mode: bool = False) -> dict:
    if mode == "ai":
        st.sidebar.subheader("AI Provider")
        provider_label = st.sidebar.selectbox(
            "Provider",
            list(AI_PROVIDER_LABELS.keys()),
            index=0,
            key=f"{prefix}_provider_label",
        )
        provider = AI_PROVIDER_LABELS[provider_label]
        api_key = st.sidebar.text_input(
            "API key",
            type="password",
            key=_provider_api_key_key(prefix),
            help="Provide a runtime API key here or set the matching environment variable.",
        )
        st.sidebar.caption("Optional preset above the slider: Regulatory Writing, Medical Affairs, Scientific Review, Educational, Marketing, or Creative.")
        temperature = _render_temperature_controls(prefix, "ai")
        refresh_models = st.sidebar.button("Refresh Available Models", key=f"{prefix}_refresh_models")
        discovery = _resolve_model_selection(
            prefix=prefix,
            provider=provider,
            base_url=None,
            api_key=api_key,
            force_refresh=refresh_models,
        )
        if not discovery["selected_model"] and discovery.get("warning") is None:
            discovery["warning"] = "No discovered models were returned. Enter a model manually."
        return {
            "mode": mode,
            "provider_choice": provider,
            "provider_label": provider_label,
            "model": discovery["selected_model"],
            "model_source": discovery["selected_model_source"],
            "api_key": api_key,
            "temperature": temperature,
            "base_url": None,
            "discovery": discovery,
        }

    if mode == "local":
        st.sidebar.subheader("Local Model")
        st.sidebar.selectbox(
            "Provider",
            ["Local Model"],
            index=0,
            disabled=True,
            key=f"{prefix}_local_provider",
        )
        base_url = st.sidebar.text_input(
            "Base URL",
            value=LOCAL_MODEL_BASE_URL,
            key=_base_url_key(prefix),
            help="OpenAI-compatible local endpoint or proxy URL.",
        )
        st.sidebar.caption("Local Model Mode works best with a fast draft temperature preset and a short completion budget.")
        fast_local_draft = st.sidebar.checkbox(
            "Fast local draft",
            value=True,
            key=f"{prefix}_fast_local_draft",
            help="When enabled, the app keeps the draft compact, caps evidence intake, and targets a quick first draft for local models.",
        )
        local_compact_prompt_mode = st.sidebar.checkbox(
            "Local Compact Prompt Mode",
            value=True,
            key=f"{prefix}_local_compact_prompt_mode",
            help="Uses compact evidence summaries only and keeps the prompt short for smaller local models.",
        )
        local_evidence_cap = 5
        if fast_local_draft:
            local_evidence_cap = st.sidebar.slider(
                "Fast draft evidence cap",
                3,
                5,
                5,
                key=f"{prefix}_fast_local_evidence_cap",
                help="Caps the number of evidence records used for the first local draft.",
            )
        local_compact_evidence_chars = st.sidebar.slider(
            "Compact evidence characters",
            2000,
            10000,
            3000,
            step=250,
            key=f"{prefix}_local_compact_evidence_chars",
            help="Caps the amount of evidence text sent to the local model.",
        )
        local_section_generation_mode = st.sidebar.checkbox(
            "Section-by-section local generation",
            value=True,
            key=f"{prefix}_local_section_generation_mode",
            help="Generates sections sequentially when the prompt is too large for a local model.",
        )
        refresh_models = st.sidebar.button("Refresh Available Models", key=f"{prefix}_refresh_models")
        discovery = _resolve_model_selection(
            prefix=prefix,
            provider=LOCAL_PROVIDER_KEY,
            base_url=base_url,
            api_key="",
            force_refresh=refresh_models,
        )
        if not discovery["selected_model"] and discovery.get("warning") is None:
            discovery["warning"] = "No local models were returned. Enter a model manually."
        warm_up_clicked = st.sidebar.button("Warm up Local Model", key=f"{prefix}_warm_up_ollama")
        prompt_estimate = _estimate_local_prompt_tokens(
            st.session_state.get("molecule_name_input", st.session_state.get("molecule_name", "")),
            st.session_state.get("local_evidence_summary"),
            local_compact_prompt_mode,
            local_compact_evidence_chars,
            local_evidence_cap,
            local_section_generation_mode,
        )
        st.sidebar.caption(
            f"Estimated prompt: ~{prompt_estimate['estimated_prompt_tokens']} tokens "
            f"(~{prompt_estimate['estimated_prompt_characters']} chars)."
        )
        st.sidebar.caption(
            f"Compact mode: {'ON' if local_compact_prompt_mode else 'OFF'} | "
            f"Evidence records: {local_evidence_cap} | Evidence chars: {local_compact_evidence_chars}"
        )
        if prompt_estimate["estimated_prompt_tokens"] > 2400 and not local_compact_prompt_mode:
            st.sidebar.warning("Estimated prompt is large. Compact mode will be applied automatically.")
        if warm_up_clicked:
            if not discovery["selected_model"]:
                st.sidebar.warning("Select or enter a local model before warming up.")
            else:
                try:
                    provider_cfg = resolve_generation_config(
                        mode="local",
                        provider_choice=LOCAL_PROVIDER_KEY,
                        model=discovery["selected_model"],
                        api_key="",
                        base_url=base_url,
                        temperature=0.0,
                    ).to_provider_config()
                    warmup_result = _warm_up_local_model(provider_cfg, discovery["selected_model"])
                    st.session_state["local_model_warmup"] = warmup_result
                    if warmup_result.get("ok"):
                        st.sidebar.success(f"Local model warm-up complete: {warmup_result.get('response', 'ready')}")
                    else:
                        st.sidebar.warning(f"Local model returned: {warmup_result.get('response', '') or 'unexpected response'}")
                except Exception as exc:
                    st.session_state["local_model_warmup"] = {"ok": False, "error": str(exc)}
                    if developer_mode:
                        st.sidebar.error(f"Warm-up failed: {exc}")
                    else:
                        st.sidebar.error("Warm-up failed. Open Developer Mode for details.")
        warmup_state = st.session_state.get("local_model_warmup")
        if warmup_state:
            if warmup_state.get("ok"):
                st.sidebar.caption(f"Last warm-up response: {warmup_state.get('response', 'ready')}")
            elif warmup_state.get("error"):
                if developer_mode:
                    st.sidebar.caption(f"Last warm-up error: {warmup_state.get('error')}")
                else:
                    st.sidebar.caption("Last warm-up failed. Open Developer Mode for details.")
        temperature = _render_temperature_controls(prefix, "local")
        prompt_estimate = _estimate_local_prompt_tokens(
            st.session_state.get("molecule_name_input", st.session_state.get("molecule_name", "")),
            st.session_state.get("local_evidence_summary"),
            local_compact_prompt_mode,
            local_compact_evidence_chars,
            local_evidence_cap,
            local_section_generation_mode,
        )
        st.sidebar.caption(
            f"Estimated prompt tokens before submission: ~{prompt_estimate['estimated_prompt_tokens']} "
            f"(about {prompt_estimate['estimated_prompt_characters']} characters)."
        )
        tiny_test_clicked = st.sidebar.button(
            "Tiny Local Test",
            key=f"{prefix}_tiny_local_test",
            help="Runs a minimal local-only probe with no evidence retrieval so you can isolate provider behavior.",
        )
        if tiny_test_clicked:
            if not discovery["selected_model"]:
                st.sidebar.warning("Select or enter a local model before running the tiny test.")
            else:
                try:
                    provider_cfg = resolve_generation_config(
                        mode="local",
                        provider_choice=LOCAL_PROVIDER_KEY,
                        model=discovery["selected_model"],
                        api_key="",
                        base_url=base_url,
                        temperature=0.2,
                    ).to_provider_config()
                    tiny_result = _run_tiny_local_test(provider_cfg, discovery["selected_model"])
                    st.session_state["tiny_local_test"] = tiny_result
                    if tiny_result.get("ok"):
                        st.sidebar.success("Tiny Local Test succeeded.")
                    else:
                        st.sidebar.warning("Tiny Local Test returned an empty response.")
                except Exception as exc:
                    st.session_state["tiny_local_test"] = {"ok": False, "error": str(exc)}
                    if developer_mode:
                        st.sidebar.error(f"Tiny Local Test failed: {exc}")
                    else:
                        st.sidebar.error("Tiny Local Test failed. Open Developer Mode for details.")
        tiny_test_state = st.session_state.get("tiny_local_test")
        if tiny_test_state:
            if tiny_test_state.get("ok"):
                st.sidebar.caption("Last Tiny Local Test succeeded.")
            elif tiny_test_state.get("error"):
                if developer_mode:
                    st.sidebar.caption(f"Last Tiny Local Test error: {tiny_test_state.get('error')}")
                else:
                    st.sidebar.caption("Last Tiny Local Test failed. Open Developer Mode for details.")
        return {
            "mode": mode,
            "provider_choice": LOCAL_PROVIDER_KEY,
            "provider_label": "Local Model",
            "model": discovery["selected_model"],
            "model_source": discovery["selected_model_source"],
            "api_key": "",
            "temperature": temperature,
            "base_url": base_url,
            "discovery": discovery,
            "fast_local_draft": fast_local_draft,
            "fast_local_evidence_cap": local_evidence_cap,
            "local_compact_prompt_mode": local_compact_prompt_mode,
            "local_compact_evidence_chars": local_compact_evidence_chars,
            "local_section_generation_mode": local_section_generation_mode,
            "prompt_estimate": prompt_estimate,
        }

    return {
        "mode": "demo",
        "provider_choice": "none",
        "provider_label": None,
        "model": "",
        "model_source": "manual",
        "api_key": "",
        "temperature": 0.3,
        "base_url": None,
        "discovery": None,
    }


def build_optional_provider_config(provider_choice: str, model: str, api_key: str, temperature: float, base_url: str | None = None):
    if provider_choice == "none":
        return None
    config = resolve_generation_config(
        mode="ai" if provider_choice != LOCAL_PROVIDER_KEY else "local",
        provider_choice=provider_choice,
        model=model,
        api_key=api_key,
        base_url=base_url or "",
        temperature=temperature,
    )
    return config.to_provider_config()


def _badge(label: str, bg: str, fg: str = "#ffffff") -> str:
    return (
        f"<span style='display:inline-block;padding:0.22rem 0.6rem;border-radius:999px;"
        f"background:{bg};color:{fg};font-weight:700;font-size:0.8rem;margin-right:0.4rem;'>"
        f"{label}</span>"
    )


def _section_title(label: str, color: str, icon: str = "•") -> str:
    return (
        f"<div class='pmono-card-title' style='color:{color};'>"
        f"<span>{icon}</span><span>{label}</span></div>"
    )


def _theme_styles(theme: str) -> str:
    palettes = {
        "System Default": {
            "bg": "#f5f7fa",
            "sidebar_bg": "#ffffff",
            "panel": "#ffffff",
            "panel_alt": "#f0f7ff",
            "input_bg": "#ffffff",
            "button_bg": "#2563eb",
            "button_bg_hover": "#1d4ed8",
            "text": "#0f172a",
            "muted": "#64748b",
            "border": "#d6deeb",
            "accent": "#2563eb",
            "accent_hover": "#1d4ed8",
            "success": "#16a34a",
            "warning": "#d97706",
            "error": "#dc2626",
        },
        "Light Mode": {
            "bg": "#f5f7fa",
            "sidebar_bg": "#ffffff",
            "panel": "#ffffff",
            "panel_alt": "#f0f7ff",
            "input_bg": "#ffffff",
            "button_bg": "#2563eb",
            "button_bg_hover": "#1d4ed8",
            "text": "#0f172a",
            "muted": "#64748b",
            "border": "#d6deeb",
            "accent": "#2563eb",
            "accent_hover": "#1d4ed8",
            "success": "#16a34a",
            "warning": "#d97706",
            "error": "#dc2626",
        },
        "Dark Mode": {
            "bg": "#0f172a",
            "sidebar_bg": "#0b1220",
            "panel": "#111827",
            "panel_alt": "#1e293b",
            "input_bg": "#111827",
            "button_bg": "#1e293b",
            "button_bg_hover": "#334155",
            "text": "#f8fafc",
            "muted": "#cbd5e1",
            "border": "#334155",
            "accent": "#60a5fa",
            "accent_hover": "#93c5fd",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "error": "#f87171",
        },
    }
    palette = palettes.get(theme, palettes["System Default"])
    return f"""
    <style>
        :root {{
            --pmono-bg: {palette["bg"]};
            --pmono-sidebar-bg: {palette["sidebar_bg"]};
            --pmono-panel: {palette["panel"]};
            --pmono-panel-alt: {palette["panel_alt"]};
            --pmono-input-bg: {palette["input_bg"]};
            --pmono-button-bg: {palette["button_bg"]};
            --pmono-button-bg-hover: {palette["button_bg_hover"]};
            --pmono-text: {palette["text"]};
            --pmono-muted: {palette["muted"]};
            --pmono-border: {palette["border"]};
            --pmono-accent: {palette["accent"]};
            --pmono-accent-hover: {palette["accent_hover"]};
            --pmono-success: {palette["success"]};
            --pmono-warning: {palette["warning"]};
            --pmono-error: {palette["error"]};
        }}
        .stApp {{
            background: var(--pmono-bg);
            color: var(--pmono-text);
            font-size: 17px;
            line-height: 1.6;
        }}
        .stApp, .stApp p, .stApp li, .stApp div, .stApp label, .stApp span {{
            color: var(--pmono-text);
        }}
        .stApp h1 {{ font-size: 2.55rem; line-height: 1.12; margin-bottom: 0.35rem; font-weight: 800; }}
        .stApp h2 {{ font-size: 1.65rem; line-height: 1.2; font-weight: 750; }}
        .stApp h3 {{ font-size: 1.25rem; line-height: 1.22; font-weight: 700; }}
        .stApp p, .stApp li {{ font-size: 1.02rem; }}
        .stApp a {{ color: var(--pmono-accent); }}
        [data-testid="stSidebar"] {{
            background: var(--pmono-sidebar-bg);
            border-right: 1px solid var(--pmono-border);
            color: var(--pmono-text);
            box-shadow: 8px 0 24px rgba(15, 23, 42, 0.03);
        }}
        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] div {{
            color: var(--pmono-text);
            font-size: 1.0rem;
        }}
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stTextInput,
        [data-testid="stSidebar"] .stPasswordInput,
        [data-testid="stSidebar"] .stTextArea,
        [data-testid="stSidebar"] .stNumberInput,
        [data-testid="stSidebar"] .stSlider,
        [data-testid="stSidebar"] .stButton,
        [data-testid="stSidebar"] .stCheckbox,
        [data-testid="stSidebar"] .stRadio,
        [data-testid="stSidebar"] .stToggle {{
            color: var(--pmono-text);
        }}
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] [data-baseweb="input"] input,
        [data-testid="stSidebar"] [data-baseweb="textarea"] textarea {{
            background-color: var(--pmono-input-bg) !important;
            color: var(--pmono-text) !important;
            border-color: var(--pmono-border) !important;
            caret-color: var(--pmono-accent);
            border-radius: 10px !important;
            box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background-color: var(--pmono-input-bg) !important;
            color: var(--pmono-text) !important;
            border-color: var(--pmono-border) !important;
            border-radius: 10px !important;
            min-height: 2.85rem;
        }}
        [data-testid="stSidebar"] [role="combobox"] {{
            background-color: var(--pmono-input-bg) !important;
            color: var(--pmono-text) !important;
            border-radius: 10px !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div,
        [data-testid="stSidebar"] [data-testid="stTextInput"] > div,
        [data-testid="stSidebar"] [data-testid="stPasswordInput"] > div {{
            background-color: transparent;
        }}
        [data-testid="stSidebar"] button {{
            background: var(--pmono-button-bg) !important;
            color: #ffffff !important;
            border: 1px solid var(--pmono-button-bg) !important;
            box-shadow: 0 8px 16px rgba(37, 99, 235, 0.14) !important;
            font-size: 0.98rem !important;
            min-height: 2.8rem;
            border-radius: 10px !important;
        }}
        [data-testid="stSidebar"] button:hover {{
            background: var(--pmono-button-bg-hover) !important;
            border-color: var(--pmono-accent-hover) !important;
        }}
        [data-testid="stSidebar"] button:disabled {{
            background: color-mix(in srgb, var(--pmono-button-bg) 35%, white 65%) !important;
            color: var(--pmono-muted) !important;
            border-color: var(--pmono-border) !important;
            opacity: 0.9;
        }}
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        [data-testid="stSidebar"] .stHelp {{
            color: var(--pmono-muted) !important;
        }}
        [data-testid="stSidebar"] .stExpander {{
            background: var(--pmono-panel);
            border: 1px solid var(--pmono-border);
            border-radius: 12px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.04);
        }}
        [data-testid="stSidebar"] .stExpander summary,
        [data-testid="stSidebar"] .streamlit-expanderHeader {{
            color: var(--pmono-text) !important;
            font-weight: 700;
        }}
        [data-testid="stTabs"] button {{
            font-size: 1.02rem !important;
            padding-top: 0.75rem !important;
            padding-bottom: 0.75rem !important;
            padding-left: 0.95rem !important;
            padding-right: 0.95rem !important;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stPasswordInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stNumberInput"] input {{
            font-size: 1.03rem !important;
            min-height: 3rem;
        }}
        [data-testid="stSlider"] {{
            padding-top: 0.1rem;
            padding-bottom: 0.2rem;
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 6rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: none;
        }}
        .pmono-footer {{
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 999;
            padding: 0.85rem 1rem;
            border-top: 1px solid rgba(255,255,255,0.12);
            background: #0f172a;
            color: rgba(255,255,255,0.92);
            font-size: 0.95rem;
            text-align: center;
            box-shadow: 0 -10px 24px rgba(15, 23, 42, 0.24);
        }}
        .pmono-footer strong {{
            color: #ffffff;
        }}
        .pmono-section-card {{
            border: 1px solid var(--pmono-border);
            background: var(--pmono-panel);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.04);
        }}
        .pmono-bullets {{
            margin: 0.25rem 0 0.55rem 1.15rem;
        }}
        .pmono-bullets li {{
            margin-bottom: 0.2rem;
        }}
        .pmono-callout {{
            border-left: 4px solid var(--pmono-accent);
            background: var(--pmono-panel-alt);
            border-radius: 10px;
            padding: 0.9rem 1rem;
            margin: 0.7rem 0;
        }}
        .stButton button, .stDownloadButton button {{
            background: var(--pmono-button-bg);
            color: #ffffff;
            border: 1px solid var(--pmono-button-bg);
            box-shadow: 0 10px 18px rgba(37, 99, 235, 0.12);
            border-radius: 10px;
            min-height: 2.85rem;
            font-size: 1.0rem;
        }}
        .stButton button:hover, .stDownloadButton button:hover {{
            background: var(--pmono-button-bg-hover);
            border-color: var(--pmono-accent);
        }}
        .stButton button:focus-visible,
        .stDownloadButton button:focus-visible,
        [data-testid="stSidebar"] button:focus-visible,
        [data-testid="stSidebar"] input:focus-visible,
        [data-testid="stSidebar"] textarea:focus-visible,
        [data-testid="stSidebar"] [role="combobox"]:focus-visible {{
            outline: 2px solid var(--pmono-accent);
            outline-offset: 2px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 12px !important;
            border: 1px solid var(--pmono-border) !important;
            background: var(--pmono-panel) !important;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06) !important;
            padding: 0.95rem 1rem !important;
            margin-bottom: 0.8rem !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: transparent !important;
        }}
        .pmono-card-title {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.18rem;
            font-weight: 800;
            margin-bottom: 0.7rem;
            padding-bottom: 0.25rem;
        }}
        .pmono-card-title::before {{
            content: "";
            display: inline-block;
            width: 0.65rem;
            height: 0.65rem;
            border-radius: 999px;
            background: currentColor;
        }}
        .pmono-blue {{ color: #2563eb; }}
        .pmono-purple {{ color: #7c3aed; }}
        .pmono-green {{ color: #16a34a; }}
        .pmono-orange {{ color: #d97706; }}
        .pmono-teal {{ color: #0f766e; }}
        .pmono-red {{ color: #dc2626; }}
        .pmono-status-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 700;
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
        }}
        .pmono-chip-blue {{ background: rgba(37, 99, 235, 0.12); color: #1d4ed8; }}
        .pmono-chip-purple {{ background: rgba(124, 58, 237, 0.12); color: #6d28d9; }}
        .pmono-chip-green {{ background: rgba(22, 163, 74, 0.12); color: #15803d; }}
        .pmono-chip-orange {{ background: rgba(217, 119, 6, 0.12); color: #b45309; }}
        .pmono-chip-teal {{ background: rgba(15, 118, 110, 0.12); color: #0f766e; }}
        .pmono-chip-red {{ background: rgba(220, 38, 38, 0.12); color: #b91c1c; }}
    </style>
    """


def _validation_human_report(validation: dict) -> str:
    score = float(validation.get("overall_compliance_score", 0) or 0)
    sections_validated = validation.get("sections_validated", 0)
    sections_compliant = validation.get("sections_compliant", 0)
    missing = validation.get("mandatory_sections_missing", [])
    critical = validation.get("critical_issues", [])
    status = validation.get("status", "UNKNOWN")
    parts = [
        f"Overall compliance score: {score:.1f}%",
        f"Status: {status}",
        f"Sections compliant: {sections_compliant}/{sections_validated}",
    ]
    if missing:
        parts.append("Missing mandatory sections: " + ", ".join(str(item).replace("_", " ").title() for item in missing))
    if critical:
        parts.append("Critical issues: " + "; ".join(str(item) for item in critical))
    return " | ".join(parts)


def _render_placeholder_cards(placeholders: dict) -> None:
    if not placeholders:
        st.caption("No draft placeholders.")
        return
    for bucket, items in placeholders.items():
        st.markdown(f"**{bucket.replace('_', ' ').title()}**")
        for item in items:
            st.info(f"{item.get('label', 'Placeholder')}\n\n{item.get('instruction', '')}")


def _render_validation_scorecards(monograph: dict, developer_mode: bool) -> None:
    validation = monograph.get("validation", {}) or {}
    score = float(validation.get("overall_compliance_score", 0) or 0)
    sections_validated = int(validation.get("sections_validated", 0) or 0)
    sections_compliant = int(validation.get("sections_compliant", 0) or 0)
    critical_issues = validation.get("critical_issues", []) or []
    missing = validation.get("mandatory_sections_missing", []) or []
    status = validation.get("status", "UNKNOWN")
    status_chip = {
        "PASS": ("✅ Validation Passed", "#16a34a", "#ffffff"),
        "FAIL": ("❌ Validation Needs Review", "#dc2626", "#ffffff"),
    }.get(status, (f"⚠ Validation {status.title()}", "#d97706", "#ffffff"))

    st.markdown(_badge(status_chip[0], status_chip[1], status_chip[2]), unsafe_allow_html=True)
    cols = st.columns(4)
    cols[0].metric("Overall compliance", f"{score:.1f}%")
    cols[1].metric("Sections compliant", f"{sections_compliant}/{sections_validated}")
    cols[2].metric("Critical issues", len(critical_issues))
    cols[3].metric("Missing sections", len(missing))

    if status == "PASS":
        st.success("Validation passed. The monograph is structurally complete and within the expected compliance range.")
    else:
        st.warning("Validation identified gaps. Review the section cards below before export or distribution.")

    st.markdown("**Human-readable validation report**")
    st.write(_validation_human_report(validation))

    details = validation.get("section_details", {}) or {}
    if details:
        st.markdown("**Section status indicators**")
        keys = list(details.keys())
        for row_start in range(0, len(keys), 2):
            cols = st.columns(2)
            for idx, section_name in enumerate(keys[row_start:row_start + 2]):
                detail = details[section_name]
                with cols[idx]:
                    section_score = float(detail.get("compliance_score", 0) or 0)
                    section_status = detail.get("status", "UNKNOWN")
                    issues = detail.get("issues", []) or []
                    st.markdown(
                        _badge(
                            f"{section_name.replace('_', ' ').title()} - {section_status}",
                            "#d9f2dd" if section_status == "PASS" else "#fff0d9",
                            "#174d25" if section_status == "PASS" else "#7a4e00",
                        ),
                        unsafe_allow_html=True,
                    )
                    st.metric("Section score", f"{section_score:.1f}%")
                    if issues:
                        for issue in issues:
                            st.warning(issue)
                    else:
                        st.caption("No issues detected.")

    if developer_mode:
        with st.expander("Developer validation internals", expanded=False):
            st.json(validation)


def _render_evidence_panel(evidence_package: dict | None, developer_mode: bool) -> None:
    if not evidence_package:
        st.caption("No live evidence package available yet.")
        return

    summary = evidence_package.get("summary", {}) or {}
    source_status = evidence_package.get("source_status", {}) or {}
    limitations = evidence_package.get("limitations", []) or []
    source_errors = evidence_package.get("source_errors", []) or []
    cache_status = evidence_package.get("cache_status", {}) or {}
    source_issues = _evidence_source_issue_items(evidence_package)
    local_records = list((evidence_package.get("sources", {}) or {}).get("local", []) or [])

    st.markdown("**Evidence retrieval summary**")
    cols = st.columns(5)
    cols[0].metric("Local", str(summary.get("local_count", len(local_records))))
    cols[1].metric("PubMed", str(summary.get("pubmed_count", 0)))
    cols[2].metric("FDA", str(summary.get("fda_count", 0)))
    cols[3].metric("EMA", str(summary.get("ema_count", 0)))
    cols[4].metric("ClinicalTrials.gov", str(summary.get("clinicaltrials_count", 0)))

    status_bits = []
    for source_name in ("local", "pubmed", "fda", "ema", "clinicaltrials"):
        status = _discovery_get(source_status.get(source_name), "status", "unknown")
        count = _discovery_get(source_status.get(source_name), "count", 0)
        source_label = EVIDENCE_SOURCE_LABELS[source_name]
        status_bits.append(f"- {source_label}: {status} ({count})")
    st.markdown("\n".join(status_bits))

    if local_records:
        local_summary = evidence_package.get("retrieved_with", {}).get("local_vault_summary", {}) or {}
        file_names = local_summary.get("file_names", []) or [record.get("source_name") or record.get("title") for record in local_records]
        total_words = local_summary.get("word_count")
        if total_words is None:
            total_words = sum(int((record.get("metadata", {}) or {}).get("word_count", 0) or 0) for record in local_records)
        st.info(
            f"Local Evidence Vault loaded {len(local_records)} file(s) with {total_words} extracted word(s)."
        )
        if file_names:
            st.caption("Local files: " + ", ".join(file_names[:8]) + ("..." if len(file_names) > 8 else ""))
        if local_summary.get("source_errors"):
            if developer_mode:
                st.caption("Local parsing errors are available in Developer Mode.")
            else:
                st.info("Some local files had parsing errors. Open Developer Mode to review details.")
        if developer_mode:
            with st.expander("Developer local evidence details", expanded=False):
                st.json(
                    {
                        "local_vault_summary": local_summary,
                        "local_records": local_records,
                    }
                )
def main() -> None:
    if st is None:
        raise RuntimeError(
            "Streamlit is required to run this app. Install the requirements and retry."
        )

    st.set_page_config(page_title=APP_NAME, layout="wide")

    theme_name = st.sidebar.selectbox(
        "Theme",
        ["System Default", "Light Mode", "Dark Mode"],
        index=0,
        key="app_theme",
    )
    st.markdown(_theme_styles(theme_name), unsafe_allow_html=True)

    st.title(APP_NAME)
    st.caption(APP_TAGLINE)
    st.info(MEDICAL_DISCLAIMER)
    if APP_VERSION or APP_BUILD:
        version_bits = [bit for bit in (APP_VERSION, APP_BUILD) if bit]
        st.caption(" | ".join(version_bits))

    st.sidebar.header("Configuration")
    developer_mode = st.sidebar.checkbox("Developer Mode", value=False, key="developer_mode")
    generation_mode_label = st.sidebar.radio(
        "Generation mode",
        list(MODE_LABELS.keys()),
        index=1,
        key="generation_mode_label",
    )
    generation_mode = MODE_LABELS[generation_mode_label]
    if st.session_state.get("active_generation_mode") != generation_mode:
        _clear_generation_runtime_state()
    st.session_state["active_generation_mode"] = generation_mode

    molecule_name = st.sidebar.text_input(
        "Molecule name",
        value=st.session_state.get("molecule_name_input", ""),
        key="molecule_name_input",
        placeholder="e.g. Metformin",
    ).strip()
    st.session_state["molecule_name"] = molecule_name

    specialty = st.sidebar.selectbox(
        "Target specialty",
        ["General Practitioner", "Cardiologist", "Endocrinologist", "Rheumatologist", "Neurologist"],
        index=0,
        key="specialty",
    )

    max_results = st.sidebar.slider("Max research results", 5, 60, 20, key="max_results")
    clean_markdown = st.sidebar.checkbox("Clean markdown artifacts", value=True, key="clean_markdown")
    use_fallback = st.sidebar.checkbox(
        "Use fallback generation when no provider is supplied",
        value=True,
        key="use_fallback",
    )
    st.sidebar.caption(
        "Local evidence files stay local and are only used in the selected model call."
    )

    uploaded_files = st.sidebar.file_uploader(
        "Local Evidence Vault",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "md", "csv", "xlsx", "html", "htm"],
        key="local_evidence_uploads",
    )
    local_folder_text = st.sidebar.text_area(
        "Local evidence folder paths (one per line)",
        height=90,
        key="local_evidence_folders",
        placeholder=r"D:\evidence\folder",
    )
    local_folder_paths = [line.strip() for line in local_folder_text.splitlines() if line.strip()]

    provider_controls: dict = {}
    if generation_mode == "ai":
        provider_controls = _render_provider_mode_controls("ai", "monograph", developer_mode)
    elif generation_mode == "local":
        provider_controls = _render_provider_mode_controls("local", "monograph", developer_mode)
    else:
        st.sidebar.subheader("Demo Mode")
        st.sidebar.caption("Deterministic fallback data is used in Demo Mode.")
        provider_controls = {
            "mode": "demo",
            "provider_choice": "none",
            "provider_label": None,
            "model": "",
            "model_source": "manual",
            "api_key": "",
            "temperature": 0.3,
            "base_url": None,
            "discovery": None,
        }
        _render_temperature_controls("monograph", "demo")

    if provider_controls.get("discovery") and provider_controls["discovery"].get("warning"):
        warning_text = _discovery_warning_to_text(provider_controls["discovery"].get("warning"), developer_mode)
        if warning_text:
            st.sidebar.warning(warning_text)

    generation_config = resolve_generation_config(
        mode=generation_mode,
        provider_choice=provider_controls.get("provider_choice", "none"),
        model=provider_controls.get("model", "") or "",
        api_key=provider_controls.get("api_key", "") or "",
        base_url=provider_controls.get("base_url", "") or "",
        max_research_articles=max_results,
        temperature=float(provider_controls.get("temperature", 0.3) or 0.3),
    )
    if generation_mode == "local":
        generation_config.local_compact_prompt_mode = bool(provider_controls.get("local_compact_prompt_mode", True))
        generation_config.local_section_generation_mode = bool(provider_controls.get("local_section_generation_mode", True))
        generation_config.local_compact_evidence_chars = int(provider_controls.get("local_compact_evidence_chars", 3000) or 3000)
        generation_config.max_research_articles = int(provider_controls.get("fast_local_evidence_cap", max_results) or max_results)
        generation_config.max_completion_tokens = 128 if bool(provider_controls.get("fast_local_draft", True)) else 192
    generation_config.max_research_articles = min(generation_config.max_research_articles, max_results)

    if generation_config.notes and developer_mode:
        with st.sidebar.expander("Generation config notes", expanded=False):
            st.json(generation_config.model_dump())
    elif generation_config.blocked_reason and not developer_mode:
        st.sidebar.caption(_discovery_warning_to_text(generation_config.blocked_reason, developer_mode=False))

    prompt_estimate = _estimate_local_prompt_tokens(
        molecule_name,
        st.session_state.get("local_evidence_summary"),
        bool(getattr(generation_config, "local_compact_prompt_mode", False)),
        int(getattr(generation_config, "local_compact_evidence_chars", 3000) or 3000),
        int(provider_controls.get("fast_local_evidence_cap", 5) or 5),
        bool(getattr(generation_config, "local_section_generation_mode", False)),
    )
    if generation_mode == "local":
        st.sidebar.caption(
            f"Estimated prompt: ~{prompt_estimate['estimated_prompt_tokens']} tokens "
            f"(~{prompt_estimate['estimated_prompt_characters']} chars)."
        )

    tab_generate, tab_audit, tab_history, tab_about, tab_help = st.tabs(
        ["Generate Monograph", "Audit Agents", "History", "About", "Help"]
    )

    def _render_export_buttons(monograph: dict, exports: dict) -> None:
        file_map = {
            "json": ("Download JSON", "application/json", ".json"),
            "markdown": ("Download Markdown", "text/markdown", ".md"),
            "pdf": ("Download PDF", "application/pdf", ".pdf"),
            "word": ("Download DOCX", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
            "xlsx": ("Download XLSX", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
            "print_ready": ("Download Print-ready HTML", "text/html", ".html"),
            "google_docs": ("Download Google Docs Template", "text/plain", ".txt"),
        }
        for key, (label, mime, suffix) in file_map.items():
            value = exports.get(key)
            if not value:
                error_key = f"{key}_error"
                if developer_mode and exports.get(error_key):
                    st.warning(f"{label} export failed: {exports[error_key]}")
                continue
            path = Path(value)
            if path.exists():
                data = path.read_bytes()
                file_name = path.name
            else:
                data = str(value).encode("utf-8")
                file_name = f"{monograph.get('molecule_name', 'monograph')}{suffix}"
            st.download_button(
                label,
                data=data,
                file_name=file_name,
                mime=mime,
                key=f"{key}_{monograph.get('history_id', 'current')}",
            )
            if developer_mode:
                st.caption(str(path) if path.exists() else file_name)

    def _render_monograph(monograph: dict) -> None:
        st.subheader(f"Structured sections for {monograph['molecule_name']}")
        st.info(monograph.get("generation_label", "Draft"))
        if monograph.get("generation_mode") == "ai":
            st.markdown(_badge("AI-generated draft for expert review", "#2c5aa0"), unsafe_allow_html=True)
        elif monograph.get("generation_mode") == "local":
            st.markdown(_badge("Local model draft generated using retrieved evidence package", "#0f6b3a"), unsafe_allow_html=True)
        else:
            st.markdown(_badge("Demo draft generated from fallback/sample data", "#8a5b00"), unsafe_allow_html=True)

        validation_status = monograph.get("validation", {}).get("status", "UNKNOWN")
        evidence_package_dict = st.session_state.get("evidence_package") or {}
        evidence_total = int((evidence_package_dict.get("summary", {}) or {}).get("total_records", 0) or 0)
        chips = []
        if monograph.get("generation_mode") == "ai":
            chips.append(_badge("?? AI Mode Active", "#2563eb"))
        elif monograph.get("generation_mode") == "local":
            chips.append(_badge("?? Local Model Active", "#0f766e"))
        else:
            chips.append(_badge("?? Demo Mode Active", "#d97706"))
        chips.append(_badge("?? Evidence Retrieved" if evidence_total > 0 else "? Evidence Limited", "#16a34a" if evidence_total > 0 else "#d97706"))
        if validation_status == "PASS":
            chips.append(_badge("? Validation Passed", "#16a34a"))
        elif validation_status == "FAIL":
            chips.append(_badge("? Generation Failed", "#dc2626"))
        else:
            chips.append(_badge("? Validation Review Needed", "#d97706"))
        st.markdown("".join(chips), unsafe_allow_html=True)

        cols = st.columns(2)
        with cols[0]:
            st.metric("Validation score", f"{monograph.get('validation', {}).get('overall_compliance_score', 0):.1f}%")
        with cols[1]:
            st.metric("Total tokens", monograph.get("total_tokens_used", 0))

        st.markdown(_section_title("Validation Summary", "#d97706", "??"), unsafe_allow_html=True)
        _render_validation_scorecards(monograph, developer_mode)
        st.markdown(_section_title("Evidence Retrieval Status", "#16a34a", "??"), unsafe_allow_html=True)
        _render_evidence_panel(st.session_state.get("evidence_package"), developer_mode)

        if developer_mode and monograph.get("evidence_traceability"):
            with st.expander("Source Mapping Viewer", expanded=False):
                st.dataframe(monograph["evidence_traceability"], use_container_width=True)
        if developer_mode and monograph.get("provider_request_diagnostics"):
            with st.expander("Provider Request Diagnostics", expanded=False):
                st.caption("Shows the exact payload and request details sent to the model endpoint.")
                for diagnostic in monograph["provider_request_diagnostics"]:
                    st.markdown(f"**Section:** {diagnostic.get('section', 'unknown')}")
                    st.json(diagnostic.get("request_diagnostics", {}))
        if developer_mode and st.session_state.get("tiny_local_test"):
            with st.expander("Tiny Local Test Diagnostics", expanded=False):
                st.caption("This local-only probe helps distinguish prompt construction from provider integration.")
                st.json(st.session_state.get("tiny_local_test"))

        if monograph.get("draft_placeholders"):
            st.markdown("**Draft placeholders**")
            _render_placeholder_cards(monograph["draft_placeholders"])

        for section_name, section_content in monograph.get("sections", {}).items():
            with st.expander(section_name.replace("_", " ").title(), expanded=False):
                st.markdown(section_content)

        if monograph.get("executive_summary"):
            with st.expander("Executive summary", expanded=False):
                st.markdown(monograph["executive_summary"])

        st.info("Preparing exports")
        try:
            exports = export_service.export_bundle(monograph)
        except Exception as exc:
            exports = {}
            _report_exception("Export bundle failed", exc, developer_mode, severity="warning")

        st.markdown(_section_title("Export Options", "#0f766e", "??"), unsafe_allow_html=True)
        if not _has_export_downloads(exports):
            st.warning("No export files were prepared.")
        _render_export_buttons(monograph, exports)

    with tab_generate:
        st.subheader("Generate a product monograph")
        st.caption("Generate demo, AI, or local model drafts with live evidence retrieval and graceful fallback handling.")

        reset_cols = st.columns([1, 1, 4])
        with reset_cols[0]:
            if st.button("Reset generation state", key="reset_generation_state_button"):
                _clear_generation_runtime_state()
                st.rerun()

        pending_generation_request = _restore_pending_generation_request(
            st.session_state.get("pending_generation_request")
        )
        if pending_generation_request:
            st.caption("A pending generation request is queued and will resume automatically.")

        generation_requested = st.button("Generate monograph", type="primary", key="generate_monograph_button")
        if pending_generation_request or st.session_state.get("resume_generation_requested"):
            generation_requested = True

        generation_allowed = True
        force_refresh = bool(st.session_state.get("evidence_refresh_requested"))
        status_slot = st.sidebar.empty()

        if generation_requested:
            st.session_state["last_generation_error"] = None
            st.session_state["generated_monograph"] = None
            st.session_state["generated_sources"] = None
            st.session_state["evidence_package"] = None
            if not molecule_name:
                st.error("Enter a molecule name.")
                generation_allowed = False
            elif generation_config.blocked:
                st.error(generation_config.blocked_reason or "Generation is blocked for the current configuration.")
                if developer_mode and generation_config.notes:
                    st.caption("; ".join(generation_config.notes))
                generation_allowed = False
            else:
                progress_panel = st.container()
                try:
                    progress_panel.info("Starting generation")
                    if pending_generation_request:
                        st.session_state.pop("pending_generation_request", None)
                        pending_config = pending_generation_request["generation_config"]
                        if isinstance(pending_config, GenerationConfig):
                            generation_config = pending_config
                        molecule_name = pending_generation_request["molecule_name"] or molecule_name
                        specialty = pending_generation_request["specialty"] or specialty
                        generation_sources = pending_generation_request["generation_sources"] or {}
                        evidence_package = pending_generation_request["evidence_package"] or {}
                        local_result = pending_generation_request.get("local_evidence_result", {})
                        local_summary = pending_generation_request.get("local_evidence_summary", {}) or {}
                        source_issues = pending_generation_request.get("source_issues", []) or []
                        evidence_dict = generation_sources
                        status_slot.info("Resuming pending generation request.")
                    elif generation_mode == "demo":
                        status_slot.info("Building demo evidence package.")
                        evidence_package = sample_evidence_package(molecule_name)
                        generation_sources = sample_sources(molecule_name)
                        local_result = {"count": 0}
                        local_summary = {
                            "files_loaded": 0,
                            "file_names": [],
                            "word_count": 0,
                            "source_errors": [],
                            "extraction_details": [],
                            "include_full_paths": False,
                        }
                        source_issues = []
                        evidence_dict = evidence_package
                        st.session_state["local_evidence_summary"] = local_summary
                    else:
                        status_slot.info("Retrieving evidence")
                        evidence_package = evidence_orchestrator.retrieve_evidence(
                            molecule_name,
                            max_results=int(generation_config.max_research_articles or max_results),
                            force_refresh=force_refresh,
                        )
                        local_result, local_summary = collect_local_evidence(
                            uploaded_files,
                            local_folder_paths,
                            include_full_paths=developer_mode,
                        )
                        st.session_state["local_evidence_summary"] = local_summary
                        if local_result.count or local_summary.get("source_errors") or uploaded_files or local_folder_paths:
                            evidence_package = merge_local_evidence_package(
                                evidence_package,
                                local_result,
                                local_summary,
                                include_local_evidence_in_references=True,
                            )
                        evidence_dict = evidence_package.model_dump()
                        source_issues = _evidence_source_issue_items(evidence_dict)
                        total_records = int(evidence_dict.get("summary", {}).get("total_records", 0) or 0)
                        confirm_proceed = bool(
                            st.session_state.get("proceed_limited_evidence")
                            or st.session_state.get("no_evidence_confirmation_pending")
                        )
                        if (source_issues or total_records == 0) and not confirm_proceed:
                            st.warning("Some evidence sources were unavailable. Generation can continue using available evidence.")
                            if not developer_mode:
                                available_sources = _available_evidence_source_labels(evidence_dict)
                                if available_sources:
                                    st.success("Generation can continue using available evidence:\n" + "\n".join(available_sources))
                            for issue in source_issues:
                                _display_evidence_issue(issue, developer_mode)
                            action_cols = st.columns(3)
                            pending_payload = _build_pending_generation_request(
                                molecule_name=molecule_name,
                                specialty=specialty,
                                generation_config=generation_config,
                                generation_sources=evidence_dict,
                                evidence_package=evidence_package,
                                local_evidence_result=local_result,
                                local_evidence_summary=local_summary,
                                source_issues=source_issues,
                            )
                            if total_records == 0:
                                if action_cols[0].button("Continue without evidence", key="continue_without_evidence_inline"):
                                    st.session_state["pending_generation_request"] = pending_payload
                                    _set_session_flag("no_evidence_confirmation_pending", True)
                                    _set_session_flag("resume_generation_requested", True)
                                    st.session_state["generation_stage"] = "awaiting_confirmation"
                                    st.rerun()
                                if action_cols[1].button("Cancel generation", key="cancel_generation_inline"):
                                    _clear_generation_runtime_state()
                                    st.rerun()
                            else:
                                if action_cols[0].button("Retry failed sources", key="retry_failed_sources_inline"):
                                    st.session_state["pending_generation_request"] = pending_payload
                                    _set_session_flag("evidence_refresh_requested", True)
                                    _set_session_flag("resume_generation_requested", True)
                                    st.session_state["generation_stage"] = "refreshing_evidence"
                                    st.rerun()
                                if action_cols[1].button("Proceed with available evidence", key="proceed_available_evidence_inline"):
                                    st.session_state["pending_generation_request"] = pending_payload
                                    _set_session_flag("proceed_limited_evidence", True)
                                    _set_session_flag("resume_generation_requested", True)
                                    st.session_state["generation_stage"] = "awaiting_confirmation"
                                    st.rerun()
                                if action_cols[2].button("Cancel generation", key="cancel_generation_partial_inline"):
                                    _clear_generation_runtime_state()
                                    st.rerun()
                            generation_allowed = False
                        else:
                            if generation_mode == "local" and bool(getattr(generation_config, "local_compact_prompt_mode", False)):
                                generation_sources = _prepare_local_compact_sources(
                                    evidence_dict,
                                    compact_prompt_mode=bool(getattr(generation_config, "local_compact_prompt_mode", False)),
                                    compact_evidence_chars=int(getattr(generation_config, "local_compact_evidence_chars", 3000) or 3000),
                                    compact_records=int(provider_controls.get("fast_local_evidence_cap", max_results) or max_results),
                                    section_generation_mode=bool(getattr(generation_config, "local_section_generation_mode", False)),
                                )
                            else:
                                generation_sources = evidence_dict

                    if generation_allowed:
                        st.session_state["generation_stage"] = "generating"
                        status_slot.info("Generating monograph")
                        provider_cfg = generation_config.to_provider_config()
                        monograph = synthesis_engine.generate_monograph(
                            molecule_name,
                            generation_sources,
                            provider_cfg,
                        )
                        st.session_state.update(_generated_monograph_state(monograph, generation_sources, evidence_package))
                        st.session_state["generation_stage"] = "rendering"
                        status_slot.info("Rendering output")

                        try:
                            monograph["executive_summary"] = executive_summary_generator.generate_executive_summary(
                                molecule_name,
                                generation_sources,
                                specialty,
                                provider_cfg,
                            )
                            monograph["generation_label"] = generation_config.output_label or monograph.get("generation_label", "Draft")
                            monograph["generation_mode"] = generation_config.mode
                            monograph["draft_placeholders"] = build_draft_placeholders(molecule_name)
                            monograph["evidence_package"] = generation_sources.get("evidence_package", evidence_dict)
                            monograph["evidence_summary"] = generation_sources.get("summary", evidence_dict.get("summary", {}))
                            monograph["traceability_appendix"] = monograph.get("sections", {}).get("evidence_traceability_appendix", "")
                            monograph["evidence_traceability"] = monograph.get("evidence_traceability", [])

                            if clean_markdown:
                                for key, value in list(monograph["sections"].items()):
                                    monograph["sections"][key] = markdown_cleaner.clean_text(value)

                            validation_input = {
                                "molecule_name": monograph["molecule_name"],
                                **monograph["sections"],
                                "traceability_appendix": monograph.get("traceability_appendix", ""),
                            }
                            is_valid, validation_report = validator.validate_and_score(validation_input)
                            monograph["validation"] = validation_report
                            monograph["is_valid_for_delivery"] = is_valid

                            history_id = output_history.log_generation(monograph)
                            monograph["history_id"] = history_id

                            st.session_state.update(_generated_monograph_state(monograph, generation_sources, evidence_package))
                            st.session_state["generation_stage"] = "exports"
                            status_slot.success("Preparing exports")
                            st.success("Monograph generated.")
                        except Exception as post_exc:
                            st.session_state["last_generation_error"] = str(post_exc)
                            st.session_state["generated_monograph"] = monograph
                            st.session_state["generated_sources"] = generation_sources
                            if hasattr(evidence_package, "model_dump"):
                                st.session_state["evidence_package"] = evidence_package.model_dump()
                            else:
                                st.session_state["evidence_package"] = evidence_package or {}
                            _report_exception("Generation finalization failed", post_exc, developer_mode, severity="warning")
                        _clear_generation_flow_state()

                except Exception as exc:
                    st.session_state["last_generation_error"] = str(exc)
                    if not st.session_state.get("generated_monograph"):
                        st.session_state["generated_monograph"] = None
                        st.session_state["generated_sources"] = None
                    st.session_state["resume_generation_requested"] = False
                    st.session_state["no_evidence_confirmation_pending"] = False
                    _report_exception("Generation failed", exc, developer_mode)
                    generation_allowed = False

        if st.session_state.get("last_generation_error"):
            st.markdown(_section_title("Errors", "#dc2626", "?"), unsafe_allow_html=True)
            if developer_mode:
                st.error(f"Last generation error: {st.session_state['last_generation_error']}")
            else:
                st.error("Last generation encountered an error. Open Developer Mode for details.")

        monograph = st.session_state.get("generated_monograph")
        if _has_renderable_monograph(monograph):
            _render_monograph(monograph)
        elif generation_mode == "demo" and not generation_requested:
            st.info("Demo Mode is ready. Click Generate monograph to build a sample draft.")

    audit_provider_cfg = generation_config.to_provider_config()
    if generation_mode == "local" and audit_provider_cfg:
        audit_provider_cfg.timeout = 15.0 if bool(provider_controls.get("fast_local_draft", True)) else 30.0

    with tab_audit:
        st.subheader("Universal audit agents")
        st.caption("Provider-agnostic audit agents with safe fallback behavior.")

        audit_mode = st.radio("Audit target", ["URL", "HTML"], horizontal=True, key="audit_mode")
        target_url = st.text_input("Target URL", placeholder="https://example.com", key="audit_target_url")
        target_html = st.text_area("Target HTML", height=220, placeholder="<html>...</html>", key="audit_target_html")
        checklist_url = st.text_input(
            "Checklist URL",
            value="https://istapage.com/blog/landing-page-audit-checklist",
            key="audit_checklist_url",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Run A11Y check", key="audit_run_a11y"):
                try:
                    if audit_mode == "HTML" and target_html.strip():
                        result = check_accessibility(
                            "inline://content",
                            audit_provider_cfg,
                            fetcher=inline_fetcher(target_html, "inline://content"),
                        )
                    else:
                        result = check_accessibility(target_url.strip(), audit_provider_cfg)
                    st.session_state.last_a11y_result = result
                    st.success("Accessibility check complete.")
                except Exception as exc:
                    st.session_state.last_a11y_result = {"error": str(exc)}
                    _report_exception("Accessibility check failed", exc, developer_mode)
        with col_b:
            if st.button("Build audit schema", key="audit_build_schema"):
                try:
                    schema_result = build_audit_schema(checklist_url.strip(), audit_provider_cfg)
                    st.session_state.audit_schema = schema_result
                    st.session_state.audit_schema_id = schema_result["schema_id"]
                    st.success(f"Built schema {schema_result['schema_id']}")
                except Exception as exc:
                    st.session_state.audit_schema_error = str(exc)
                    _report_exception("Build failed", exc, developer_mode)
        with col_c:
            if st.button("Build and run audit", key="audit_build_and_run"):
                try:
                    schema_result = build_audit_schema(checklist_url.strip(), audit_provider_cfg)
                    st.session_state.audit_schema = schema_result
                    st.session_state.audit_schema_id = schema_result["schema_id"]
                    if audit_mode == "HTML" and target_html.strip():
                        audit_result = run_audit(
                            "inline://content",
                            schema_result["schema_id"],
                            audit_provider_cfg,
                            fetcher=inline_fetcher(target_html, "inline://content"),
                        )
                    else:
                        audit_result = run_audit(
                            target_url.strip(),
                            schema_result["schema_id"],
                            audit_provider_cfg,
                        )
                    st.session_state.last_audit_result = audit_result
                    st.success("Audit complete.")
                except Exception as exc:
                    st.session_state.last_audit_result = {"error": str(exc)}
                    _report_exception("Audit failed", exc, developer_mode)

        st.markdown("### Rendered accessibility review")
        st.caption("Playwright-rendered review with Axe-core support when available. Works for URLs and inline HTML.")
        rendered_target = target_url.strip()
        rendered_inline_html = audit_mode == "HTML" and bool(target_html.strip())
        if rendered_inline_html:
            rendered_target = "inline://rendered"
        if st.button("Run rendered accessibility review", key="audit_rendered_a11y"):
            try:
                if not rendered_target:
                    st.warning("Enter a Target URL or provide HTML before running the rendered accessibility review.")
                else:
                    rendered_result = run_rendered_accessibility_review(
                        rendered_target,
                        audit_provider_cfg,
                        html=target_html.strip() if rendered_inline_html else None,
                    )
                    st.session_state.last_rendered_a11y_result = rendered_result
                    if rendered_result.get("playwright_available"):
                        st.success("Rendered accessibility review complete.")
                    else:
                        st.info(rendered_result.get("summary", "Rendered accessibility review unavailable."))
            except Exception as exc:
                st.session_state.last_rendered_a11y_result = {"error": str(exc)}
                _report_exception("Rendered accessibility review failed", exc, developer_mode)

        if st.session_state.get("last_a11y_result"):
            st.subheader("A11Y result")
            if developer_mode:
                st.json(st.session_state.last_a11y_result)
            else:
                st.write(st.session_state.last_a11y_result)

        if st.session_state.get("last_rendered_a11y_result"):
            st.subheader("Rendered A11Y result")
            if developer_mode:
                st.json(st.session_state.last_rendered_a11y_result)
            else:
                st.write(st.session_state.last_rendered_a11y_result)

        if st.session_state.get("audit_schema"):
            st.subheader("Audit schema")
            schema_summary = st.session_state.audit_schema
            st.metric("Schema ID", schema_summary.get("schema_id", "unknown"))
            st.metric("Criteria", len(schema_summary.get("schema", {}).get("criteria", [])))
            st.write(schema_summary.get("source_title", "Checklist schema"))
            if developer_mode:
                with st.expander("Developer schema payload", expanded=False):
                    st.json(schema_summary)

        if st.session_state.get("last_audit_result"):
            st.subheader("Audit run result")
            if developer_mode:
                st.json(st.session_state.last_audit_result)
            else:
                st.write(st.session_state.last_audit_result)

    with tab_history:
        st.subheader("Generation history")
        try:
            summary = output_history.get_daily_summary()
            if developer_mode:
                st.json(summary)
            else:
                st.write(summary)
        except Exception as exc:
            _report_exception("History summary unavailable", exc, developer_mode, severity="warning")

    with tab_about:
        st.markdown(
            f"""
            ### About
            {APP_NAME} is a local-first drafting tool for product monographs.

            ### Notes
            - AI Mode requires a valid provider model and API key.
            - Local Model Mode uses `http://localhost:1234/v1` by default.
            - Demo Mode uses deterministic sample data.
            - Evidence retrieval falls back gracefully when a source is unavailable.
            - Export files are written locally.
            """
        )
        st.caption(APP_COPYRIGHT)
        st.code("streamlit run app.py", language="bash")
        st.code("python -m uvicorn src.agents.api.server:app --reload --port 8010", language="bash")

    with tab_help:
        st.markdown(
            """
            ### Help
            - **Modes**: Demo Mode is safe fallback data, AI Mode uses a hosted provider, and Local Model Mode targets a local OpenAI-compatible endpoint.
            - **Temperature**: Lower values are more deterministic; higher values are more varied. For medical writing, 0.2-0.3 is usually safest.
            - **Evidence retrieval**: The app merges Local Evidence Vault files with PubMed, FDA, EMA, and ClinicalTrials.gov when available.
            - **Local model**: The default endpoint is `http://localhost:1234/v1`. Use Warm up Local Model and Tiny Local Test from the sidebar.
            - **Exports**: JSON, Markdown, PDF, DOCX, XLSX, print-ready HTML, and Google Docs import templates are generated locally.
            """
        )
        st.caption(APP_COPYRIGHT)


if __name__ == "__main__":
    main()
