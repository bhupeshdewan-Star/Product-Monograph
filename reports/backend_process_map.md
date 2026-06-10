\# Backend Process Map



\## Generate Monograph Flow



Generate Monograph Button

(app.py:1776)



↓



Evidence Retrieval



\* EvidenceRetrievalOrchestrator

\* PubMed Client

\* FDA Client

\* EMA Client

\* ClinicalTrials Client

\* Local Vault Merge



↓



Evidence Normalization



\* normalize\_evidence\_package()

\* traceability enrichment



↓



Prompt Construction



\* src/monograph/prompts.py

\* SOP prompt injection

\* evidence\_package attached



↓



AI Provider Layer



\* OpenAI

\* Anthropic

\* Gemini

\* Groq

\* DeepSeek

\* OpenRouter

\* Local Ollama (OpenAI-compatible)



↓



Monograph Generation



\* ProductMonographGenerator

\* src/monograph/generator.py



↓



Executive Summary Generation



\* src/monograph/executive\_summary.py



↓



Markdown Cleanup



\* markdown\_cleaner.py



↓



Validation



\* MonographValidator

\* SOP Engine

\* Compliance scoring



↓



History Logging



\* OutputHistoryTracker



↓



Session Storage



\* generated\_monograph

\* generated\_sources

\* evidence\_package



↓



Export Service



\* Markdown

\* Print Ready HTML

\* PDF

\* DOCX

\* XLSX



↓



Output Folder



\* data/monographs



\## Notes



Legacy path detected:



\* claude\_synthesis.py



Status: Needs verification before removal.



