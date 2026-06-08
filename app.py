from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Optional

try:
    import streamlit as st
except ImportError:  # pragma: no cover - handled at runtime
    st = None

from config import APP_NAME, APP_TAGLINE, MEDICAL_DISCLAIMER
from src.agents.a11y.checker import check_accessibility
from src.agents.auditor.builder import build_audit_schema
from src.agents.auditor.runner import run_audit
from src.agents.providers.base import ProviderConfig
from src.monograph.executive_summary import executive_summary_generator
from src.monograph.generator import synthesis_engine
from src.monograph.validators import validator
from src.services.data_sources import data_manager
from src.services.export_service import export_service
from src.services.history_tracker import output_history
from src.utils.markdown_cleaner import markdown_cleaner


PROVIDER_OPTIONS = [
    "none",
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "groq",
    "openrouter",
    "openai-compatible local",
]


def build_provider_config(
    provider_name: str,
    model: str,
    api_key: str = "",
    temperature: float = 0.3,
    base_url: str = "",
) -> Optional[ProviderConfig]:
    normalized = (provider_name or "none").strip().lower()
    if normalized == "none":
        return None
    if normalized == "openai-compatible local":
        return ProviderConfig(
            provider="openai",
            model=model,
            api_key=api_key or None,
            temperature=temperature,
            base_url=base_url or None,
        )
    return ProviderConfig(
        provider=normalized,
        model=model,
        api_key=api_key or None,
        temperature=temperature,
        base_url=base_url or None,
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


def inline_fetcher(html: str, final_url: str = "inline://content"):
    def _fetcher(_: str):
        return SimpleNamespace(html=html, final_url=final_url)

    return _fetcher


def render_provider_controls(prefix: str) -> Optional[ProviderConfig]:
    st.sidebar.subheader(f"{prefix} Provider")
    provider = st.sidebar.selectbox(
        f"{prefix} provider",
        PROVIDER_OPTIONS,
        key=f"{prefix}_provider",
    )
    model = st.sidebar.text_input(
        f"{prefix} model",
        value="gpt-4o-mini" if provider == "openai" else "claude-3-5-sonnet-latest",
        key=f"{prefix}_model",
    )
    api_key = st.sidebar.text_input(
        f"{prefix} API key",
        type="password",
        key=f"{prefix}_api_key",
        help="Use a runtime key or rely on environment variables.",
    )
    temperature = st.sidebar.slider(
        f"{prefix} temperature",
        0.0,
        1.0,
        0.3,
        0.05,
        key=f"{prefix}_temperature",
    )
    base_url = ""
    if provider == "openai-compatible local":
        base_url = st.sidebar.text_input(
            f"{prefix} base URL",
            value="http://localhost:11434/v1",
            key=f"{prefix}_base_url",
            help="For API-compatible local models or proxy endpoints.",
        )
    return build_provider_config(provider, model, api_key, temperature, base_url)


def main() -> None:
    if st is None:
        raise RuntimeError(
            "Streamlit is required to run this app. Install the requirements and retry."
        )

    st.set_page_config(page_title=APP_NAME, layout="wide")

    st.title(APP_NAME)
    st.caption(APP_TAGLINE)
    st.info(MEDICAL_DISCLAIMER)

    st.sidebar.header("Configuration")
    monograph_provider = render_provider_controls("monograph")
    audit_provider = render_provider_controls("audit")

    st.sidebar.divider()
    st.sidebar.checkbox("Use fallback generation when no provider is supplied", value=True, key="use_fallback")
    st.sidebar.checkbox("Clean markdown artifacts", value=True, key="clean_markdown")
    max_results = st.sidebar.slider("Max research results", 10, 100, 30)

    tab_generate, tab_audit, tab_history, tab_about = st.tabs(
        ["Generate Monograph", "Audit Agents", "History", "About"]
    )

    with tab_generate:
        st.subheader("Generate a Product Monograph")
        molecule_name = st.text_input("Molecule name", placeholder="e.g. Metformin")
        specialty = st.selectbox(
            "Target specialty",
            ["General Practitioner", "Cardiologist", "Endocrinologist", "Rheumatologist", "Neurologist"],
        )

        if st.button("Generate monograph", type="primary"):
            if not molecule_name.strip():
                st.error("Enter a molecule name.")
            else:
                with st.spinner("Fetching sources and generating monograph..."):
                    try:
                        sources = data_manager.fetch_all_sources(molecule_name.strip(), max_results)
                        sources["formatted_text"] = data_manager.structure_for_claude(sources)
                    except Exception as exc:
                        st.warning(f"Source fetch failed, using local sample data: {exc}")
                        sources = sample_sources(molecule_name.strip())

                    provider_cfg = monograph_provider if not st.session_state.use_fallback else monograph_provider
                    monograph = synthesis_engine.generate_monograph(
                        molecule_name.strip(),
                        sources,
                        provider_cfg,
                    )
                    monograph["executive_summary"] = executive_summary_generator.generate_executive_summary(
                        molecule_name.strip(),
                        sources,
                        specialty,
                        provider_cfg,
                    )

                    if st.session_state.clean_markdown:
                        for key, value in list(monograph["sections"].items()):
                            monograph["sections"][key] = markdown_cleaner.clean_text(value)

                    is_valid, validation_report = validator.validate_and_score(monograph)
                    monograph["validation"] = validation_report
                    monograph["is_valid_for_delivery"] = is_valid

                    history_id = output_history.log_generation(monograph)
                    monograph["history_id"] = history_id

                    st.session_state.generated_monograph = monograph
                    st.session_state.generated_sources = sources
                    st.success("Monograph generated.")

        monograph = st.session_state.get("generated_monograph")
        if monograph:
            st.subheader(f"Structured sections for {monograph['molecule_name']}")
            st.metric("Validation score", f"{monograph.get('validation', {}).get('overall_compliance_score', 0):.1f}%")
            st.metric("Total tokens", monograph.get("total_tokens_used", 0))

            cols = st.columns(2)
            with cols[0]:
                st.json(monograph.get("validation", {}))
            with cols[1]:
                st.json(monograph.get("quality_scores", {}))

            for section_name, section_content in monograph.get("sections", {}).items():
                with st.expander(section_name.replace("_", " ").title(), expanded=False):
                    st.markdown(section_content)

            if monograph.get("executive_summary"):
                with st.expander("Executive summary", expanded=False):
                    st.markdown(monograph["executive_summary"])

            exports = {}
            try:
                exports = export_service.export_bundle(monograph)
            except Exception as exc:
                st.warning(f"Export bundle failed: {exc}")

            st.subheader("Exports")
            st.write(exports or {"note": "No exports available"})
            st.download_button(
                "Download JSON",
                data=json.dumps(monograph, indent=2, ensure_ascii=False),
                file_name=f"{monograph['molecule_name']}.json",
                mime="application/json",
            )

    with tab_audit:
        st.subheader("Universal audit agents")
        st.caption("These agents work with any compatible provider or with deterministic fallback mode.")

        audit_mode = st.radio("Audit target", ["URL", "HTML"], horizontal=True)
        target_url = st.text_input("Target URL", placeholder="https://example.com")
        target_html = st.text_area("Target HTML", height=220, placeholder="<html>...</html>")
        checklist_url = st.text_input(
            "Checklist URL",
            value="https://istapage.com/blog/landing-page-audit-checklist",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Run A11Y check"):
                if audit_mode == "HTML" and target_html.strip():
                    result = check_accessibility(
                        "inline://content",
                        audit_provider,
                        fetcher=inline_fetcher(target_html, "inline://content"),
                    )
                else:
                    result = check_accessibility(target_url.strip(), audit_provider)
                st.session_state.last_a11y_result = result
                st.success("Accessibility check complete.")
        with col_b:
            if st.button("Build audit schema"):
                schema_result = build_audit_schema(checklist_url.strip(), audit_provider)
                st.session_state.audit_schema = schema_result
                st.session_state.audit_schema_id = schema_result["schema_id"]
                st.success(f"Built schema {schema_result['schema_id']}")
        with col_c:
            if st.button("Build and run audit"):
                schema_result = build_audit_schema(checklist_url.strip(), audit_provider)
                st.session_state.audit_schema = schema_result
                st.session_state.audit_schema_id = schema_result["schema_id"]
                if audit_mode == "HTML" and target_html.strip():
                    audit_result = run_audit(
                        "inline://content",
                        schema_result["schema_id"],
                        audit_provider,
                        fetcher=inline_fetcher(target_html, "inline://content"),
                    )
                else:
                    audit_result = run_audit(
                        target_url.strip(),
                        schema_result["schema_id"],
                        audit_provider,
                    )
                st.session_state.last_audit_result = audit_result
                st.success("Audit complete.")

        if st.session_state.get("last_a11y_result"):
            st.subheader("A11Y result")
            st.json(st.session_state.last_a11y_result)

        if st.session_state.get("audit_schema"):
            st.subheader("Audit schema")
            st.json(st.session_state.audit_schema)

        if st.session_state.get("last_audit_result"):
            st.subheader("Audit run result")
            st.json(st.session_state.last_audit_result)

    with tab_history:
        st.subheader("Generation history")
        try:
            st.json(output_history.get_daily_summary())
        except Exception as exc:
            st.warning(f"History summary unavailable: {exc}")

    with tab_about:
        st.markdown(
            """
            ### Purpose
            Generate product monographs and run universal audit agents from one clean codebase.

            ### Included agents
            - Global A11Y Checker
            - Global Auditor Builder
            - Global Audit Runner

            ### Notes
            - The audit stack is provider-agnostic.
            - Local API-compatible models are supported through the OpenAI-compatible adapter path.
            - External source fetches can fail in restricted network environments; sample data is used as fallback.
            """
        )
        st.code("streamlit run app.py", language="bash")
        st.code("python -m uvicorn src.agents.api.server:app --reload --port 8010", language="bash")


if __name__ == "__main__":
    main()
