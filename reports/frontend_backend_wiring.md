\# Frontend Backend Wiring



| UI Control                    | Callback             | Backend Function                    |

| ----------------------------- | -------------------- | ----------------------------------- |

| Generate Monograph            | generation\_requested | synthesis\_engine.generate\_monograph |

| Refresh Available Models      | refresh\_models       | model\_discovery                     |

| Warm Up Ollama                | warm\_up\_clicked      | \_warm\_up\_local\_model                |

| Tiny Local Test               | tiny\_test\_clicked    | \_run\_tiny\_local\_test                |

| File Uploader                 | uploaded\_files       | merge\_local\_evidence\_package        |

| Run A11Y Check                | audit\_run\_a11y       | a11y checker                        |

| Build Audit Schema            | audit\_build\_schema   | auditor builder                     |

| Build and Run Audit           | audit\_build\_and\_run  | auditor runner                      |

| Rendered Accessibility Review | audit\_rendered\_a11y  | rendered review                     |

| Download Buttons              | export\_bundle        | ExportService                       |



\## Tabs



\* Generate

\* Audit

\* History

\* About

\* Help



\## Provider Controls



\* Provider Selectbox

\* API Key Input

\* Model Input

\* Base URL Input

\* Temperature Slider



\## Local Model Controls



\* Compact Prompt Mode

\* Fast Local Draft

\* Evidence Cap Slider

\* Warm Up Ollama

\* Tiny Local Test



\## Wiring Issues



Needs verification:



\* Unused legacy provider managers

\* Legacy Claude synthesis engine

\* Duplicate data source managers



