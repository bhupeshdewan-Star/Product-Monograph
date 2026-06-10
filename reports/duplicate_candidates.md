\# Duplicate / Dead Code Candidate Report



\## Confirmed Active Path



The active UI imports the monograph engine from:



\- `src.monograph.generator import synthesis\_engine`



The active Generate Monograph button calls:



\- `synthesis\_engine.generate\_monograph(...)`



Therefore, the active monograph engine appears to be:



\- `src/monograph/generator.py`

\- `ProductMonographGenerator`

\- `synthesis\_engine = ProductMonographGenerator()`



\## Likely Legacy / Duplicate Candidates



\### 1. `claude\_synthesis.py`



Contains:



\- `class ClaudeSynthesisEngine`

\- `synthesis\_engine = ClaudeSynthesisEngine()`



Likely duplicate because the active UI imports `synthesis\_engine` from `src.monograph.generator`, not from `claude\_synthesis.py`.



Status: needs verification before deletion.



\### 2. `ai\_provider\_manager.py`



Contains:



\- `class AIProviderManager`

\- `ai\_provider = AIProviderManager()`



Potential duplicate because current provider flow appears to use:



\- `src/agents/providers/\*`

\- `src/agents/providers/provider\_factory.py`

\- `src/monograph/generation\_config.py`



Status: needs verification because `global\_audit\_api.py` references `AIProviderManager`.



\### 3. `free\_ai\_priority\_manager.py`



Contains:



\- `class FreeAIPriorityManager`

\- `free\_ai\_manager = FreeAIPriorityManager()`



Potential duplicate provider-routing logic.



Status: needs verification.



\### 4. `free\_model\_fallback.py`



Contains:



\- `class FreeModelFallback`

\- `free\_model\_manager = FreeModelFallback()`



Potential duplicate fallback-provider routing logic.



Status: needs verification.



\### 5. `data\_sources.py`



Contains:



\- `class DataSourceManager`

\- `data\_manager = DataSourceManager()`



Potential duplicate because active evidence retrieval appears to use:



\- `src/services/evidence\_retrieval/orchestrator.py`

\- `src/services/evidence\_retrieval/pubmed\_client.py`

\- `src/services/evidence\_retrieval/fda\_client.py`

\- `src/services/evidence\_retrieval/ema\_client.py`

\- `src/services/evidence\_retrieval/clinicaltrials\_client.py`



Status: needs verification.



\### 6. `data\_sources\_enhanced.py`



Contains:



\- `class EnhancedDataSourceManager`

\- `data\_manager\_enhanced = EnhancedDataSourceManager()`



Potential duplicate or legacy enhanced scraper.



Status: needs verification.



\### 7. `src/services/data\_sources.py`



Contains:



\- `class DataSourceManager`

\- `data\_manager = DataSourceManager()`



Potential duplicate of root-level `data\_sources.py`.



Status: needs verification.



\## Recommendation



Do not delete any file yet.



First confirm import usage with:



```cmd

findstr /s /i /n "claude\_synthesis AIProviderManager free\_ai\_manager free\_model\_manager data\_manager data\_manager\_enhanced" \*.py

