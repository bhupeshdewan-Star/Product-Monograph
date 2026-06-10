\# Local AI Capability Map



\## Supported Providers



\* OpenAI

\* Anthropic

\* Gemini

\* Groq

\* DeepSeek

\* OpenRouter

\* Local OpenAI-Compatible Provider



\## Local Model Path



UI

↓



Local Model Mode



↓



http://localhost:11434/v1



↓



OpenAICompatibleProvider



↓



provider.generate()



↓



ProductMonographGenerator



\## Evidence Sources



\* PubMed

\* FDA

\* EMA

\* ClinicalTrials.gov

\* Local Vault



\## Evidence Storage



\* data/evidence\_cache

\* session\_state\["evidence\_package"]



\## Validation Path



MonographValidator

↓



SOPEngine

↓



Compliance Score



\## Audit Path



A11Y Checker

↓



Auditor Builder

↓



Auditor Runner



\## Export Path



ExportService



\* Markdown

\* PDF

\* DOCX

\* XLSX

\* Print Ready



\## Hooks



\* provider.generate()

\* export\_bundle()

\* validate\_and\_score()

\* retrieve\_evidence()



\## Extension Points



\* New AI Providers

\* New Evidence Sources

\* New Export Formats

\* New Audit Agents

\* New Validation Rules



\## Missing Capabilities



\### Product Appraisal



\* Dedicated appraisal workflow



\### Visual Aid Builder



\* Slide asset generation



\### Slide Generator



\* PPTX authoring workflow



\### Medical Writer



\* Multi-document drafting



\### Training Manual Builder



\* Curriculum generation



\### Regulatory Review



\* Regulatory rules engine



Status: Needs verification.



