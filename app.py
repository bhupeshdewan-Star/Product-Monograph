"""
Main Streamlit Application: Product Monograph Generator
Web interface for pharmaceutical monograph generation with SOP compliance
"""
import streamlit as st
import os
from datetime import datetime
import json
from data_sources import data_manager
from claude_synthesis import synthesis_engine
from sop_engine import sop_engine
from pdf_generator import pdf_generator
from validator import validator
from markdown_cleaner import markdown_cleaner
from pdf_table_formatter import pdf_table_formatter
from document_generators import word_generator, google_docs_generator
from sop_compliance_validator import SOPComplianceValidator
from output_history_tracker import output_history
from executive_summary_generator import executive_summary_generator
from free_model_fallback import free_model_manager

# Initialize validators and tools
sop_validator = SOPComplianceValidator()

# Get recommended free model
recommended_provider, recommended_model, needs_key, explanation = free_model_manager.recommend_provider()

st.set_page_config(
    page_title="Product Monograph Generator",
    page_icon="[DOCUMENT]",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generation_in_progress' not in st.session_state:
    st.session_state.generation_in_progress = False
if 'generated_monograph' not in st.session_state:
    st.session_state.generated_monograph = None
if 'validation_report' not in st.session_state:
    st.session_state.validation_report = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 0.5em;
    }
    .section-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">[DOCUMENT] Pharmaceutical Product Monograph Generator</div>', unsafe_allow_html=True)
st.markdown("Generate SOP-compliant product monographs automatically using AI and medical databases")

# Sidebar Configuration
with st.sidebar:
    st.header("[SETTINGS] Configuration")

    # Show recommended free model
    st.subheader("AI Model Selection")
    st.success(f"[AUTO] {explanation}")
    st.caption(f"Priority: OpenAI → Gemini → Claude → DeepSeek → Groq")

    # API Key (Optional - only if user wants specific provider)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Optional: Add API Key")
    with col2:
        if st.checkbox("Use custom API?"):
            api_provider = st.radio("Provider:", ["OpenAI", "Google", "Claude", "DeepSeek", "Groq"])

            if api_provider == "OpenAI":
                api_key = st.text_input("OpenAI API Key", type="password", help="From https://platform.openai.com/api-keys")
            elif api_provider == "Google":
                api_key = st.text_input("Google API Key", type="password", help="From https://makersuite.google.com/app/apikey")
            elif api_provider == "Claude":
                api_key = st.text_input("Claude API Key", type="password", help="From https://console.anthropic.com/")
            elif api_provider == "DeepSeek":
                api_key = st.text_input("DeepSeek API Key", type="password", help="From https://platform.deepseek.com/")
            else:  # Groq
                api_key = st.text_input("Groq API Key", type="password", help="From https://console.groq.com/")

            if api_key:
                st.caption(f"[OK] Using {api_provider} API")
        else:
            st.info("[FREE] Using auto-selected free model - no API key needed!")
            api_key = None

    # Demo mode option
    st.divider()
    st.subheader("Demo Mode")
    demo_mode = st.checkbox("Use demo (sample) monograph?", help="Pre-generated sample for testing")

    st.divider()

    # Settings
    st.subheader("Generation Settings")
    include_images = st.checkbox("Include diagrams & charts", value=False, help="Add visual elements to PDF")
    auto_validate = st.checkbox("Auto-validate before delivery", value=True, help="Run compliance checks")
    clean_markdown = st.checkbox("Clean markdown artifacts", value=True, help="Remove ## ** * formatting")

    st.subheader("Output Formats")
    generate_pdf = st.checkbox("Generate PDF", value=True, help="Create PDF output")
    generate_word = st.checkbox("Generate Word (.docx)", value=True, help="Create editable Word document")
    generate_gdocs = st.checkbox("Generate Google Docs template", value=True, help="Create import template")
    generate_json = st.checkbox("Generate JSON", value=True, help="Export as JSON data")

    st.divider()

    # Display token budget
    st.subheader("Token Budget")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Per Monograph", "~27,100", help="Average tokens per generation")
    with col2:
        st.metric("Cost", "$0.15", help="Estimated cost per monograph")

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(["Generate", "View", "Validate", "Learn"])

# Tab 1: Generate Monograph
with tab1:
    st.header("Generate Monograph")

    col1, col2 = st.columns([2, 1])

    with col1:
        molecule_name = st.text_input(
            "Molecule Name",
            placeholder="e.g., Metformin, Aspirin, Ibuprofen",
            help="Enter generic name, brand name, or IUPAC name"
        )

    with col2:
        max_results = st.slider("Max Research Articles", 20, 100, 50)

    if st.button("[LAUNCH] Generate Monograph", type="primary", use_container_width=True):
        if not molecule_name:
            st.error("Please enter a molecule name")
        else:
            st.session_state.generation_in_progress = True

            with st.spinner(f"Generating monograph for {molecule_name}..."):
                try:
                    output_files = {}
                    current_provider = recommended_provider

                    # DEMO MODE: Use pre-generated sample data
                    if demo_mode:
                        st.info("[DEMO] Using pre-generated sample monograph...")

                        # Sample monograph data
                        sources = {
                            "molecule": molecule_name,
                            "sources": {
                                "pubmed": [{"title": f"Sample {molecule_name} Study"}],
                                "fda": [],
                                "google_scholar": [],
                                "open_access": []
                            },
                            "total_articles": 1,
                            "formatted_text": f"Sample research data for {molecule_name}"
                        }

                        monograph = {
                            "molecule_name": molecule_name,
                            "sections": {
                                "introduction": f"## {molecule_name} Introduction\n\n{molecule_name} is a pharmaceutical compound used in clinical practice. This is a sample monograph generated in demo mode.",
                                "pharmacology": f"## Pharmacology\n\n{molecule_name} works through specific molecular mechanisms.",
                                "pharmacokinetics": f"## Pharmacokinetics\n\nAbsorption, distribution, metabolism, and elimination of {molecule_name}.",
                                "clinical_efficacy": f"## Clinical Efficacy\n\nClinical studies demonstrate efficacy of {molecule_name} in target populations.",
                                "safety": f"## Safety & Tolerability\n\nAdverse events and safety profile of {molecule_name}.",
                                "dosage": f"## Dosage & Administration\n\nRecommended dosing of {molecule_name} is molecule-specific.",
                                "contraindications": f"## Contraindications\n\n{molecule_name} should not be used in specific populations.",
                                "drug_interactions": f"## Drug Interactions\n\n{molecule_name} may interact with other medications.",
                                "references": f"[1] Sample reference for {molecule_name}"
                            },
                            "total_tokens_used": 0
                        }
                        st.success("[OK] Sample monograph loaded (5 sample articles)")
                        st.info(f"Demo mode active. Production would use: {explanation}")

                    else:
                        # NORMAL MODE: Fetch real sources and generate
                        st.info(f"[MODEL] Using: {explanation}")

                        # Step 1: Fetch research sources
                        st.info("[LIBRARY] Step 1/6: Fetching research sources...")
                        sources = data_manager.fetch_all_sources(molecule_name, max_results)
                        sources['formatted_text'] = data_manager.structure_for_claude(sources)
                        st.success(f"[OK] Found {sources['total_articles']} articles")

                        # Step 2: Generate monograph
                        st.info("[DOCUMENT] Step 2/6: Generating sections (parallel execution)...")
                        monograph = synthesis_engine.generate_monograph(molecule_name, sources)
                        st.success(f"[OK] Generated {len(monograph['sections'])} sections")

                    # Step 3: Clean markdown artifacts
                    if clean_markdown:
                        st.info("[CLEAN] Step 3/6: Cleaning markdown artifacts...")
                        cleaned_sections = {}
                        for section_name, content in monograph['sections'].items():
                            cleaned_sections[section_name] = markdown_cleaner.clean_text(content)
                        monograph['sections'] = cleaned_sections
                        st.success("[OK] Markdown artifacts removed")
                    else:
                        st.info("[SKIP] Step 3/6: Markdown cleaning skipped")

                    # Step 4: Validate SOP compliance
                    st.info("[CHECK] Step 4/6: Running SOP compliance validation...")
                    if mode == "Demo Mode (No Setup)":
                        # Demo mode: Use sample validation report
                        validation_report = {
                            'score': 85.0,
                            'overall_compliant': True,
                            'issues': ["Sample: This is a demo monograph"],
                            'warnings': ["Demo mode: Limited validation"],
                            'section_checks': {}
                        }
                        st.success("[DEMO] Compliance Score: 85.0% (Demo Data)")
                    else:
                        is_valid, validation_report = sop_validator.validate_sop_compliance(monograph)
                        compliance_score = validation_report.get('score', 0)
                        st.success(f"[OK] Compliance Score: {compliance_score:.1f}%")

                    monograph['validation'] = validation_report
                    st.session_state.validation_report = validation_report
                    compliance_score = validation_report.get('score', 0)

                    # Step 5: Generate output files
                    st.info("[FILES] Step 5/6: Generating output files...")

                    if generate_pdf:
                        pdf_path = pdf_generator.generate_pdf(monograph)
                        output_files['pdf'] = pdf_path
                        st.success(f"[OK] PDF: {os.path.basename(pdf_path)}")

                    if generate_word:
                        word_path = word_generator.generate_word_monograph(monograph)
                        output_files['word'] = word_path
                        st.success(f"[OK] Word: {os.path.basename(word_path)}")

                    if generate_gdocs:
                        gdocs_path = google_docs_generator.create_google_docs_template(monograph)
                        output_files['gdocs'] = gdocs_path
                        st.success(f"[OK] Google Docs: {os.path.basename(gdocs_path)}")

                    if generate_json:
                        json_filename = f"{molecule_name}_monograph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(json_filename, 'w') as f:
                            json.dump(monograph, f, indent=2)
                        output_files['json'] = json_filename
                        st.success(f"[OK] JSON: {json_filename}")

                    # Step 6: Log to history
                    st.info("[HISTORY] Step 6/6: Logging to history...")
                    output_history.log_generation({
                        'molecule': molecule_name,
                        'timestamp': datetime.now().isoformat(),
                        'compliance_score': compliance_score,
                        'output_files': output_files,
                        'total_articles': sources['total_articles']
                    })
                    st.success("[OK] History logged")

                    # Save monograph
                    st.session_state.generated_monograph = monograph
                    st.session_state.output_files = output_files
                    st.session_state.generation_in_progress = False

                    st.success("[DONE] Monograph generation complete!")

                    # Display summary
                    st.markdown("### [STATS] Generation Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Sections", len(monograph['sections']))
                    with col2:
                        st.metric("Tokens Used", monograph.get('total_tokens_used', 'N/A'))
                    with col3:
                        st.metric("Compliance", f"{compliance_score:.1f}%")
                    with col4:
                        st.metric("Files Generated", len(output_files))

                except Exception as e:
                    st.error(f"Error during generation: {str(e)}")
                    st.session_state.generation_in_progress = False

    # Quick Start Examples
    with st.expander("📌 Example Molecules"):
        st.markdown("""
        Try these molecules to test the system:
        - **Metformin** - Common diabetes drug, lots of data
        - **Aspirin** - Well-studied pain reliever
        - **Lisinopril** - ACE inhibitor for hypertension
        - **Omeprazole** - Proton pump inhibitor
        - **Atorvastatin** - Cholesterol medication
        """)

# Tab 2: View Generated Monograph
with tab2:
    st.header("View Generated Monograph")

    if st.session_state.generated_monograph:
        monograph = st.session_state.generated_monograph

        st.markdown(f"### {monograph['molecule_name']} Monograph")

        # Display sections
        for section_name, section_content in monograph['sections'].items():
            with st.expander(f"[PAGE] {section_name.replace('_', ' ').title()}"):
                st.markdown(section_content)

        # Download options
        st.divider()
        st.markdown("### Download Generated Files")

        output_files = st.session_state.get('output_files', {})

        col1, col2, col3, col4 = st.columns(4)

        # PDF Download
        with col1:
            if 'pdf' in output_files and os.path.exists(output_files['pdf']):
                with open(output_files['pdf'], 'rb') as f:
                    st.download_button(
                        label="[FILE] PDF",
                        data=f.read(),
                        file_name=os.path.basename(output_files['pdf']),
                        mime="application/pdf"
                    )
            else:
                st.button("[FILE] PDF", disabled=True)

        # Word Download
        with col2:
            if 'word' in output_files and os.path.exists(output_files['word']):
                with open(output_files['word'], 'rb') as f:
                    st.download_button(
                        label="[FILE] Word",
                        data=f.read(),
                        file_name=os.path.basename(output_files['word']),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            else:
                st.button("[FILE] Word", disabled=True)

        # Google Docs Download
        with col3:
            if 'gdocs' in output_files and os.path.exists(output_files['gdocs']):
                with open(output_files['gdocs'], 'r') as f:
                    st.download_button(
                        label="[FILE] Google Docs",
                        data=f.read(),
                        file_name=os.path.basename(output_files['gdocs']),
                        mime="text/plain"
                    )
            else:
                st.button("[FILE] Google Docs", disabled=True)

        # JSON Download
        with col4:
            if 'json' in output_files and os.path.exists(output_files['json']):
                with open(output_files['json'], 'r') as f:
                    st.download_button(
                        label="[FILE] JSON",
                        data=f.read(),
                        file_name=os.path.basename(output_files['json']),
                        mime="application/json"
                    )
            else:
                st.button("[FILE] JSON", disabled=True)

    else:
        st.info("No monograph generated yet. Use the 'Generate' tab to create one.")

# Tab 3: Validation Report
with tab3:
    st.header("Validation Report")

    if st.session_state.validation_report:
        report = st.session_state.validation_report

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall Compliance", f"{report.get('score', 0):.1f}%")
        with col2:
            st.metric("Compliant", "Yes" if report.get('overall_compliant', False) else "No")
        with col3:
            st.metric("Issues", len(report.get('issues', [])))
        with col4:
            st.metric("Warnings", len(report.get('warnings', [])))

        st.divider()

        # Detailed scoring
        if 'detailed_scoring' in report:
            st.subheader("Detailed Scoring")
            scoring = report['detailed_scoring']

            # Create metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Structure", f"{scoring['structure_compliance']:.1f}%")
            with col2:
                st.metric("Content", f"{scoring['content_quality']:.1f}%")
            with col3:
                st.metric("Evidence", f"{scoring['evidence_quality']:.1f}%")
            with col4:
                st.metric("Formatting", f"{scoring['formatting_compliance']:.1f}%")

        # Section details
        st.subheader("Section Compliance")
        for section, details in report.get('section_details', {}).items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{section.replace('_', ' ').title()}**")
            with col2:
                st.write(f"Score: {details['compliance_score']:.1f}%")
            with col3:
                st.write(f"Status: {details['status']}")

        # Recommendations
        if 'recommendation' in report:
            st.divider()
            st.subheader("Recommendations")
            rec = report['recommendation']
            st.info(f"**Status:** {rec['status']}")

            if rec['priority_fixes']:
                st.warning("Priority Fixes Required:")
                for fix in rec['priority_fixes']:
                    st.write(f"• {fix}")

            if rec.get('positive_notes'):
                st.success("Positive Notes:")
                for note in rec['positive_notes']:
                    st.write(f"• {note}")

    else:
        st.info("No validation report available. Generate a monograph to see validation results.")

# Tab 4: Learn More
with tab4:
    st.header("About This Tool")

    st.markdown("""
    ### What is a Product Monograph?
    A product monograph is a comprehensive, evidence-based reference document about a pharmaceutical product.
    It includes pharmacology, pharmacokinetics, clinical efficacy, safety data, dosing, and references.

    ### SOP Compliance
    This tool generates monographs following your Standard Operating Procedures (SOPs) including:
    - [OK] Mandatory sections (Pharmacology, PK, Efficacy, Safety, Dosing)
    - [OK] Evidence quality standards
    - [OK] CIOMS adverse event classification
    - [OK] Regulatory compliance requirements

    ### Data Sources
    The tool automatically searches:
    - **PubMed**: 30 million+ medical articles
    - **FDA**: Official drug approvals and labels
    - **Google Scholar**: Academic research
    - **Open Access**: Free full-text articles

    ### Token Usage & Cost
    - Average cost per monograph: **$0.15 USD**
    - Annual budget for 100 monographs: **~$15 USD**
    - Development tokens used: ~77,000

    ### Quality Assurance
    - Auto-validation against SOP requirements
    - Evidence quality checking
    - Compliance scoring (0-100%)
    - Detailed recommendations for improvement

    ### Next Steps
    1. Generate your first monograph (try "Metformin")
    2. Review the validation report
    3. Download the PDF for expert review
    4. Provide feedback to improve future generations
    """)

    st.divider()

    st.markdown("### 📞 Support")
    st.markdown("""
    For issues or questions:
    - Check the README.md file
    - Review the validation report for specific issues
    - Contact: your-email@example.com
    """)

# Footer
st.divider()
st.markdown("""
<small>
[LAUNCH] **Product Monograph Generator** | Built with Streamlit & Claude API
[WARN]️ **DISCLAIMER**: This tool generates DRAFT documents. All monographs require expert medical review before distribution.
Generated: {date}
</small>
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M UTC")), unsafe_allow_html=True)
