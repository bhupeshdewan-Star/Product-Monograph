\# System Inventory



Source files used:

\- repo\_inventory.txt

\- code\_map.txt

\- evidence\_hits.txt

\- provider\_hits.txt

\- export\_hits.txt

\- validation\_hits.txt



\## 1. Active Python Files

Needs verification from repo\_inventory.txt.



\## 2. Entry Point

app.py appears to be the main Streamlit entry point.



\## 3. UI Files

app.py is the primary UI file.



\## 4. Backend Services

\- src/monograph/generator.py

\- src/services/evidence\_retrieval/orchestrator.py

\- src/services/export\_service.py

\- src/monograph/validators.py



\## 5. Evidence Retrieval

\- PubMed

\- FDA

\- EMA

\- ClinicalTrials.gov

\- Local vault



\## 6. Provider Integrations

\- OpenAI

\- Anthropic

\- Google/Gemini

\- DeepSeek

\- Groq

\- OpenRouter

\- OpenAI-compatible local/Ollama



\## 7. Export Services

\- Markdown

\- Print-ready HTML

\- PDF

\- DOCX

\- XLSX

\- Google Docs template



\## 8. Validation Services

\- src/monograph/validators.py

\- src/monograph/sop\_engine.py



\## 9. Data Storage

\- data/evidence\_cache

\- data/generation\_history

\- data/monographs

\- data/skill\_files



\## 10. Dead Code / Duplicate Candidates

Needs verification:

\- ai\_provider\_manager.py

\- free\_ai\_priority\_manager.py

\- free\_model\_fallback.py

\- duplicate root-level and src-level SOP/validator modules

