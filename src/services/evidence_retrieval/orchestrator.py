from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from .cache import EvidenceCache, evidence_cache
from .clinicaltrials_client import ClinicalTrialsClient
from .ema_client import EMAClient
from .fda_client import FDAClient
from .normalizer import normalize_evidence_package
from .pubmed_client import PubMedClient
from .schemas import EvidencePackage, EvidenceRetrievalRequest, EvidenceSourceResult


class EvidenceRetrievalOrchestrator:
    def __init__(
        self,
        *,
        cache: EvidenceCache | None = None,
        pubmed_client: PubMedClient | None = None,
        fda_client: FDAClient | None = None,
        ema_client: EMAClient | None = None,
        clinicaltrials_client: ClinicalTrialsClient | None = None,
    ) -> None:
        self.cache = cache or evidence_cache
        self.pubmed_client = pubmed_client or PubMedClient()
        self.fda_client = fda_client or FDAClient()
        self.ema_client = ema_client or EMAClient()
        self.clinicaltrials_client = clinicaltrials_client or ClinicalTrialsClient()

    def retrieve_evidence(
        self,
        molecule: str,
        *,
        max_results: int = 30,
        include_pubmed: bool = True,
        include_fda: bool = True,
        include_ema: bool = True,
        include_clinicaltrials: bool = True,
        force_refresh: bool = False,
    ) -> EvidencePackage:
        request = EvidenceRetrievalRequest(
            molecule=molecule,
            max_results=max_results,
            include_pubmed=include_pubmed,
            include_fda=include_fda,
            include_ema=include_ema,
            include_clinicaltrials=include_clinicaltrials,
            force_refresh=force_refresh,
        )
        cache_key = self.cache.make_key(request.model_dump())
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                package = EvidencePackage.model_validate(cached["package"])
                package.cache_status = {"hit": True, "key": cache_key, "cache_dir": str(self.cache.cache_dir)}
                return package

        source_results: dict[str, EvidenceSourceResult] = {}
        tasks = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            if include_pubmed:
                tasks[executor.submit(self.pubmed_client.fetch, molecule, max_results)] = "pubmed"
            if include_fda:
                tasks[executor.submit(self.fda_client.fetch, molecule, max_results)] = "fda"
            if include_ema:
                tasks[executor.submit(self.ema_client.fetch, molecule, max_results)] = "ema"
            if include_clinicaltrials:
                tasks[executor.submit(self.clinicaltrials_client.fetch, molecule, max_results)] = "clinicaltrials"

            for future in as_completed(tasks):
                source_name = tasks[future]
                try:
                    source_results[source_name] = future.result()
                except Exception as exc:
                    source_results[source_name] = EvidenceSourceResult(
                        source=source_name, status="failed", error=str(exc)
                    )

        for source_name in ("pubmed", "fda", "ema", "clinicaltrials"):
            source_results.setdefault(
                source_name,
                EvidenceSourceResult(source=source_name, status="disabled", error="Source disabled by user."),
            )

        package = normalize_evidence_package(
            molecule,
            source_results,
            cache_status={"hit": False, "key": cache_key, "cache_dir": str(self.cache.cache_dir)},
            retrieved_with=request.model_dump(),
        )
        self.cache.set(cache_key, {"package": package.model_dump()})
        return package

    def clear_cache(self) -> None:
        self.cache.clear()

    def cache_stats(self) -> dict[str, Any]:
        return self.cache.stats()


evidence_orchestrator = EvidenceRetrievalOrchestrator()
